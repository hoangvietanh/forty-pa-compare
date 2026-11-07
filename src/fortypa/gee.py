"""Earth Engine side: ForTy V2 Beta class maps, protected areas from WDPA, class areas per year, map thumbnails."""
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import ee
import numpy as np
import pandas as pd
import requests
from PIL import Image

FORTY = "projects/nature-trace/assets/forest_typology/v2_beta"
WDPA = "WCMC/WDPA/current/polygons"

# Class value = argmax band index + 1 (B0 -> 1 … B6 -> 7). Rows run from natural to planted classes, the order used in
# legends and tables. Colors from ColorBrewer by origin: natural forest in Greens, planted in Blues, tree crops in
# Oranges, other land light gray.
CLASSES = pd.DataFrame([
    (1, "B0", "Rừng nguyên sinh – trưởng thành", "Primary forest: mature", "#006D2C"),
    (7, "B6", "Rừng nguyên sinh – đang phục hồi", "Primary forest: regrowing", "#31A354"),
    (2, "B1", "Rừng tái sinh tự nhiên", "Naturally regenerating forest", "#A1D99B"),
    (3, "B2", "Rừng trồng (luân kỳ > 40 năm)", "Planted forest", "#08519C"),
    (4, "B3", "Rừng trồng thâm canh (luân kỳ ≤ 40 năm)", "Plantation forest", "#6BAED6"),
    (5, "B4", "Cây công nghiệp và nông lâm kết hợp", "Tree crops and agroforestry", "#FD8D3C"),
    (6, "B5", "Đất khác (không phải rừng)", "Other land (non-forest)", "#E5E5E5"),
], columns=["value", "band", "label", "label_en", "color"])
FOREST = CLASSES[CLASSES.value != 6].reset_index(drop=True)
NATURAL = (1, 7, 2)  # mature primary, regrowing primary, naturally regenerating
PLANTED = (3, 4, 5)  # planted, plantation, tree crops and agroforestry

# Class change between two years, grouped by what changed (N natural, P planted / tree crops, O other land). Four
# colors only: with six, some pair always failed the dataviz validator over all pairs (they all meet on a map). This
# order passes it over all pairs (CVD 7.5 for 3↔2, so the legend carries labels and areas as secondary encoding).
# The per-transition areas (from class -> to class) stay available in the transitions table.
CHANGES = pd.DataFrame([
    (0, "Không đổi lớp", "#E4E4DF"),
    (1, "Đổi lớp trong cùng nhóm (tự nhiên ↔ tự nhiên, trồng ↔ trồng)", "#D9A400"),
    (2, "Tăng rừng / phục hồi (đất khác → rừng, rừng trồng → tự nhiên)", "#1E6FD9"),
    (3, "Rừng / cây → đất khác", "#B83FB0"),
    (4, "Rừng tự nhiên → rừng trồng / cây công nghiệp", "#D62828"),
], columns=["code", "label", "color"])


def _group(c):
    return "N" if c in NATURAL else "P" if c in PLANTED else "O"


def change_code(c0, c1):
    """Change category (CHANGES.code) for one class transition c0 -> c1 (class values 1–7)."""
    if c0 == c1:
        return 0
    return {("N", "N"): 1, ("P", "P"): 1, ("O", "N"): 2, ("O", "P"): 2, ("P", "N"): 2,
            ("N", "O"): 3, ("P", "O"): 3, ("N", "P"): 4}[(_group(c0), _group(c1))]

PA_COLS = ["SITE_ID", "NAME", "NAME_ENG", "DESIG_ENG", "DESIG_TYPE", "IUCN_CAT", "REALM", "STATUS", "STATUS_YR",
           "GIS_AREA", "GIS_M_AREA", "LAND_KM2", "LON", "LAT"]


def init(project):
    try:
        ee.Initialize(project=project)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project)


