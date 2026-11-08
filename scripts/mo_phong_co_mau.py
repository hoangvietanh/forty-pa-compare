"""Mô phỏng cỡ mẫu: lấy mẫu ngẫu nhiên phân tầng theo cỡ khu từ tổng thể khu đủ điều kiện của mỗi nước, xem ước lượng
trung bình (theo khu, có trọng số tầng) lệch khỏi giá trị thật của cả tổng thể bao nhiêu.

Tổng thể: kết quả sàng lọc `outputs/sang_loc/<ISO3>.csv`, tiêu chí đã chốt: GOV nhà nước + rừng chặt (tỷ lệ rừng ForTy
2017 ≥ 10% VÀ ≥ 50% diện tích trong biome rừng).
Chỉ tiêu:
  - mọi nước: % rừng ForTy 2017 của khu (có sẵn cho toàn bộ tổng thể, dùng làm đại diện cho chỉ tiêu hiện trạng);
  - Việt Nam: thêm FCI 2025 và ΔFCI 2017→2025 từ cache diện tích (dự án này + dự án VN cũ).
Ra: outputs/mo_phong_co_mau.csv (sai số ±, nửa độ rộng khoảng 95% của ước lượng quanh giá trị thật).
Chạy: PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/mo_phong_co_mau.py
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fortypa import screen  # noqa: E402
from fortypa.compare import SIZE_BINS, allocate  # noqa: E402
from fortypa.index import WEIGHTS  # noqa: E402

COUNTRIES = ["VNM", "LAO", "KHM", "THA", "PHL", "IDN", "BRA", "MDG", "CMR", "GAB", "USA", "AUS", "RUS"]
AREA_CACHES = [ROOT / "outputs" / "areas",
               Path(r"C:\Users\gfd\Documents\Claude\Projects\2026.10.25 nature forest alphaearth map\outputs\areas")]
NS = [20, 30, 40, 60, 80, 100, 150, 200, 250, 300]
REPS = 2000
SEED = 20261108


def population(iso):
    s = screen.eligible(pd.read_csv(ROOT / "outputs" / "sang_loc" / f"{iso}.csv", encoding="utf-8-sig"))
    s["forest_pct"] = s.forest_frac * 100
    s["stratum"] = pd.cut(s.LAND_KM2, SIZE_BINS, right=False, labels=False)
    return s.reset_index(drop=True)


def vn_fci(site_ids):
    """FCI 2025 và ΔFCI 2017→2025 cho các khu VN có cache diện tích."""
    rows = []
    for sid in site_ids:
        f = next((d / f"{sid}_2017-2025.json" for d in AREA_CACHES if (d / f"{sid}_2017-2025.json").exists()), None)
        if f is None:
            continue
        a = pd.DataFrame(json.loads(f.read_text(encoding="utf-8")))
        a["w"] = a.value.map(WEIGHTS) * a.area_ha
        g = a.groupby("year")
        fci = 100 * g.w.sum() / g.area_ha.sum()
        rows.append(dict(SITE_ID=sid, fci_2025=fci[2025], dfci=fci[2025] - fci[2017]))
    return pd.DataFrame(rows)


def simulate(pop, col, n, rng):
    """Nửa độ rộng khoảng 95% của (ước lượng − giá trị thật), ước lượng = trung bình phân tầng có trọng số."""
    true = pop[col].mean()
    groups = [g[col].to_numpy() for _, g in pop.groupby("stratum")]
    sizes = np.array([len(g) for g in groups])
    if n >= sizes.sum():
        return 0.0
    alloc = allocate(sizes, n)
    err = np.empty(REPS)
    for r in range(REPS):
        est = sum(N_h * rng.choice(g, n_h, replace=False).mean() for g, N_h, n_h in zip(groups, sizes, alloc) if n_h)
        err[r] = est / sizes.sum() - true
    return float(np.percentile(np.abs(err), 95))


def main():
    rng = np.random.default_rng(SEED)
    out = []
    for iso in COUNTRIES:
        pop = population(iso)
        cols = ["forest_pct"]
        if iso == "VNM":
            pop = pop.merge(vn_fci(pop.SITE_ID), on="SITE_ID", how="left")
            print(f"VNM: {pop.fci_2025.notna().sum()}/{len(pop)} khu có cache FCI")
            cols += ["fci_2025", "dfci"]
        for col in cols:
            p = pop.dropna(subset=[col])
            row = dict(ISO3=iso, chi_tieu=col, N=len(p), gia_tri_that=p[col].mean(), do_lech_chuan=p[col].std())
            row.update({f"n{n}": simulate(p, col, n, rng) for n in NS})
            out.append(row)
            print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
    pd.DataFrame(out).to_csv(ROOT / "outputs" / "mo_phong_co_mau.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
