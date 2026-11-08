"""Comparing countries: sample of PAs per country, indicators per PA, country aggregates with stratified bootstrap
intervals, pairwise tests and a rank-based score.

Each country's PAs are either all its eligible PAs (census) or a random sample stratified by size (sample_pas). Every
PA carries its sampling weight W = N_H / N_DRAWN (PAs in its size stratum / PAs drawn from it; 1 in a census) and its
STRATUM, and every country figure is weighted by W: a weighted median or share "per PA", W × area when the PAs are
pooled into one area. Tables without W (the earlier top-30 selection) count every PA once.

Two questions are kept apart, because they are answered by different numbers:
- state: how natural the land in the PAs is in the last year (FCI level). This depends on the biome as much as on
  protection: a desert or glacier park has a low FCI however well it is protected.
- trend: how the FCI moved between the first and last year (ΔFCI, its share of the starting FCI, the share of PAs
  that declined, the net change of natural forest). This is what protection can influence.
"""

import numpy as np
import pandas as pd

from .gee import NATURAL
from .index import DECLINE, RECOVERY, WEIGHTS, fci_series

# ΔFCI as % of the first-year FCI only where that FCI is at least this: in desert parks FCI is near 0 and a change of
# a few hundredths of a point would read as −90 %.
REL_MIN_FCI = 5.0

COUNTRIES = pd.DataFrame([
    ("VNM", "Việt Nam", "#2a78d6"),
    ("LAO", "Lào", "#7b4fd6"),
    ("KHM", "Campuchia", "#c43d8f"),
    ("THA", "Thái Lan", "#d6a400"),
    ("PHL", "Philippines", "#3fa7c4"),
    ("IDN", "Indonesia", "#8c5a2b"),
    ("BRA", "Brazil", "#4f9d2d"),
    ("MDG", "Madagascar", "#e0457b"),
    ("CMR", "Cameroon", "#5b6b2f"),
    ("GAB", "Gabon", "#2f8f83"),
    ("USA", "Mỹ", "#eb6834"),
    ("AUS", "Úc", "#1baf7a"),
    ("RUS", "Nga", "#6b7a99"),
], columns=["ISO3", "name", "color"])

# PAs drawn per country when it has more than CENSUS_MAX eligible PAs, chosen by simulation for a 95 % error of
# about ±3 FCI points on the per-PA mean (scripts/mo_phong_co_mau.py); countries up to CENSUS_MAX take all.
CENSUS_MAX = 200
SAMPLE_N = {"IDN": 150, "AUS": 150, "BRA": 250, "RUS": 250, "USA": 300}
SIZE_BINS = [1, 10, 100, 1000, np.inf]  # km² of land, the strata
SEED = 20261108


def allocate(sizes, n):
    """n PAs spread over strata in proportion to their sizes, at least 2 per stratum (the whole stratum if
    smaller)."""
    sizes = np.asarray(sizes)
    alloc = np.minimum(sizes, 2)
    rest = n - alloc.sum()
    while rest > 0:
        room = sizes - alloc
        if room.sum() == 0:
            break
        share = np.where(room > 0, sizes, 0) / np.where(room > 0, sizes, 0).sum() * rest
        add = np.minimum(np.floor(share).astype(int), room)
        if add.sum() == 0:
            add[np.argmax(np.where(room > 0, share, -1))] = 1
        alloc += add
        rest = n - alloc.sum()
    return alloc


def sample_size(iso3, n_eligible):
    """PAs to draw for a country, None for a census."""
    return None if n_eligible <= CENSUS_MAX else SAMPLE_N[iso3]


def sample_pas(pop, n=None, seed=SEED):
    """Stratified random sample of n PAs from a country's eligible PAs (screen.eligible), strata by LAND_KM2
    (SIZE_BINS). n None or ≥ the number of PAs takes them all. Adds STRATUM, N_H, N_DRAWN and W = N_H / N_DRAWN."""
    pop = pop.assign(STRATUM=pd.cut(pop.LAND_KM2, SIZE_BINS, right=False, labels=False)).reset_index(drop=True)
    sizes = pop.STRATUM.value_counts().sort_index()
    take = sizes.to_numpy() if n is None or n >= len(pop) else allocate(sizes.to_numpy(), n)
    rng = np.random.default_rng(seed)
    parts = []
    for (h, n_h_all), n_h in zip(sizes.items(), take):
        g = pop[pop.STRATUM == h]
        parts.append(g.iloc[np.sort(rng.choice(len(g), n_h, replace=False))]
                     .assign(N_H=n_h_all, N_DRAWN=n_h, W=n_h_all / n_h))
    return pd.concat(parts).sort_values("LAND_KM2", ascending=False).reset_index(drop=True)


