"""Comparing countries: indicators per PA, country aggregates with bootstrap intervals, pairwise permutation tests
and a rank-based score.

Two questions are kept apart, because they are answered by different numbers:
- state: how natural the land in the PAs is in the last year (FCI level). This depends on the biome as much as on
  protection: a desert or glacier park has a low FCI however well it is protected.
- trend: how the FCI moved between the first and last year (ΔFCI, its share of the starting FCI, the share of PAs
  that declined, the net change of natural forest). This is what protection can influence.
"""
import math

import numpy as np
import pandas as pd

from .gee import NATURAL
from .index import DECLINE, RECOVERY, WEIGHTS, fci_series

# ΔFCI as % of the first-year FCI only where that FCI is at least this: in desert parks FCI is near 0 and a change of
# a few hundredths of a point would read as −90 %.
REL_MIN_FCI = 5.0

COUNTRIES = pd.DataFrame([
    ("VNM", "Việt Nam", "#2a78d6"),
    ("USA", "Mỹ", "#eb6834"),
    ("AUS", "Úc", "#1baf7a"),
], columns=["ISO3", "name", "color"])


def select_groups(df, top_n=20, n_mid=10, n_groups=4):
    """Picks the PAs of one country from the full list of eligible PAs ranked by land area (RANK 1 = largest):
    - "large": the top_n largest;
    - "medium": split the list into n_groups groups of equal count by area, counted from the largest, and take the
      n_mid largest PAs of the second group, skipping any already in "large".
    Adds GROUP and N_ELIGIBLE (number of eligible PAs in the country)."""
    n = len(df)
    lo, hi = math.ceil(n / n_groups), math.ceil(2 * n / n_groups)  # second group = RANK lo+1 … hi
    large = df[df.RANK <= top_n].assign(GROUP="large")
    medium = df[(df.RANK > max(lo, top_n)) & (df.RANK <= hi)].head(n_mid).assign(GROUP="medium")
    return pd.concat([large, medium]).assign(N_ELIGIBLE=n, Q2_FROM=lo + 1, Q2_TO=hi)


def group_label(key, n):
    return f"{n} khu lớn nhất" if key == "large" else f"{n} khu cỡ vừa"


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
    changed class."""
    y0, y1 = years[0], years[-1]
    f = _fci(_class_areas(areas, [y0, y1])).unstack("year")
    cols = [c for c in ("ISO3", "GROUP", "RANK", "SITE_ID", "NAME", "DESIG_ENG", "LAND_KM2") if c in pas]
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
    return out.reset_index()


def country_series(pas, areas, years):
    """Per country and year: pooled FCI (all PAs of the country as one area, i.e. weighted by area), median FCI of its
    PAs, and the pooled FCI minus its first-year value."""
    t = _class_areas(areas, years).reset_index()
    t = t.merge(pas[["SITE_ID", "ISO3"]], on="SITE_ID")
    pooled = _fci(t.groupby(["ISO3", "year"])[list(range(1, 8))].sum())[["fci", "fci_forest", "forest_pct"]]
    per_pa = _fci(t.set_index(["ISO3", "SITE_ID", "year"])[list(range(1, 8))])
    pooled["fci_median"] = per_pa.fci.groupby(["ISO3", "year"]).median()
    pooled["dfci_pooled"] = pooled.fci - pooled.fci.groupby("ISO3").transform("first")
    return pooled.reset_index()


def bootstrap_ci(values, stat=np.median, n=10000, level=0.95, seed=0):
    """Percentile bootstrap interval of stat(values)."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    rng = np.random.default_rng(seed)
    boots = stat(rng.choice(v, size=(n, len(v)), replace=True), axis=1)
    a = (1 - level) / 2
    return float(np.quantile(boots, a)), float(np.quantile(boots, 1 - a))


