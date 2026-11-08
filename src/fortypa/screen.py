"""Population of protected areas per country: national, terrestrial, state-governed sites, with forest indicators.

A site (SITE_ID, its parcels merged) enters the population when:
  DESIG_TYPE = National, STATUS Designated/Inscribed, REALM ≠ Marine, land part ≥ 1 km²,
  GOV_TYPE (most frequent over its parcels) in GOV_KEEP (state or shared governance; "Not Reported" kept),
and it is eligible for the comparison when it is also forested by the strict criterion: ForTy 2017 forest share
(classes 1, 2, 3, 4, 7) ≥ MIN_FOREST AND at least MIN_BIOME of it lies in a RESOLVE forest biome.

The indicators are computed once per country (100 m for sites < 100 km², 500 m above) and cached as
outputs/sang_loc/<ISO3>.csv.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ee
import pandas as pd

from . import gee

GOV_KEEP = ["Federal or national ministry or agency", "Sub-national ministry or agency",
            "Government-delegated management", "Joint governance", "Collaborative governance",
            "Transboundary governance", "Not Reported"]
FOREST_CLASSES = [1, 2, 3, 4, 7]
FOREST_BIOMES = [1, 2, 3, 4, 5, 6, 14]  # RESOLVE: tropical moist/dry/conifer, temperate broadleaf/conifer, boreal, mangrove
MIN_FOREST, MIN_BIOME = 0.10, 0.50
COLS = ["SITE_ID", "SITE_PID", "NAME", "DESIG_ENG", "IUCN_CAT", "GOV_TYPE", "GIS_AREA", "GIS_M_AREA"]
CHUNK = 150


def base(iso):
    """WDPA records of one country before the site-level filters (land area, governance)."""
    return (ee.FeatureCollection(gee.WDPA).filter(ee.Filter.eq("ISO3", iso))
            .filter(ee.Filter.inList("STATUS", ["Designated", "Inscribed"]))
            .filter(ee.Filter.eq("DESIG_TYPE", "National")).filter(ee.Filter.neq("REALM", "Marine")))


def _indicator_image():
    cls = gee.class_image(2017)
    biome = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017").reduceToImage(["BIOME_NUM"], ee.Reducer.first())
    return (cls.remap(FOREST_CLASSES, [1] * len(FOREST_CLASSES), 0).rename("forest")
            .addBands(cls.mask().unmask(0).rename("cov"))
            .addBands(biome.remap(FOREST_BIOMES, [1] * len(FOREST_BIOMES), 0).unmask(0).rename("fbiome")))


def _reduce_chunk(fc, img, scale):
    res = img.reduceRegions(fc.select(["SITE_PID"]), ee.Reducer.mean(), scale=scale, tileScale=4)
    rows = res.reduceColumns(ee.Reducer.toList(4), ["SITE_PID", "forest", "cov", "fbiome"]).get("list").getInfo()
    return pd.DataFrame(rows, columns=["SITE_PID", "forest", "cov", "fbiome"])


def screen(iso):
    """One row per site of the country (all governance types, GOV_OK marks the kept ones) with forest_frac,
    forty_cov (share of the site with ForTy data), forest_biome_frac and FOREST_OK (loose criterion, either
    condition; the comparison uses the strict one, see eligible)."""
    b = base(iso)
    rows = b.reduceColumns(ee.Reducer.toList(len(COLS)), COLS).get("list").getInfo()
    p = pd.DataFrame(rows, columns=COLS)
    p["SITE_ID"] = p.SITE_ID.astype(int)
    # WDPA sometimes repeats one parcel as several records with the same SITE_PID, each carrying the full GIS_AREA
    # (SWE 555773377 is repeated 18 times): count its area once
    p = p.drop_duplicates("SITE_PID")
    p["LAND"] = p.GIS_AREA - p.GIS_M_AREA
    site_land = p.groupby("SITE_ID").LAND.sum()
    p = p[p.SITE_ID.map(site_land) >= 1].copy()
    p["GOV_SITE"] = p.SITE_ID.map(p.groupby("SITE_ID").GOV_TYPE.agg(lambda s: s.mode().iat[0]))
    keep = p[p.GOV_SITE.isin(GOV_KEEP)]

    img = _indicator_image()
    jobs = []
    for small, scale in ((True, 100), (False, 500)):
        part = keep[(keep.SITE_ID.map(site_land) < 100) == small]
        pids = part.SITE_PID.tolist()
        jobs += [(pids[i:i + CHUNK], scale) for i in range(0, len(pids), CHUNK)]

    def run(job):
        # Earth Engine memory/time errors: split the chunk in two; a single parcel goes to a coarser scale (max 2 km)
        pids, scale = job
        try:
            return _reduce_chunk(b.filter(ee.Filter.inList("SITE_PID", pids)), img, scale)
        except ee.EEException:
            if len(pids) > 1:
                h = len(pids) // 2
                return pd.concat([run((pids[:h], scale)), run((pids[h:], scale))], ignore_index=True)
            if scale >= 2000:
                print(f"  bỏ qua {pids[0]} (lỗi cả ở {scale} m)", flush=True)
                return pd.DataFrame([[pids[0], None, None, None]], columns=["SITE_PID", "forest", "cov", "fbiome"])
            return run((pids, scale * 2))

    with ThreadPoolExecutor(8) as ex:
        ind = pd.concat(list(ex.map(run, jobs)), ignore_index=True) if jobs else pd.DataFrame(
            columns=["SITE_PID", "forest", "cov", "fbiome"])
    ind = ind.groupby("SITE_PID", as_index=False).mean()  # repeated records: mean over their geometries
    p = p.merge(ind, on="SITE_PID", how="left")

    w = p.LAND.clip(lower=1e-6)
    for c in ("forest", "cov", "fbiome"):
        p[c + "_w"] = p[c] * w
    p["w"] = w.where(p.forest.notna(), 0)
    p["wc"] = w.where(p["cov"].notna(), 0)
    g = p.groupby("SITE_ID")
    site = g.agg(NAME=("NAME", "first"), DESIG_ENG=("DESIG_ENG", "first"), IUCN_CAT=("IUCN_CAT", "first"),
                 GOV_TYPE=("GOV_SITE", "first"), PARCELS=("SITE_PID", "size"), LAND_KM2=("LAND", "sum"),
                 fw=("forest_w", "sum"), cw=("cov_w", "sum"), bw=("fbiome_w", "sum"), w=("w", "sum"),
                 wc=("wc", "sum")).reset_index()
    site["forest_frac"] = site.fw / site.w.where(site.w > 0)
    site["forty_cov"] = site.cw / site.wc.where(site.wc > 0)
    site["forest_biome_frac"] = site.bw / site.wc.where(site.wc > 0)
    site = site.drop(columns=["fw", "cw", "bw", "w", "wc"])
    site["GOV_OK"] = site.GOV_TYPE.isin(GOV_KEEP)
    site["FOREST_OK"] = site.GOV_OK & ((site.forest_frac >= MIN_FOREST) | (site.forest_biome_frac >= MIN_BIOME))
    site.insert(0, "ISO3", iso)
    return site.sort_values("LAND_KM2", ascending=False)


def load(iso, cache_dir):
    """screen(iso), cached as <cache_dir>/<ISO3>.csv."""
    f = Path(cache_dir) / f"{iso}.csv"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        screen(iso).to_csv(f, index=False, encoding="utf-8-sig")
    return pd.read_csv(f, encoding="utf-8-sig")


def eligible(site):
    """Sites of the comparison population: state governance and forested by the strict criterion, largest first."""
    ok = site.GOV_OK & (site.forest_frac >= MIN_FOREST) & (site.forest_biome_frac >= MIN_BIOME)
    return site[ok].sort_values("LAND_KM2", ascending=False).reset_index(drop=True)