def class_image(year, region=None):
    """ForTy V2 Beta class map (1–7) for one year as a single byte band named y<year>; nodata stays masked."""
    ic = ee.ImageCollection(f"{FORTY}/{year}")
    if region is not None:
        ic = ic.filterBounds(region)
    raw = ic.mosaic()
    # probabilities are 0–250; 255 marks nodata, and an all-zero pixel has no prediction
    raw = raw.updateMask(raw.select(0).lte(250).And(raw.reduce(ee.Reducer.sum()).gt(0)))
    return raw.toArray().arrayArgmax().arrayGet([0]).add(1).toByte().rename(f"y{year}")


def dfci_image(y0, y1, region=None):
    """Per-pixel ΔFCI from y0 to y1 as band d = 100 × (weight of the y1 class − weight of the y0 class), from −100
    (mature primary forest → other land) to +100, and band f = 1 where the class changed; masked where either year has
    no data. Averaged over an area, d is that area's ΔFCI."""
    from .index import WEIGHTS
    vals = list(WEIGHTS)

    def w(c):
        return c.remap(vals, [100 * WEIGHTS[v] for v in vals]).toFloat()

    c0, c1 = class_image(y0, region), class_image(y1, region)
    return (w(c1).subtract(w(c0)).rename("d").addBands(c0.neq(c1).toFloat().rename("f"))
            .updateMask(c0.mask().And(c1.mask())))


def select_pas(iso3="VNM", desig_eng=None, status=("Designated", "Inscribed"), desig_types=None,
               exclude_realm=("Marine",), min_land_km2=1.0, pick=None):
    """Protected areas of one country. Returns (ee.FeatureCollection with one feature per SITE_ID, DataFrame of
    attributes sorted by land area, largest first).

    WDPA stores some sites as several parcels (same SITE_ID, SITE_PID <id>_1, <id>_2 …): their areas are summed and
    their polygons dissolved, so each site is counted once. LAND_KM2 = GIS_AREA − GIS_M_AREA (the non-marine part);
    RANK is the site's rank by LAND_KM2 among all eligible sites of the country (1 = largest). pick(df) -> subset
    chooses the sites to keep from that full ranked list (e.g. compare.select_top). LON/LAT is the centroid, used to
    pick the UTM zone.
    """
    base = (ee.FeatureCollection(WDPA).filter(ee.Filter.eq("ISO3", iso3))
            .filter(ee.Filter.inList("STATUS", list(status))))
    if desig_eng:
        base = base.filter(ee.Filter.inList("DESIG_ENG", list(desig_eng)))
    if desig_types:
        base = base.filter(ee.Filter.inList("DESIG_TYPE", list(desig_types)))
    if exclude_realm:
        base = base.filter(ee.Filter.inList("REALM", list(exclude_realm)).Not())

    cols = PA_COLS[:-3]
    rows = base.reduceColumns(ee.Reducer.toList(len(cols)), cols).get("list").getInfo()
    parcels = pd.DataFrame(rows, columns=cols)
    parcels["SITE_ID"] = parcels.SITE_ID.astype(int)
    df = parcels.groupby("SITE_ID", as_index=False).agg(
        {**{c: "first" for c in cols if c not in ("SITE_ID", "GIS_AREA", "GIS_M_AREA")},
         "GIS_AREA": "sum", "GIS_M_AREA": "sum"})
    df["PARCELS"] = df.SITE_ID.map(parcels.SITE_ID.value_counts())
    df["LAND_KM2"] = df.GIS_AREA - df.GIS_M_AREA
    df = df[df.LAND_KM2 >= min_land_km2].sort_values("LAND_KM2", ascending=False).reset_index(drop=True)
    df.insert(0, "ISO3", iso3)
    df.insert(1, "RANK", range(1, len(df) + 1))
    if pick is not None:
        df = pick(df)

    single = df[df.PARCELS == 1].SITE_ID.tolist()
    fc = base.filter(ee.Filter.inList("SITE_ID", single)).select(["SITE_ID"])
    multi = [ee.Feature(base.filter(ee.Filter.eq("SITE_ID", s)).union(10).first()).set("SITE_ID", s)
             for s in df[df.PARCELS > 1].SITE_ID]
    if multi:
        fc = fc.merge(ee.FeatureCollection(multi))

    def _centroid(f):
        c = f.geometry().centroid(100).coordinates()
        return ee.Feature(None, {"SITE_ID": f.get("SITE_ID"), "LON": c.get(0), "LAT": c.get(1)})

    cent = fc.map(_centroid).reduceColumns(ee.Reducer.toList(3), ["SITE_ID", "LON", "LAT"]).get("list").getInfo()
    cent = pd.DataFrame(cent, columns=["SITE_ID", "LON", "LAT"]).astype({"SITE_ID": int})
    df = df.merge(cent, on="SITE_ID").sort_values("RANK").reset_index(drop=True)
    return fc, df