def select_top(df, top_n=30):
    """The top_n largest PAs of one country from the full list of eligible PAs ranked by land area (RANK 1 =
    largest). Adds GROUP ("large"), N_ELIGIBLE (number of eligible PAs in the country) and NO (display number, = RANK)."""
    return df[df.RANK <= top_n].assign(GROUP="large", N_ELIGIBLE=len(df), NO=lambda d: d.RANK)


def group_label(n):
    return f"{n} khu lớn nhất"


def wmedian(v, w):
    """Weighted median (the first value whose cumulative weight reaches half the total), NaNs dropped."""
    v, w = np.asarray(v, float), np.asarray(w, float)
    ok = ~np.isnan(v)
    v, w = v[ok], w[ok]
    if not len(v):
        return np.nan
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return float(v[o][np.searchsorted(c, c[-1] / 2)])


def wmean(v, w):
    v, w = np.asarray(v, float), np.asarray(w, float)
    ok = ~np.isnan(v)
    return float(np.sum(v[ok] * w[ok]) / np.sum(w[ok])) if ok.any() else np.nan


def _weights(d):
    return d.W if "W" in d else pd.Series(1.0, index=d.index)


def strat_boot(d, stat, n=2000, seed=0):
    """stat(d') over n stratified bootstrap replicates d' of the PA table d: within every STRATUM its PAs are drawn
    with replacement, keeping their weights. The spread is the sampling error of the country figure."""
    rng = np.random.default_rng(seed)
    strata = (d.STRATUM if "STRATUM" in d else pd.Series(0, index=d.index)).to_numpy()
    groups = [np.flatnonzero(strata == h) for h in np.unique(strata)]
    out = np.empty(n)
    for r in range(n):
        idx = np.concatenate([g[rng.integers(0, len(g), len(g))] for g in groups])
        out[r] = stat(d.iloc[idx])
    return out


def _class_areas(areas, years):
    """SITE_ID × year × class value (ha)."""
    return (areas[areas.year.isin(years)]
            .pivot_table(index=["SITE_ID", "year"], columns="value", values="area_ha", aggfunc="sum")
            .reindex(columns=range(1, 8)).fillna(0))


def _fci(t):
    """FCI over all analysed land, FCI over forest only (classes 1–5, 7), forest share and natural forest area,
    from a table whose columns are class values."""
    w = sum(t[v] * WEIGHTS[v] for v in WEIGHTS)
    forest = t.drop(columns=6).sum(axis=1)
    total = t.sum(axis=1)
    return pd.DataFrame({"fci": 100 * w / total, "fci_forest": (100 * w / forest).where(forest > 0),
                         "forest_pct": 100 * forest / total, "natural_ha": t[list(NATURAL)].sum(axis=1),
                         "forest_ha": forest, "total_ha": total})


