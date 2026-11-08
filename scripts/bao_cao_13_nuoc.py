"""Báo cáo HTML so sánh 13 nước, từ kết quả của scripts/chay_13_nuoc.py (khu_<ISO3>.csv + cache areas/transitions).

Ra:
  outputs/bao_cao_FCI_13_nuoc.html   một file, ảnh nhúng base64 (gửi/mở ở bất cứ đâu)
  docs/13-nuoc/index.html + img/      cho GitHub Pages (ảnh riêng, 256 màu)
  outputs/so_sanh_13/*.csv            bảng chỉ tiêu tính lại (thêm KTC của FCI trung vị)
Bản đồ tổng quan mỗi nước lấy từ GEE (cần đăng nhập); các hình khác vẽ từ số liệu.
Chạy: PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/bao_cao_13_nuoc.py
"""
import json
import sys
from pathlib import Path

import ee
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from chay_13_nuoc import N_POINTS, POINT_MIN_KM2, PROJECT, YEARS  # noqa: E402
from fortypa import charts, compare, compare13_report, gee, index, screen  # noqa: E402

OUT = ROOT / "outputs"
RES = OUT / "so_sanh_13"
FIG = RES / "hinh"


def load_cache(sub, key, site_ids, cols):
    rows = []
    for s in site_ids:
        rows += json.loads((OUT / sub / f"{s}_{key}.json").read_text(encoding="utf-8"))
    return pd.DataFrame(rows).reindex(columns=cols)


def _latin(s):
    """True when every letter is Latin (Vietnamese diacritics included), i.e. readable without a Khmer, Thai, Lao
    or Cyrillic font."""
    return all(ord(ch) < 0x250 or 0x1E00 <= ord(ch) <= 0x1EFF for ch in str(s) if ch.isalpha())


def readable_names(pas):
    """WDPA NAME is the local-language name; where it is not in Latin script, WDPA's NAME_ENG is used instead."""
    eng = {}
    for iso, d in pas.groupby("ISO3"):
        if d.NAME.map(_latin).all():
            continue
        rows = (screen.base(iso).filter(ee.Filter.inList("SITE_ID", [int(s) for s in d.SITE_ID]))
                .reduceColumns(ee.Reducer.toList(2), ["SITE_ID", "NAME_ENG"]).get("list").getInfo())
        eng.update({int(s): n for s, n in rows if n})
    return [n if _latin(n) or s not in eng else eng[s] for s, n in zip(pas.SITE_ID, pas.NAME)]


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    pas = pd.concat([pd.read_csv(RES / f"khu_{i}.csv", encoding="utf-8-sig") for i in compare.COUNTRIES.ISO3],
                    ignore_index=True)
    pas = pas[pas.OK].reset_index(drop=True)
    gee.init(PROJECT)
    pas["NAME"] = readable_names(pas)
    y0, y1 = YEARS[0], YEARS[-1]
    areas = load_cache("areas", f"{y0}-{y1}", pas.SITE_ID, ["SITE_ID", "year", "value", "area_ha", "scale_m",
                                                            "n_points"])
    trans = load_cache("transitions", f"{y0}to{y1}", pas.SITE_ID, ["SITE_ID", "from", "to", "area_ha", "scale_m",
                                                                   "n_points"])
    trans["change"] = [gee.change_code(a, b) for a, b in zip(trans["from"], trans["to"])]

    fci = index.fci_index(areas, YEARS)
    ind = compare.pa_indicators(pas, areas, fci, trans, YEARS)
    series = compare.country_series(pas, areas, YEARS)
    table = compare.country_table(ind, series, YEARS)
    rank, groups = compare.ranking(table, YEARS)
    tests = compare.pairwise_tests(ind)
    table.to_csv(RES / "so_sanh_nuoc.csv", index=False, encoding="utf-8-sig")
    rank.to_csv(RES / "xep_hang_nuoc.csv", encoding="utf-8-sig")
    tests.to_csv(RES / "kiem_dinh_tung_cap.csv", index=False, encoding="utf-8-sig")
    print("Đã tính lại chỉ tiêu", flush=True)

    ci = {r.ISO3: (r.dfci_ci_lo, r.dfci_ci_hi) for r in table.itertuples()}
    figs = {
        "ci": charts.ci_figure(table, YEARS, FIG / "khoang_tin_cay.png"),
        "strip": charts.state_trend_figure(ind, ci, YEARS, FIG / "trang_thai_xu_huong.png",
                                           min_delta=index.MIN_DELTA, label="Các khu được phân tích"),
        "series": charts.series_grid_figure(series, YEARS, FIG / "FCI_theo_nam.png"),
        "composition": charts.composition_figure(areas, pas, YEARS, FIG / "co_cau_loai_rung.png",
                                                 label="các khu đủ điều kiện (có trọng số)"),
        "pairwise": charts.pairwise_figure(tests, FIG / "kiem_dinh_tung_cap.png"),
    }
    print("Đã vẽ hình so sánh", flush=True)

    names = compare.COUNTRIES.set_index("ISO3").name
    dfci = ind.set_index("SITE_ID").dfci
    overview = {}
    for iso in compare.COUNTRIES.ISO3:
        p_i = pas[pas.ISO3 == iso]
        fc, _ = gee.site_collection(screen.base(iso), p_i.SITE_ID)
        colors = {s: charts.dfci_color(dfci[s]) for s in p_i.SITE_ID if s in dfci.index}
        png = OUT / "thumbs" / f"overview13_{iso}.png"
        extent = gee.overview_thumb(fc, colors, png, dims=1100)
        overview[iso] = charts.overview_figure(names[iso], png, extent, p_i.assign(dfci=p_i.SITE_ID.map(dfci)),
                                               FIG / f"ban_do_dFCI_{iso}.png", labels=False)
        print(f"  bản đồ {iso}", flush=True)

    kw = dict(pas=pas, ind=ind, table=table, rank=rank, groups=groups, tests=tests, years=YEARS, figs=figs,
              overview=overview, n_points=N_POINTS, point_min_km2=POINT_MIN_KM2)
    a = compare13_report.build_report(OUT / "bao_cao_FCI_13_nuoc.html", embed=True, **kw)
    b = compare13_report.build_report(ROOT / "docs" / "13-nuoc" / "index.html", embed=False, **kw)
    print(a, f"{a.stat().st_size / 1e6:.1f} MB")
    print(b, f"{b.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