def pa_feature(fc, site_id):
    return ee.Feature(fc.filter(ee.Filter.eq("SITE_ID", int(site_id))).first())


def utm_epsg(lon, lat):
    return (32600 if lat >= 0 else 32700) + int((lon + 180) // 6) + 1


def _scales_for(pa, scales, max_pixels):
    """The scales whose pixel count over the PA stays within max_pixels (the coarsest one if none does): on a park of
    tens of thousands of km² a 10 m request runs for half an hour before Earth Engine gives up."""
    if not max_pixels:
        return scales
    ok = [s for s in scales if pa.GIS_AREA * 1e6 / s ** 2 <= max_pixels]
    return ok or scales[-1:]


def _pa_areas(fc, pa, years, scales, tile_scale, max_pixels=None):
    """Class areas (ha) of one PA for every year in one request, in the PA's UTM zone so a pixel is scale² m².

    frequencyHistogram counts edge pixels by the fraction inside the polygon. Coarser scales are tried only when the
    finer one fails (timeout or memory on very large PAs); the scale used is kept with the result.
    """
    geom = pa_feature(fc, pa.SITE_ID).geometry()
    img = ee.Image.cat([class_image(y, geom) for y in years])
    crs = f"EPSG:{utm_epsg(pa.LON, pa.LAT)}"
    errors = []
    for scale in _scales_for(pa, scales, max_pixels):
        try:
            h = img.reduceRegion(ee.Reducer.frequencyHistogram(), geom, scale=scale, crs=crs,
                                 maxPixels=1e13, tileScale=tile_scale).getInfo()
            rows = [{"SITE_ID": int(pa.SITE_ID), "year": y, "value": int(k), "area_ha": n * scale ** 2 / 1e4,
                     "scale_m": scale} for y in years for k, n in (h.get(f"y{y}") or {}).items()]
            return rows, errors
        except Exception as e:
            errors.append(f"scale {scale} m: {type(e).__name__}: {str(e)[:160]}")
    return None, errors


def _pa_transitions(fc, pa, years, scales, tile_scale, max_pixels=None):
    """Area (ha) of every class transition first year -> last year in one PA, at 10 m in the PA's UTM zone."""
    geom = pa_feature(fc, pa.SITE_ID).geometry()
    y0, y1 = years[0], years[-1]
    pair = class_image(y0, geom).multiply(10).add(class_image(y1, geom)).rename("t")  # 17 = class 1 -> class 7
    crs = f"EPSG:{utm_epsg(pa.LON, pa.LAT)}"
    errors = []
    for scale in _scales_for(pa, scales, max_pixels):
        try:
            h = pair.reduceRegion(ee.Reducer.frequencyHistogram(), geom, scale=scale, crs=crs,
                                  maxPixels=1e13, tileScale=tile_scale).getInfo()
            return [{"SITE_ID": int(pa.SITE_ID), "from": int(k) // 10, "to": int(k) % 10,
                     "area_ha": n * scale ** 2 / 1e4, "scale_m": scale} for k, n in (h.get("t") or {}).items()], errors
        except Exception as e:
            errors.append(f"scale {scale} m: {type(e).__name__}: {str(e)[:160]}")
    return None, errors


def _per_pa(fn, fc, pas, cache_dir, key, what, workers, log, *args):
    """Runs fn(fc, pa, *args) -> (rows, errors) for every PA not yet cached as <cache_dir>/<SITE_ID>_<key>.json.

    Returns (all rows, {SITE_ID: errors} for the PAs that failed at every scale).
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    out, todo, failed = [], [], {}
    for pa in pas.itertuples():
        f = cache_dir / f"{pa.SITE_ID}_{key}.json"
        if f.exists():
            out += json.loads(f.read_text(encoding="utf-8"))
        else:
            todo.append(pa)
    log(f"{what}: {len(pas) - len(todo)} PA lấy từ cache, {len(todo)} PA cần tính trên GEE")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, fc, pa, *args): pa for pa in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            pa = futs[fut]
            rows, errors = fut.result()
            if rows is None:
                failed[pa.SITE_ID] = errors
                log(f"  [{i}/{len(todo)}] LỖI {pa.SITE_ID} {pa.NAME_ENG}: {errors[-1]}")
                continue
            (cache_dir / f"{pa.SITE_ID}_{key}.json").write_text(json.dumps(rows), encoding="utf-8")
            out += rows
            note = f" (dùng {rows[0]['scale_m']} m)" if errors else ""
            log(f"  [{i}/{len(todo)}] {pa.SITE_ID} {pa.NAME_ENG}{note} – {time.time() - t0:.0f}s")
    return out, failed


def compute_areas(fc, pas, years, cache_dir, scales=(10, 20, 30), tile_scale=4, workers=6, max_pixels=None,
                  log=print):
    """Long table SITE_ID | year | value | area_ha | scale_m for all PAs, cached as one JSON per PA."""
    out, failed = _per_pa(_pa_areas, fc, pas, cache_dir, f"{min(years)}-{max(years)}", "Diện tích", workers, log,
                          years, scales, tile_scale, max_pixels)
    df = pd.DataFrame(out, columns=["SITE_ID", "year", "value", "area_ha", "scale_m"])
    return df.merge(CLASSES[["value", "label", "label_en"]], on="value", how="left"), failed


def compute_transitions(fc, pas, years, cache_dir, scales=(10, 20, 30), tile_scale=4, workers=6, max_pixels=None,
                        log=print):
    """Long table SITE_ID | from | to | area_ha | scale_m | change (CHANGES.code), first year -> last year."""
    out, failed = _per_pa(_pa_transitions, fc, pas, cache_dir, f"{years[0]}to{years[-1]}", "Chuyển đổi lớp",
                          workers, log, years, scales, tile_scale, max_pixels)
    df = pd.DataFrame(out, columns=["SITE_ID", "from", "to", "area_ha", "scale_m"])
    df["change"] = [change_code(a, b) for a, b in zip(df["from"], df["to"])]
    return df, failed


def overlaps(fc, pas):
    """Pairs of selected PAs whose polygons intersect: area of the intersection and its share of each PA."""
    def per_a(a):
        others = fc.filterBounds(a.geometry()).filter(ee.Filter.neq("SITE_ID", a.get("SITE_ID")))
        return others.map(lambda b: ee.Feature(None, {
            "a": a.get("SITE_ID"), "b": b.get("SITE_ID"),
            "km2": a.geometry().intersection(b.geometry(), ee.ErrorMargin(50)).area(50).divide(1e6)}))

    rows = fc.map(per_a).flatten().reduceColumns(ee.Reducer.toList(3), ["a", "b", "km2"]).get("list").getInfo()
    df = pd.DataFrame(rows, columns=["a", "b", "km2"]).astype({"a": int, "b": int})
    df = df[(df.a < df.b) & (df.km2 > 0.01)]
    info = pas.set_index("SITE_ID")
    df["name_a"], df["name_b"] = info.NAME.reindex(df.a).values, info.NAME.reindex(df.b).values
    df["desig_a"], df["desig_b"] = info.DESIG_ENG.reindex(df.a).values, info.DESIG_ENG.reindex(df.b).values
    # GIS_AREA is WDPA's own figure and can be slightly below the geometry's area, hence the clip at 100 %
    df["pct_of_a"] = (100 * df.km2 / info.GIS_AREA.reindex(df.a).values).clip(upper=100)
    df["pct_of_b"] = (100 * df.km2 / info.GIS_AREA.reindex(df.b).values).clip(upper=100)
    return df.sort_values("km2", ascending=False).reset_index(drop=True)


def _region(pa, geom):
    pad = max(300, (pa.GIS_AREA ** 0.5) * 1000 * 0.04)  # ~4 % of the PA's width around it
    return geom.bounds(100).buffer(pad, 100).bounds(100)


def _thumb(fc, pa, layer, dims):
    """Thumbnail URL of a visualized layer(geom) clipped to the PA, on white, with the PA outline."""
    f = pa_feature(fc, pa.SITE_ID)
    geom = f.geometry()
    bg = ee.Image(1).visualize(palette=["FFFFFF"])
    outline = ee.FeatureCollection([f]).style(color="333333", fillColor="00000000", width=1)
    img = ee.ImageCollection([bg, layer(geom).clip(geom), outline]).mosaic()
    return img.getThumbURL({"region": _region(pa, geom), "dimensions": dims, "crs": "EPSG:3857", "format": "png"})


def _class_layer(year):
    palette = [CLASSES.set_index("value").color[v].lstrip("#") for v in range(1, 8)]
    return lambda geom: class_image(year, geom).visualize(min=1, max=7, palette=palette)


OUTSIDE, OUTLINE = -999.0, -998.0  # values in the ΔFCI map array besides real ΔFCI (−100 … 100)

# Per-pixel ΔFCI classes (points): ColorBrewer RdYlBu 11, red = loss, blue = gain. Map pixels where no pixel changed
# class are drawn in UNCHANGED gray instead of the middle class, so stable land does not look yellow.
DFCI_PIXEL_BINS = pd.DataFrame([
    (-1e9, -50, "#A50026", "≤ −50"), (-50, -25, "#D73027", "−50 đến −25"), (-25, -10, "#F46D43", "−25 đến −10"),
    (-10, -5, "#FDAE61", "−10 đến −5"), (-5, -1, "#FEE090", "−5 đến −1"), (-1, 1, "#FFFFBF", "−1 đến +1"),
    (1, 5, "#E0F3F8", "+1 đến +5"), (5, 10, "#ABD9E9", "+5 đến +10"), (10, 25, "#74ADD1", "+10 đến +25"),
    (25, 50, "#4575B4", "+25 đến +50"), (50, 1e9, "#313695", "≥ +50"),
], columns=["lo", "hi", "color", "label"])
UNCHANGED = "#E5E5E5"


def _dfci_bands(geom, f, y0, y1, utm, scale, pixel_m):
    """Per-pixel ΔFCI at `scale` m averaged into map pixels of pixel_m, as two bands:
    d = mean ΔFCI under the map pixel, OUTSIDE or OUTLINE; f = share of pixels under it that changed class, 0–250.
    Averaging goes in 4×4 steps (10 → 40 → 160 m …): one step from 10 m to a 200 m map pixel exceeds Earth Engine's
    memory limit on large PAs."""
    img = dfci_image(y0, y1, geom).reproject(utm.atScale(scale))
    s = scale

    def shrink(i):
        return i.reduceResolution(ee.Reducer.mean(), maxPixels=64)

    while s * 4 <= pixel_m:
        s *= 4
        img = shrink(img).reproject(utm.atScale(s))
    if s < pixel_m:  # last, partial step into the requested grid
        img = shrink(img)
    outline = ee.Image(0).paint(ee.FeatureCollection([f]), 1, 1).eq(1)
    d = img.select("d").unmask(0).clip(geom).unmask(OUTSIDE, False).where(outline, OUTLINE).toFloat().rename("d")
    frac = img.select("f").multiply(250).round().unmask(0, False).toByte().rename("f")
    return d.addBands(frac)


def dfci_array(fc, pa, years, dims=900, scale=10, tile_km2=250, workers=8):
    """Per-pixel ΔFCI map first -> last year of one PA in EPSG:3857 as two arrays (see _dfci_bands): mean ΔFCI
    (float32, with OUTSIDE / OUTLINE) and share of changed pixels (uint8, 0–250).

    A single request for a large PA at 10 m exceeds Earth Engine's memory limit, so the map is fetched with
    ee.data.computePixels in tiles of about tile_km2 on a fixed grid and stitched here.
    """
    f = pa_feature(fc, pa.SITE_ID)
    geom = f.geometry()
    ring = _region(pa, geom).coordinates().getInfo()[0]
    lon0, lat0 = map(min, zip(*ring))
    lon1, lat1 = map(max, zip(*ring))
    R = 6378137.0

    def merc(lon, lat):
        return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    (x0, y0), (x1, y1) = merc(lon0, lat0), merc(lon1, lat1)
    px = max(x1 - x0, y1 - y0) / dims  # mercator metres per map pixel
    ground = px * math.cos(math.radians((lat0 + lat1) / 2))
    W, H = math.ceil((x1 - x0) / px), math.ceil((y1 - y0) / px)
    img = _dfci_bands(geom, f, years[0], years[-1], ee.Projection(f"EPSG:{utm_epsg(pa.LON, pa.LAT)}"),
                      scale, ground)
    t = max(16, int(math.sqrt(tile_km2) * 1000 / ground))  # tile side in map pixels
    out = np.full((H, W), OUTSIDE, dtype=np.float32)
    share = np.zeros((H, W), dtype=np.uint8)

    def _tile(i, j):
        w, h = min(t, W - j), min(t, H - i)
        req = {"expression": img, "fileFormat": "NUMPY_NDARRAY",
               "grid": {"dimensions": {"width": w, "height": h}, "crsCode": "EPSG:3857",
                        "affineTransform": {"scaleX": px, "shearX": 0, "translateX": x0 + j * px,
                                            "shearY": 0, "scaleY": -px, "translateY": y1 - i * px}}}
        for attempt in range(3):
            try:
                a = ee.data.computePixels(req)
                out[i:i + h, j:j + w], share[i:i + h, j:j + w] = a["d"], a["f"]
                return
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(3 * (attempt + 1))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda ij: _tile(*ij), [(i, j) for i in range(0, H, t) for j in range(0, W, t)]))
    return out, share


def _rgb(hex_color):
    return np.array([int(hex_color[k:k + 2], 16) for k in (1, 3, 5)], dtype=np.uint8)


def render_dfci(d, share):
    """RGB array: outside white, PA outline dark gray, map pixels where nothing changed light gray, the rest in their
    DFCI_PIXEL_BINS color."""
    out = np.full(d.shape + (3,), 255, dtype=np.uint8)
    inside = d > OUTLINE
    for b in DFCI_PIXEL_BINS.itertuples():
        out[inside & (d >= b.lo) & (d < b.hi)] = _rgb(b.color)
    out[inside & (share == 0)] = _rgb(UNCHANGED)
    out[d == OUTLINE] = (0x33, 0x33, 0x33)
    return out


def _download(jobs, log, what, workers=6, retries=3):
    """jobs: [(key, path, url_fn)]; fetches each missing PNG (url_fn() builds the URL). Returns {key: Path}."""
    def _get(path, url_fn):
        if path.exists():
            return path, None
        err = None
        for attempt in range(retries):
            try:
                r = requests.get(url_fn(), timeout=300)
                if not r.ok:  # Earth Engine puts the reason (e.g. "User memory limit exceeded.") in the body
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
                path.write_bytes(r.content)
                return path, None
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:200]}"
                time.sleep(3 * (attempt + 1))
        return None, err

    done = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_get, path, fn): key for key, path, fn in jobs}
        for fut in as_completed(futs):
            path, err = fut.result()
            if path:
                done[futs[fut]] = path
            else:
                log(f"  LỖI {what} {futs[fut]}: {err}")
    log(f"{what}: {len(done)}/{len(jobs)}")
    return done


def download_thumbs(fc, pas, years, out_dir, dims=900, workers=6, retries=3, log=print):
    """PNG of the class map for each PA and year (non-forest in light gray, PA outline in dark gray); cached on disk.

    Returns {(SITE_ID, year): Path} for the images that exist.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [((pa.SITE_ID, y), out_dir / f"{pa.SITE_ID}_{y}.png",
             lambda pa=pa, y=y: _thumb(fc, pa, _class_layer(y), dims)) for pa in pas.itertuples() for y in years]
    return _download(jobs, log, "Ảnh bản đồ", workers, retries)


def overview_thumb(fc, colors, out_path, dims=1100, pad=0.06):
    """Map of a set of PAs on a light country background, each PA filled with colors[SITE_ID] (hex) and outlined.

    Returns the extent of the PNG as (x0, y0, x1, y1) in EPSG:3857 metres, to place labels on it."""
    out_path = Path(out_path)
    ring = fc.geometry(1000).bounds(1000).coordinates().getInfo()[0]
    lon0, lat0 = map(min, zip(*ring))
    lon1, lat1 = map(max, zip(*ring))
    dx, dy = (lon1 - lon0) * pad, (lat1 - lat0) * pad
    lon0, lon1, lat0, lat1 = lon0 - dx, lon1 + dx, max(lat0 - dy, -80), min(lat1 + dy, 80)
    region = ee.Geometry.Rectangle([lon0, lat0, lon1, lat1], None, False)
    land = (ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filterBounds(region)
            .style(color="BDBDB8", fillColor="EDEDEA", width=0.6))
    styles = ee.Dictionary({str(int(k)): {"color": "333333", "width": 1, "fillColor": v.lstrip("#")}
                            for k, v in colors.items()})
    pas = fc.map(lambda f: f.set("style", styles.get(ee.Number(f.get("SITE_ID")).format("%d")))) \
            .style(styleProperty="style")
    img = ee.ImageCollection([ee.Image(1).visualize(palette=["FFFFFF"]), land, pas]).mosaic()
    # not cached: the colors follow ΔFCI, which changes whenever the areas are recomputed
    r = requests.get(img.getThumbURL({"region": region, "dimensions": dims, "crs": "EPSG:3857", "format": "png"}),
                     timeout=300)
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    out_path.write_bytes(r.content)
    R = 6378137.0

    def merc(lon, lat):
        return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    (x0, y0), (x1, y1) = merc(lon0, lat0), merc(lon1, lat1)
    return x0, y0, x1, y1


def download_change_maps(fc, pas, years, out_dir, dims=900, scale=10, big_km2=None, big_scale=30, log=print):
    """Per-pixel ΔFCI map first -> last year for each PA (see dfci_array). The arrays are cached as .npz and the PNG is
    drawn from them, so changing the colors only needs a redraw, not new Earth Engine requests.

    PAs larger than big_km2 are mapped from big_scale m pixels instead of `scale` (tiles grow accordingly): at 10 m a
    30,000 km² park needs hundreds of tile requests. Returns {SITE_ID: Path of the PNG}.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    done, t0 = {}, time.time()
    todo = [pa for pa in pas.itertuples()]
    for i, pa in enumerate(todo, 1):
        stem = out_dir / f"{pa.SITE_ID}_dfci_{years[0]}_{years[-1]}"
        npz = stem.with_suffix(".npz")
        if not npz.exists():
            s = big_scale if big_km2 and pa.GIS_AREA > big_km2 else scale
            try:
                d, share = dfci_array(fc, pa, years, dims, s, tile_km2=250 * (s / 10) ** 2)
                np.savez_compressed(npz, d=d, share=share, scale=s)
                log(f"  [{i}/{len(todo)}] {pa.SITE_ID} {pa.NAME_ENG} – {time.time() - t0:.0f}s")
            except Exception as e:
                log(f"  [{i}/{len(todo)}] LỖI {pa.SITE_ID} {pa.NAME_ENG}: {type(e).__name__}: {str(e)[:200]}")
                continue
        a = np.load(npz)
        png = stem.with_suffix(".png")
        Image.fromarray(render_dfci(a["d"], a["share"])).save(png, optimize=True)
        done[pa.SITE_ID] = png
    log(f"Bản đồ ΔFCI từng điểm ảnh: {len(done)}/{len(todo)}")
    return done