def pa_indicators(pas, areas, fci, transitions, years):
    """One row per PA: identity, FCI of the first and last year (all land and forest only), ΔFCI and its share of the
    starting FCI, 9-year trend and verdict, forest share, net change of natural forest, gross share of land that
    changed class, and n_points (size of the point sample, empty for a full count)."""
    y0, y1 = years[0], years[-1]
    f = _fci(_class_areas(areas, [y0, y1])).unstack("year")
    cols = [c for c in ("ISO3", "GROUP", "NO", "RANK", "SITE_ID", "NAME", "DESIG_ENG", "LAND_KM2", "STRATUM", "W")
            if c in pas]
    out = pas[cols].merge(
        fci[["SITE_ID", f"fci_{y0}", f"fci_{y1}", "dfci", "trend", "mk_p", "verdict"]], on="SITE_ID")
    out = out.set_index("SITE_ID")
    out["dfci_rel"] = 100 * out.dfci / out[f"fci_{y0}"].where(out[f"fci_{y0}"] >= REL_MIN_FCI)
    # the year-to-year step with the largest fall, and its share of the whole change: a fall packed into one or two
    # years looks like a disturbance event (fire, storm), a spread-out one like gradual conversion
    s = fci_series(areas, years)
    steps = s.diff(axis=1).iloc[:, 1:]
    out["drop_year"] = steps.idxmin(axis=1)
    out["drop_share"] = 100 * steps.min(axis=1) / out.dfci.where(out.dfci < 0)
    for y in (y0, y1):
        out[f"fci_forest_{y}"] = f[("fci_forest", y)]
        out[f"forest_pct_{y}"] = f[("forest_pct", y)]
    nat0, nat1 = f[("natural_ha", y0)], f[("natural_ha", y1)]
    out["natural_change_pct"] = (100 * (nat1 - nat0) / nat0.where(nat0 > 0))
    out["natural_ha_" + str(y0)], out["natural_ha_" + str(y1)] = nat0, nat1
    if transitions is not None:
        t = transitions.groupby("SITE_ID")
        out["changed_pct"] = 100 * t.apply(lambda d: d[d.change > 0].area_ha.sum()) / t.area_ha.sum()
    out["scale_m"] = areas.groupby("SITE_ID").scale_m.max()
    if "n_points" in areas:
        out["n_points"] = areas.groupby("SITE_ID").n_points.max()
    return out.reset_index()


def country_series(pas, areas, years):
    """Per country and year: pooled FCI (all PAs of the country as one area, each PA's areas × W), weighted median FCI
    of its PAs, and the pooled FCI minus its first-year value."""
    cls = list(range(1, 8))
    t = _class_areas(areas, years).reset_index()
    t = t.merge(pas[["SITE_ID", "ISO3"]].assign(W=_weights(pas).to_numpy()), on="SITE_ID")
    pooled = _fci(t[cls].mul(t.W, axis=0).groupby([t.ISO3, t.year]).sum())[["fci", "fci_forest", "forest_pct"]]
    per_pa = _fci(t.set_index(["ISO3", "SITE_ID", "year"])[cls])
    per_pa["W"] = t.W.to_numpy()
    pooled["fci_median"] = per_pa.groupby(level=["ISO3", "year"]).apply(lambda g: wmedian(g.fci, g.W))
    pooled["dfci_pooled"] = pooled.fci - pooled.fci.groupby("ISO3").transform("first")
    return pooled.reset_index()


def _wshare(mask, w):
    return 100 * float(np.sum(w[mask]) / np.sum(w))


def country_table(ind, series, years, n_boot=2000):
    """One row per country (in COUNTRIES order) with the state and trend indicators, every per-PA figure weighted by
    W; n = PAs analysed, N = eligible PAs they stand for. The 95 % interval of the median ΔFCI comes from the
    stratified bootstrap."""
    y0, y1 = years[0], years[-1]
    rows = []
    for c in COUNTRIES.itertuples():
        d = ind[ind.ISO3 == c.ISO3]
        if d.empty:
            continue
        w = _weights(d).to_numpy()
        s = series[series.ISO3 == c.ISO3].set_index("year")
        boot = strat_boot(d, lambda b: wmedian(b.dfci, _weights(b)), n_boot)
        lo, hi = np.quantile(boot, [0.025, 0.975])
        fboot = strat_boot(d, lambda b: wmedian(b[f"fci_{y1}"], _weights(b)), n_boot, seed=1)
        flo, fhi = np.quantile(fboot, [0.025, 0.975])
        nat0, nat1 = np.sum(d[f"natural_ha_{y0}"] * w), np.sum(d[f"natural_ha_{y1}"] * w)
        rows.append({
            "ISO3": c.ISO3, "country": c.name, "n": len(d), "N": float(w.sum()),
            "land_km2": float(np.sum(d.LAND_KM2 * w)),
            f"fci_pooled_{y0}": s.fci[y0], f"fci_pooled_{y1}": s.fci[y1], "dfci_pooled": s.fci[y1] - s.fci[y0],
            f"fci_median_{y1}": wmedian(d[f"fci_{y1}"], w), f"fci_median_{y1}_lo": flo, f"fci_median_{y1}_hi": fhi,
            f"fci_forest_pooled_{y1}": s.fci_forest[y1],
            f"forest_pct_pooled_{y1}": s.forest_pct[y1],
            "dfci_median": wmedian(d.dfci, w), "dfci_ci_lo": lo, "dfci_ci_hi": hi, "dfci_mean": wmean(d.dfci, w),
            "dfci_rel_median": wmedian(d.dfci_rel, w),
            "n_decline": int((d.verdict == DECLINE).sum()), "n_recovery": int((d.verdict == RECOVERY).sum()),
            "pct_decline": _wshare((d.verdict == DECLINE).to_numpy(), w),
            "pct_negative": _wshare((d.dfci < 0).to_numpy(), w),
            "natural_change_pct": 100 * (nat1 - nat0) / nat0 if nat0 else np.nan,
            "changed_pct_median": wmedian(d.changed_pct, w) if "changed_pct" in d else np.nan,
        })
    return pd.DataFrame(rows)