def permutation_p(a, b, stat=np.median, n=20000, seed=0):
    """Two-sided p-value for stat(a) − stat(b) under random relabelling of the pooled values."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    obs = stat(a) - stat(b)
    pool = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    idx = np.argsort(rng.random((n, len(pool))), axis=1)
    perm = pool[idx]
    d = stat(perm[:, :len(a)], axis=1) - stat(perm[:, len(a):], axis=1)
    return float((np.sum(np.abs(d) >= abs(obs) - 1e-12) + 1) / (n + 1))


def country_table(ind, series, years):
    """One row per country (in COUNTRIES order) with the state and trend indicators."""
    y0, y1 = years[0], years[-1]
    rows = []
    for c in COUNTRIES.itertuples():
        d = ind[ind.ISO3 == c.ISO3]
        if d.empty:
            continue
        s = series[series.ISO3 == c.ISO3].set_index("year")
        lo, hi = bootstrap_ci(d.dfci)
        nat0, nat1 = d[f"natural_ha_{y0}"].sum(), d[f"natural_ha_{y1}"].sum()
        rows.append({
            "ISO3": c.ISO3, "country": c.name, "n": len(d), "land_km2": d.LAND_KM2.sum(),
            f"fci_pooled_{y0}": s.fci[y0], f"fci_pooled_{y1}": s.fci[y1], "dfci_pooled": s.fci[y1] - s.fci[y0],
            f"fci_median_{y1}": d[f"fci_{y1}"].median(), f"fci_forest_pooled_{y1}": s.fci_forest[y1],
            f"forest_pct_pooled_{y1}": s.forest_pct[y1],
            "dfci_median": d.dfci.median(), "dfci_ci_lo": lo, "dfci_ci_hi": hi, "dfci_mean": d.dfci.mean(),
            "dfci_rel_median": d.dfci_rel.median(),
            "n_decline": int((d.verdict == DECLINE).sum()), "n_recovery": int((d.verdict == RECOVERY).sum()),
            "pct_decline": 100 * (d.verdict == DECLINE).mean(), "pct_negative": 100 * (d.dfci < 0).mean(),
            "natural_change_pct": 100 * (nat1 - nat0) / nat0 if nat0 else np.nan,
            "changed_pct_median": d.changed_pct.median() if "changed_pct" in d else np.nan,
        })
    return pd.DataFrame(rows)


def pairwise_tests(ind, col="dfci"):
    """Median difference of `col` and permutation p-value for every pair of countries."""
    iso = [c for c in COUNTRIES.ISO3 if c in set(ind.ISO3)]
    name = COUNTRIES.set_index("ISO3").name
    rows = []
    for i, a in enumerate(iso):
        for b in iso[i + 1:]:
            va, vb = ind.loc[ind.ISO3 == a, col].dropna(), ind.loc[ind.ISO3 == b, col].dropna()
            rows.append({"a": name[a], "b": name[b], "median_a": va.median(), "median_b": vb.median(),
                         "diff": va.median() - vb.median(), "p": permutation_p(va, vb)})
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
    """Rank of each country on every criterion (1 = best), the mean rank per group (state, trend) and overall
    (mean of the two group scores, so the four trend criteria do not outweigh the two state criteria)."""
    y0, y1 = years[0], years[-1]
    t = table.set_index("country")
    out = pd.DataFrame(index=t.index)
    groups = {}
    for col, label, higher, group in CRITERIA:
        col, label = col.format(y0=y0, y1=y1), label.format(y0=y0, y1=y1)
        out[label] = t[col].rank(ascending=not higher, method="min")
        groups.setdefault(group, []).append(label)
    for g, cols in groups.items():
        out[f"Điểm {g.lower()}"] = out[cols].mean(axis=1)
    out["Điểm chung"] = out[[f"Điểm {g.lower()}" for g in groups]].mean(axis=1)
    out["Hạng chung"] = out["Điểm chung"].rank(method="min").astype(int)
    return out.sort_values("Điểm chung"), groups
