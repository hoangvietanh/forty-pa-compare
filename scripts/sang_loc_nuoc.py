"""Sàng lọc quốc gia ứng viên: số khu bảo tồn đủ điều kiện sau khi lọc GOV_TYPE và lọc rừng.

Khu đủ điều kiện (cấp SITE_ID, các mảnh cùng SITE_ID được gộp):
  DESIG_TYPE = National, STATUS Designated/Inscribed, REALM ≠ Marine, phần đất ≥ 1 km²,
  GOV_TYPE thuộc nhóm nhà nước (GOV_KEEP; "Not Reported" được giữ và đếm riêng).
Khu có rừng: tỷ lệ rừng ForTy 2017 (lớp 1, 2, 3, 4, 7) ≥ 10% HOẶC ≥ 50% diện tích nằm trong biome rừng RESOLVE.

Kết quả từng nước: outputs/sang_loc/<ISO3>.csv (cache, chạy lại chỉ tính nước thiếu); tổng hợp: outputs/sang_loc_nuoc.csv.
Chạy: PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/sang_loc_nuoc.py [ISO3 ...]
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fortypa import gee, screen  # noqa: E402
from fortypa.screen import MIN_BIOME, MIN_FOREST  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "sang_loc"

COUNTRIES = {
    "VNM": "Việt Nam", "LAO": "Lào", "KHM": "Campuchia", "THA": "Thái Lan", "MMR": "Myanmar", "MYS": "Malaysia",
    "IDN": "Indonesia", "PHL": "Philippines", "PNG": "Papua New Guinea", "JPN": "Nhật Bản", "KOR": "Hàn Quốc",
    "NPL": "Nepal", "LKA": "Sri Lanka", "BRA": "Brazil", "PER": "Peru", "COL": "Colombia", "CRI": "Costa Rica",
    "MEX": "Mexico", "COD": "CHDC Congo", "GAB": "Gabon", "CMR": "Cameroon", "KEN": "Kenya", "TZA": "Tanzania",
    "MDG": "Madagascar", "ZAF": "Nam Phi", "USA": "Mỹ", "CAN": "Canada", "AUS": "Úc", "NZL": "New Zealand",
    "FIN": "Phần Lan", "SWE": "Thụy Điển", "DEU": "Đức", "FRA": "Pháp", "RUS": "Nga",
}
def summarize(site):
    gov, fo = site[site.GOV_OK], site[site.FOREST_OK]
    nr = lambda s: s.isin(["Not Reported", "Not Applicable", "Not Assigned"]).mean() * 100 if len(s) else float("nan")
    return dict(
        n_quoc_gia_tren_can=len(site),
        n_sau_loc_gov=len(gov),
        n_gov_not_reported=int((gov.GOV_TYPE == "Not Reported").sum()),
        n_co_rung=len(fo),
        n_co_rung_ty_le_10=int((gov.forest_frac >= MIN_FOREST).sum()),
        n_co_rung_biome=int((gov.forest_biome_frac >= MIN_BIOME).sum()),
        n_co_rung_ca_hai=int(((gov.forest_frac >= MIN_FOREST) & (gov.forest_biome_frac >= MIN_BIOME)).sum()),
        n_co_rung_ge100km2=int((fo.LAND_KM2 >= 100).sum()),
        dien_tich_co_rung_km2=fo.LAND_KM2.sum(),
        ty_le_rung_gop_pct=(fo.forest_frac * fo.LAND_KM2).sum() / fo.LAND_KM2.sum() * 100 if len(fo) else float("nan"),
        pct_iucn_not_reported=nr(fo.IUCN_CAT),
        n_thieu_forty=int((gov.forty_cov.fillna(0) < 0.9).sum()),
    )


def main(isos):
    gee.init("ee-hoangvietanh")
    rows = []
    for iso in isos:
        if not (OUT / f"{iso}.csv").exists():
            print(f"{iso}: đang tính …", flush=True)
        site = screen.load(iso, OUT)
        rows.append(dict(ISO3=iso, country=COUNTRIES.get(iso, iso), **summarize(site)))
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(ROOT / "outputs" / "sang_loc_nuoc.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main(sys.argv[1:] or list(COUNTRIES))