def pairwise_tests(ind, col="dfci", n_boot=2000):
    """Difference of the weighted medians of `col` for every pair of countries, its 95 % stratified bootstrap
    interval and a two-sided bootstrap p-value (twice the share of replicates on the far side of 0)."""
    iso = [c for c in COUNTRIES.ISO3 if c in set(ind.ISO3)]
    name = COUNTRIES.set_index("ISO3").name
    med = lambda b: wmedian(b[col], _weights(b))
    boot = {i: strat_boot(ind[ind.ISO3 == i], med, n_boot, seed=k) for k, i in enumerate(iso)}
    rows = []
    for i, a in enumerate(iso):
        for b in iso[i + 1:]:
            ma, mb = med(ind[ind.ISO3 == a]), med(ind[ind.ISO3 == b])
            d = boot[a] - boot[b]
            p = min(1.0, 2 * min(np.mean(d <= 0), np.mean(d >= 0)) + 1 / n_boot)
            rows.append({"a": name[a], "b": name[b], "median_a": ma, "median_b": mb, "diff": ma - mb,
                         "ci_lo": float(np.quantile(d, 0.025)), "ci_hi": float(np.quantile(d, 0.975)), "p": p})
    return pd.DataFrame(rows)


# (column of country_table, label, higher is better, group)
CRITERIA = [
    ("fci_median_{y1}", "FCI {y1} (trung vị các khu)", True, "Trạng thái"),
    ("fci_forest_pooled_{y1}", "FCI phần có rừng {y1} (gộp)", True, "Trạng thái"),
    ("dfci_median", "ΔFCI {y0}→{y1} (trung vị các khu)", True, "Xu hướng"),
    ("dfci_rel_median", "ΔFCI so với FCI {y0} (trung vị, %)", True, "Xu hướng"),
    ("pct_negative", "% khu có ΔFCI âm", False, "Xu hướng"),
    ("natural_change_pct", "Thay đổi ròng rừng tự nhiên (gộp, %)", True, "Xu hướng"),
]


def ranking(table, years):
    """Rank of each country on every criterion (1 = best), then:
    - state score: mean of the two state FCI values (0–100, higher = better), so the size of a gap counts, not only
      its order; ranked into the state rank;
    - trend score: mean rank of the four trend criteria (lower = better);
    - overall score: mean of the state rank and the trend score (lower = better), so the four trend criteria do not
      outweigh the state."""
    y0, y1 = years[0], years[-1]
    t = table.set_index("country")
    out = pd.DataFrame(index=t.index)
    groups = {}
    for col, label, higher, group in CRITERIA:
        col, label = col.format(y0=y0, y1=y1), label.format(y0=y0, y1=y1)
        out[label] = t[col].rank(ascending=not higher, method="min")
        groups.setdefault(group, []).append(label)
    state_cols = [c.format(y0=y0, y1=y1) for c, _, _, g in CRITERIA if g == "Trạng thái"]
    out["Điểm trạng thái"] = t[state_cols].mean(axis=1)
    out["Hạng trạng thái"] = out["Điểm trạng thái"].rank(ascending=False, method="min")
    out["Điểm xu hướng"] = out[groups["Xu hướng"]].mean(axis=1)
    out["Điểm chung"] = out[["Hạng trạng thái", "Điểm xu hướng"]].mean(axis=1)
    out["Hạng chung"] = out["Điểm chung"].rank(method="min").astype(int)
    return out.sort_values("Điểm chung"), groups
