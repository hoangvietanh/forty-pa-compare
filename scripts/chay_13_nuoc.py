"""So sánh 13 nước theo khung đã chốt (KHUNG_NGHIEN_CUU.md, mục 8).

Mỗi nước:
  1. tổng thể: khu quốc gia, trên cạn, quản lý nhà nước, có rừng theo tiêu chí chặt (screen.eligible);
  2. ≤ 200 khu thì lấy tất cả, nhiều hơn thì rút ngẫu nhiên phân tầng theo cỡ khu (compare.sample_pas, trọng số W);
  3. diện tích từng loại rừng 2017–2025: khu có polygon < POINT_MIN_KM2 đếm toàn bộ pixel 10 m, khu lớn hơn rút
     N_POINTS điểm (cùng bộ điểm cho cả 9 năm). Khu đã có bảng đếm toàn bộ trong cache thì giữ bảng đó.
Sau đó: FCI, chỉ tiêu từng khu, bảng so sánh có trọng số, kiểm định từng cặp nước, xếp hạng.

Kết quả: outputs/so_sanh_13/ (các CSV); cache dùng chung outputs/areas, outputs/transitions, outputs/points.
Chạy lại chỉ tính phần còn thiếu.
Chạy: PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/chay_13_nuoc.py [ISO3 ...]
"""
import shutil
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fortypa import compare, gee, index, screen  # noqa: E402

PROJECT = "ee-hoangvietanh"
YEARS = list(range(2017, 2026))
POINT_MIN_KM2 = 100
N_POINTS = 5000
AREA_SCALES = (10, 20, 30, 60, 100)
MAX_PIXELS = 2e7
WORKERS = 6
OUT = ROOT / "outputs"
RES = OUT / "so_sanh_13"
# kết quả đếm toàn bộ pixel của dự án khu bảo tồn Việt Nam (cùng phương pháp, cùng tên file theo SITE_ID)
REUSE_CACHE_FROM = Path(r"C:\Users\gfd\Documents\Claude\Projects\2026.10.25 nature forest alphaearth map\outputs")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def reuse_cache(site_ids):
    ids, n = {str(s) for s in site_ids}, 0
    for sub in ("areas", "transitions"):
        for f in (REUSE_CACHE_FROM / sub).glob("*.json"):
            if f.name.split("_")[0] in ids and not (OUT / sub / f.name).exists():
                shutil.copy2(f, OUT / sub / f.name)
                n += 1
    return n


def country(iso):
    elig = screen.eligible(screen.load(iso, OUT / "sang_loc"))
    samp = compare.sample_pas(elig, compare.sample_size(iso, len(elig)))
    fc, geo = gee.site_collection(screen.base(iso), samp.SITE_ID)
    pas = samp.merge(geo, on="SITE_ID").assign(NAME_ENG=lambda d: d.NAME)
    log(f"{iso}: {len(elig)} khu đủ điều kiện, phân tích {len(pas)} "
        f"({(pas.GEOM_KM2 >= POINT_MIN_KM2).sum()} khu lấy mẫu điểm)")
    if REUSE_CACHE_FROM.exists():
        log(f"{iso}: chép {reuse_cache(pas.SITE_ID)} file cache từ dự án Việt Nam")
    big = pas[pas.GEOM_KM2 >= POINT_MIN_KM2]
    failed = gee.compute_points(fc, big, YEARS, OUT / "points", OUT / "areas", OUT / "transitions", n=N_POINTS,
                                workers=WORKERS, log=log)
    kw = dict(scales=AREA_SCALES, workers=WORKERS, max_pixels=MAX_PIXELS, log=log)
    ok = pas[~pas.SITE_ID.isin(failed)]
    areas, fa = gee.compute_areas(fc, ok, YEARS, OUT / "areas", **kw)
    trans, ft = gee.compute_transitions(fc, ok, YEARS, OUT / "transitions", **kw)
    bad = set(failed) | set(fa) | set(ft)
    if bad:
        log(f"{iso}: {len(bad)} khu lỗi, bỏ khỏi phân tích: {sorted(bad)}")
    pas = pas.assign(ISO3=iso, OK=~pas.SITE_ID.isin(bad))
    pas.to_csv(RES / f"khu_{iso}.csv", index=False, encoding="utf-8-sig")
    keep = set(pas.SITE_ID[pas.OK])
    return pas, areas[areas.SITE_ID.isin(keep)], trans[trans.SITE_ID.isin(keep)]


def main(isos):
    gee.init(PROJECT)
    for d in ("areas", "transitions", "points", "so_sanh_13"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    parts = [country(iso) for iso in isos]
    pas = pd.concat([p for p, _, _ in parts], ignore_index=True)
    pas = pas[pas.OK]
    areas = pd.concat([a for _, a, _ in parts], ignore_index=True)
    trans = pd.concat([t for _, _, t in parts], ignore_index=True)

    fci = index.fci_index(areas, YEARS)
    ind = compare.pa_indicators(pas, areas, fci, trans, YEARS)
    ind.merge(index.fci_series(areas, YEARS).round(3).add_prefix("fci_nam_"), left_on="SITE_ID", right_index=True) \
        .to_csv(RES / "chi_so_FCI_tung_khu.csv", index=False, encoding="utf-8-sig")
    series = compare.country_series(pas, areas, YEARS)
    series.to_csv(RES / "FCI_theo_nuoc_theo_nam.csv", index=False, encoding="utf-8-sig")
    table = compare.country_table(ind, series, YEARS)
    table.to_csv(RES / "so_sanh_nuoc.csv", index=False, encoding="utf-8-sig")
    rank, _ = compare.ranking(table, YEARS)
    rank.to_csv(RES / "xep_hang_nuoc.csv", encoding="utf-8-sig")
    compare.pairwise_tests(ind).to_csv(RES / "kiem_dinh_tung_cap.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(table[["country", "n", "N", "fci_median_2025", "fci_forest_pooled_2025", "dfci_median", "dfci_ci_lo",
                 "dfci_ci_hi", "pct_negative", "natural_change_pct"]].round(2).to_string(index=False))
    print(rank[["Hạng trạng thái", "Điểm xu hướng", "Hạng chung"]].to_string())


if __name__ == "__main__":
    main(sys.argv[1:] or list(compare.COUNTRIES.ISO3))
