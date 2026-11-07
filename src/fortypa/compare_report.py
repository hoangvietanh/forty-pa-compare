"""HTML report comparing countries: key findings and ranking, method, country tables and figures, overview maps,
then one section per country with its PAs."""
import html
from pathlib import Path

import numpy as np
import pandas as pd

from .charts import area_table, fmt_ha
from .compare import COUNTRIES, REL_MIN_FCI
from .gee import CLASSES, FOREST
from .index import DECLINE, MAX_P, MIN_DELTA, RECOVERY, WEIGHTS
from .report import CSS, _fci_html, _img, _transitions_html

EXTRA_CSS = """
nav.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;margin:0 0 8px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:12px 0}
.kpi{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:#fff}
.kpi .k{font-size:13px;color:var(--muted)}.kpi .v{font-size:22px;font-weight:650;margin:2px 0}
.kpi .d{font-size:13px;color:var(--muted)}
.ctry{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:0}
td.best{font-weight:700}
"""


def _s(v, d=2):
    if v is None or v != v:
        return "–"
    return ("+" if v > 0 else "") + fmt_ha(v, d)


def _pct(v, d=2):
    return "–" if v is None or v != v else _s(v, d) + "%"


def _n(v, d=1):
    return "–" if v is None or v != v else fmt_ha(v, d)


def _cls(v):
    return "up" if v > 0 else "down" if v < 0 else ""


def _dot(iso):
    c = COUNTRIES.set_index("ISO3").loc[iso]
    return f"<span class='ctry' style='background:{c.color}'></span>{html.escape(c['name'])}"


def _drops(ind):
    """PAs whose FCI fell by at least MIN_DELTA, with the year step of the largest fall and its share."""
    d = ind[ind.dfci <= -MIN_DELTA].sort_values("dfci")
    if d.empty:
        return ""
    name = COUNTRIES.set_index("ISO3").name
    items = "; ".join(f"{html.escape(r.NAME)} ({html.escape(name[r.ISO3])}, ΔFCI {_s(r.dfci)}, giảm mạnh nhất "
                      f"{int(r.drop_year) - 1}→{int(r.drop_year)}: {fmt_ha(r.drop_share, 0)}% mức giảm)"
                      for r in d.itertuples())
    return (f"Các khu có FCI giảm từ {fmt_ha(MIN_DELTA, 0)} điểm trở lên: {items}. Ở các khu này phần lớn mức giảm "
            "dồn vào một hoặc hai năm, giống một sự kiện xáo trộn (chẳng hạn cháy rừng) hơn là chuyển đổi đất diễn ra "
            "dần dần; cần đối chiếu với dữ liệu cháy và thực địa trước khi kết luận nguyên nhân.")


def _findings(table, rank, tests, years, ind):
    """Key findings, written from the numbers."""
    y0, y1 = years[0], years[-1]
    t = table.set_index("country")
    best = rank.index[0]
    best_state = rank["Điểm trạng thái"].idxmin()
    best_trend = rank["Điểm xu hướng"].idxmin()
    lines = [f"<b>Xếp hạng chung: {' &gt; '.join(html.escape(c) for c in rank.index)}.</b> "
             f"{html.escape(best)} đứng đầu theo điểm chung (trung bình của điểm trạng thái và điểm xu hướng)."]
    lines.append(f"<b>Trạng thái {y1}</b> (mức độ tự nhiên của lớp phủ): tốt nhất là {html.escape(best_state)}, "
                 "FCI trung vị " + ", ".join(f"{html.escape(c)} {_n(t.loc[c, f'fci_median_{y1}'])}"
                                            for c in t.index) +
                 ". Chỉ số này phụ thuộc mạnh vào sinh cảnh: khu sa mạc, đồng cỏ, băng tuyết có FCI thấp dù được "
                 "bảo vệ tốt, nên nó không đo hiệu quả bảo tồn.")
    lines.append(f"<b>Xu hướng {y0}→{y1}:</b> tốt nhất là {html.escape(best_trend)}. ΔFCI trung vị "
                 + ", ".join(f"{html.escape(c)} {_s(t.loc[c, 'dfci_median'])} điểm "
                             f"(KTC 95%: {_s(t.loc[c, 'dfci_ci_lo'])} đến {_s(t.loc[c, 'dfci_ci_hi'])})"
                             for c in t.index) + "; số khu suy giảm rõ (|ΔFCI| ≥ 1 và Mann–Kendall p &lt; 0,05): "
                 + ", ".join(f"{html.escape(c)} {int(t.loc[c, 'n_decline'])}/{int(t.loc[c, 'n'])}"
                             for c in t.index) + ".")
    drops = _drops(ind)
    if drops:
        lines.append(drops)
    sig = tests[tests.p < 0.05]
    if len(sig):
        lines.append("Khác biệt ΔFCI trung vị có ý nghĩa thống kê (kiểm định hoán vị, p &lt; 0,05) giữa: "
                     + "; ".join(f"{html.escape(r.a)} và {html.escape(r.b)} (chênh {_s(r['diff'])} điểm, "
                                 f"p = {fmt_ha(r.p, 3)})" for _, r in sig.iterrows()) + ".")
    else:
        lines.append("Không cặp nước nào khác nhau có ý nghĩa thống kê về ΔFCI trung vị (kiểm định hoán vị, "
                     "p ≥ 0,05): với 20 khu mỗi nước, khác biệt về xu hướng nhỏ hơn mức có thể khẳng định.")
    lines.append("Mọi thay đổi đều nhỏ so với sai số phân loại có thể có của dữ liệu thử nghiệm ForTy V2 Beta, nên "
                 "thứ hạng là kết quả sàng lọc, không phải đánh giá hiệu quả quản lý.")
    return "<ul>" + "".join(f"<li>{x}</li>" for x in lines) + "</ul>"


def _fci_scale(years):
    """One-line reading guide for FCI and ΔFCI, with the weights taken from index.WEIGHTS."""
    y0, y1 = years[0], years[-1]
    pts = lambda v: fmt_ha(100 * WEIGHTS[v], 0)
    return (f"<p class='meta' style='font-size:14px;margin:0 0 4px'><b>FCI</b> (chỉ số tình trạng rừng) cho biết lớp phủ "
            f"trong khu tự nhiên đến đâu, thang 0–100: 100 = toàn khu là rừng nguyên sinh trưởng thành; nguyên sinh đang "
            f"phục hồi tính {pts(7)}, tái sinh tự nhiên {pts(2)}, rừng trồng {pts(3)}, rừng trồng thâm canh {pts(4)}, cây "
            f"công nghiệp {pts(5)}, đất không có rừng 0. FCI của khu là trung bình các mức này theo diện tích. "
            f"<b>ΔFCI</b> = FCI {y1} − FCI {y0} (điểm): âm là mất hoặc suy thoái rừng, dương là phục hồi; "
            f"|ΔFCI| dưới {fmt_ha(MIN_DELTA, 0)} điểm coi như ổn định. Số lớn là FCI {y1} trung vị các khu, số trong "
            f"ngoặc là ΔFCI trung vị.</p>")


def _kpis(table, years):
    y1 = years[-1]
    cards = []
    for r in table.itertuples():
        d = r._asdict()
        cards.append(
            f"<div class='kpi'><div class='k'>{_dot(r.ISO3)} · {r.n} khu · {fmt_ha(r.land_km2 * 100)} ha</div>"
            f"<div class='v'>FCI {_n(d[f'fci_median_{y1}'])} <span class='{_cls(r.dfci_median)}' "
            f"style='font-size:16px'>({_s(r.dfci_median)})</span></div>"
            f"<div class='d'>trung vị FCI {y1} (ΔFCI trung vị) · {r.n_decline} khu suy giảm, {r.n_recovery} khu "
            f"phục hồi</div></div>")
    return "<div class='kpis'>" + "".join(cards) + "</div>"


def _country_table(table, years):
    y0, y1 = years[0], years[-1]
    rows = [
        ("Số khu · tổng diện tích đất (ha)", lambda r: f"{r.n} · {fmt_ha(r.land_km2 * 100)}"),
        (f"Tỷ lệ rừng &amp; cây {y1} (gộp)", lambda r: _n(r[f"forest_pct_pooled_{y1}"]) + "%"),
        (f"FCI gộp {y0} → {y1}", lambda r: f"{_n(r[f'fci_pooled_{y0}'], 2)} → {_n(r[f'fci_pooled_{y1}'], 2)}"),
        ("ΔFCI gộp (điểm)", lambda r: f"<span class='{_cls(r.dfci_pooled)}'>{_s(r.dfci_pooled, 3)}</span>"),
        (f"FCI {y1} trung vị các khu", lambda r: _n(r[f"fci_median_{y1}"])),
        (f"FCI phần có rừng {y1} (gộp)", lambda r: _n(r[f"fci_forest_pooled_{y1}"])),
        ("ΔFCI trung vị (KTC 95%)", lambda r: f"<span class='{_cls(r.dfci_median)}'>{_s(r.dfci_median, 3)}</span>"
                                             f" ({_s(r.dfci_ci_lo, 3)} đến {_s(r.dfci_ci_hi, 3)})"),
        ("ΔFCI trung bình", lambda r: _s(r.dfci_mean, 3)),
        (f"ΔFCI so với FCI {y0} (trung vị)", lambda r: _pct(r.dfci_rel_median)),
        ("% khu có ΔFCI âm", lambda r: _n(r.pct_negative, 0) + "%"),
        ("Suy giảm / phục hồi / ổn định", lambda r: f"{r.n_decline} / {r.n_recovery} / "
                                                   f"{r.n - r.n_decline - r.n_recovery}"),
        ("Thay đổi ròng rừng tự nhiên (gộp)", lambda r: f"<span class='{_cls(r.natural_change_pct)}'>"
                                                       f"{_pct(r.natural_change_pct)}</span>"),
        (f"Diện tích đổi lớp {y0}→{y1} (trung vị)", lambda r: _n(r.changed_pct_median) + "%"),
    ]
    head = "".join(f"<th class='n'>{_dot(r.ISO3)}</th>" for r in table.itertuples())
    body = "".join(f"<tr><td>{lab}</td>" + "".join(f"<td class='n'>{fn(r)}</td>" for _, r in table.iterrows())
                   + "</tr>" for lab, fn in rows)
    return f"<div class='card scroll'><table><tr><th>Chỉ tiêu</th>{head}</tr>{body}</table></div>"


def _rank_table(rank, groups):
    cols = [c for g in groups.values() for c in g]
    head = "".join(f"<th class='n'>{html.escape(c)}</th>" for c in cols)
    head += "".join(f"<th class='n'>Điểm {g.lower()}</th>" for g in groups) + "<th class='n'>Điểm chung</th>" \
            "<th class='n'>Hạng</th>"
    body = ""
    for c, r in rank.iterrows():
        body += (f"<tr><td>{html.escape(c)}</td>" + "".join(
            f"<td class='n{' best' if r[k] == 1 else ''}'>{int(r[k])}</td>" for k in cols)
                 + "".join(f"<td class='n'>{fmt_ha(r[f'Điểm {g.lower()}'], 2)}</td>" for g in groups)
                 + f"<td class='n'>{fmt_ha(r['Điểm chung'], 2)}</td><td class='n'><b>{int(r['Hạng chung'])}</b></td></tr>")
    return f"<div class='card scroll'><table><tr><th>Nước</th>{head}</tr>{body}</table></div>"


def _tests_table(tests):
    body = "".join(f"<tr><td>{html.escape(r.a)} – {html.escape(r.b)}</td><td class='n'>{_s(r.median_a, 3)}</td>"
                   f"<td class='n'>{_s(r.median_b, 3)}</td><td class='n'>{_s(r['diff'], 3)}</td>"
                   f"<td class='n'>{fmt_ha(r.p, 3)}</td></tr>" for _, r in tests.iterrows())
    return (f"<div class='card scroll'><table style='max-width:720px'><tr><th>Cặp nước (A – B)</th>"
            f"<th class='n'>ΔFCI trung vị A</th><th class='n'>ΔFCI trung vị B</th><th class='n'>Chênh A − B</th>"
            f"<th class='n'>p (hoán vị)</th></tr>{body}</table></div>")


def _pa_table(ind, years):
    y0, y1 = years[0], years[-1]
    body = ""
    for r in ind.sort_values("RANK").itertuples():
        d = r._asdict()
        cls = "down" if r.verdict == DECLINE else "up" if r.verdict == RECOVERY else ""
        body += (f"<tr><td>{r.RANK}</td><td><a href='#pa{r.SITE_ID}'>{html.escape(r.NAME)}</a></td>"
                 f"<td>{html.escape(r.DESIG_ENG)}</td><td class='n'>{fmt_ha(r.LAND_KM2 * 100)}</td>"
                 f"<td class='n'>{_n(d[f'fci_{y0}'])}</td><td class='n'>{_n(d[f'fci_{y1}'])}</td>"
                 f"<td class='n'><span class='{_cls(r.dfci)}'>{_s(r.dfci)}</span></td>"
                 f"<td class='n'>{_pct(r.dfci_rel)}</td><td class='n'>{fmt_ha(r.mk_p, 3)}</td>"
                 f"<td><span class='badge {cls}'>{html.escape(r.verdict)}</span></td>"
                 f"<td class='n'>{_n(d[f'forest_pct_{y1}'], 0)}%</td>"
                 f"<td class='n'>{_pct(r.natural_change_pct)}</td><td class='n'>{_n(r.changed_pct)}%</td>"
                 f"<td class='n'>{int(r.scale_m)}</td></tr>")
    return (f"<div class='card scroll'><table><tr><th>#</th><th>Khu bảo tồn</th><th>Loại</th>"
            f"<th class='n'>Diện tích đất (ha)</th><th class='n'>FCI {y0}</th><th class='n'>FCI {y1}</th>"
            f"<th class='n'>ΔFCI</th><th class='n'>ΔFCI/FCI {y0}</th><th class='n'>p MK</th><th>Kết luận</th>"
            f"<th class='n'>Rừng &amp; cây {y1}</th><th class='n'>Rừng tự nhiên</th><th class='n'>Đổi lớp</th>"
            f"<th class='n'>Độ phân giải (m)</th></tr>{body}</table></div>")


def _pa_section(i, pa, areas, years, figures, fci_row, transitions, embed, base):
    y0, y1 = years[0], years[-1]
    meta = FOREST.set_index("value")
    a = areas[areas.SITE_ID == pa.SITE_ID]
    t = area_table(a, years)
    cols = [v for v in t.columns if t[v].sum() > 0]
    thead = "".join(f"<th class='n'><span class='sw' style='background:{meta.color[v]}'></span>"
                    f"{html.escape(meta.label[v])}</th>" for v in cols)
    trows = "".join(f"<tr><td>{y}</td>" + "".join(f"<td class='n'>{fmt_ha(t.loc[y, v])}</td>" for v in cols)
                    + f"<td class='n'><b>{fmt_ha(t.loc[y, cols].sum())}</b></td></tr>" for y in years)
    coarse = a.scale_m.max()
    f = figures.get(pa.SITE_ID, {})
    p = [f"<section class='card' id='pa{pa.SITE_ID}'><h3>{i}. {html.escape(pa.NAME)}</h3>"
         f"<p class='meta'>{html.escape(str(pa.NAME_ENG))} · {html.escape(pa.DESIG_ENG)} · IUCN "
         f"{html.escape(str(pa.IUCN_CAT))} · công nhận {pa.STATUS_YR} · WDPA {pa.SITE_ID}"
         f" · {fmt_ha(pa.LAND_KM2 * 100)} ha đất"
         + (f" · {pa.PARCELS} mảnh gộp lại" if pa.PARCELS > 1 else "")
         + (f" · <span class='note'>diện tích tính ở {coarse} m</span>" if coarse > 10 else "") + "</p>"]
    if fci_row is not None:
        p.append(_fci_html(fci_row, years))
    if f.get("map"):
        p.append(_img(f["map"], embed, base, f"Bản đồ loại rừng {pa.NAME} năm {y0} và {y1}"))
    if f.get("change"):
        p.append(_img(f["change"], embed, base, f"Bản đồ thay đổi loại rừng {pa.NAME} {y0}–{y1}"))
    if transitions is not None:
        p.append(_transitions_html(transitions[transitions.SITE_ID == pa.SITE_ID], years))
    if f.get("chart"):
        p.append(_img(f["chart"], embed, base, f"Biểu đồ diện tích theo loại rừng {pa.NAME} {y0}–{y1}"))
    p.append(f"<details><summary>Bảng số liệu (ha)</summary><div class='scroll'><table><tr><th>Năm</th>{thead}"
             f"<th class='n'>Tổng</th></tr>{trows}</table></div></details></section>")
    return "".join(p)


def _method(cfg, years, n_per_country, same_sign):
    y0, y1 = years[0], years[-1]
    lab = CLASSES.set_index("value").label
    weights = "".join(f"<tr><td>{html.escape(lab[v])}</td><td class='n'>{fmt_ha(w, 1)}</td></tr>"
                      for v, w in sorted(WEIGHTS.items(), key=lambda kv: -kv[1]))
    desig = ", ".join(f"“{html.escape(d)}”" for d in cfg["DESIG_ENG"])
    return f"""<div class='card' id='phuongphap'><h2 style='margin-top:0'>Dữ liệu và phương pháp</h2>
<h3>Dữ liệu</h3>
<p><b>ForTy V2 Beta</b> (<code>projects/nature-trace/assets/forest_typology/v2_beta/&lt;năm&gt;</code>, Google DeepMind,
Google Research, WRI, IIASA): bản đồ loại rừng toàn cầu 10 m theo năm {y0}–{y1}, 7 band xác suất; lớp của mỗi pixel là
band có xác suất cao nhất. Độ chính xác công bố (90% về loại rừng, 95% về rừng/không rừng) là của bản đồ năm 2020; chuỗi
thời gian V2 Beta là bản thử nghiệm, chưa được kiểm định riêng cho biến động theo năm, cũng chưa kiểm định riêng cho Việt
Nam, Mỹ hay Úc.</p>
<p><b>Khu bảo tồn:</b> <code>WCMC/WDPA/current/polygons</code>. Với mỗi nước (ISO3 = VNM, USA, AUS): trạng thái
Designated/Inscribed, bỏ khu thuần biển, và chỉ giữ các khu có
<code>DESIG_ENG</code> thuộc {desig}:</p>
<pre style='background:#f6f6f4;padding:8px 12px;border-radius:6px;overflow-x:auto'>fc = fc.filter(ee.Filter.inList("DESIG_ENG", {list(cfg["DESIG_ENG"])}))</pre>
<p>WDPA lưu một số khu thành nhiều mảnh (cùng <code>SITE_ID</code>); các mảnh được gộp thành một khu. Sau khi lọc, mỗi
nước giữ <b>{n_per_country} khu có diện tích đất liền lớn nhất</b> (<code>GIS_AREA − GIS_M_AREA</code>). Ở Mỹ chỉ có
National Park và Nature Reserve; “Cultural and Historical Site” chỉ có ở Việt Nam. Các khu lớn nhất của Mỹ và Úc nằm nhiều
ở Alaska, sa mạc và vùng khô hạn, còn của Việt Nam là rừng nhiệt đới, nên ba nhóm khu khác nhau rất nhiều về sinh cảnh.</p>
<h3 style='margin-top:18px'>Diện tích và chỉ số FCI của từng khu</h3>
<p>Diện tích từng lớp mỗi năm tính bằng <code>frequencyHistogram</code> trong hệ UTM của khu ở 10 m (1 pixel = 100 m²).
Các khu của Mỹ và Úc lớn gấp 5–30 lần khu của Việt Nam. Để mỗi request nằm trong giới hạn của GEE, khu nào có hơn
{fmt_ha(cfg.get("MAX_PIXELS", 2e7) / 1e6, 0)} triệu pixel ở 10 m được tính ở độ phân giải thô hơn (20, 30 hoặc 60 m; cột
“Độ phân giải” trong bảng từng nước); ở mức này tổng diện tích từng lớp gần như không đổi nhưng các mảng nhỏ hơn
pixel có thể bị gộp vào lớp xung quanh. Bản đồ thay đổi của khu lớn hơn {fmt_ha(cfg.get("CHANGE_BIG_KM2", 3000), 0)} km²
được tính từ pixel 30 m.</p>
<p><b>Bản đồ ΔFCI từng điểm ảnh.</b> Mỗi pixel có ΔFCI = 100 × (trọng số lớp {y1} − trọng số lớp {y0}), từ −100 (rừng
nguyên sinh trưởng thành thành đất khác) đến +100. Mỗi điểm ảnh trên bản đồ là trung bình của các pixel bên dưới, nên
trung bình của cả khu chính là ΔFCI của khu. Màu theo ColorBrewer RdYlBu (đỏ giảm, xanh tăng); điểm ảnh không có pixel
nào đổi lớp tô xám. Bản đồ loại rừng dùng ColorBrewer: rừng tự nhiên màu lục, rừng trồng màu lam, cây công nghiệp màu
cam. Chỉ số tình trạng rừng (FCI) gán mỗi lớp một trọng số theo
mức độ tự nhiên:</p>
<p style='text-align:center'>FCI<sub>t</sub> = 100 × Σ<sub>c</sub> w<sub>c</sub>·A<sub>c,t</sub> / Σ<sub>c</sub>
A<sub>c,t</sub> &nbsp;&nbsp;&nbsp; ΔFCI = FCI<sub>{y1}</sub> − FCI<sub>{y0}</sub></p>
<div class='scroll'><table style='max-width:420px'><tr><th>Lớp</th><th class='n'>Trọng số w</th></tr>{weights}</table></div>
<p>Khu được kết luận <b>suy giảm</b> hoặc <b>phục hồi</b> khi |ΔFCI| ≥ {fmt_ha(MIN_DELTA, 0)} điểm và kiểm định
Mann–Kendall trên chuỗi {len(years)} năm có p &lt; {fmt_ha(MAX_P, 2)}; còn lại là <b>ổn định / không rõ</b>. ΔFCI cùng
dấu với xu hướng Theil–Sen {len(years)} năm ở {fmt_ha(same_sign, 0)}% số khu.</p>
<h3 style='margin-top:18px'>Cách so sánh giữa các nước</h3>
<p>FCI trả lời hai câu hỏi khác nhau, nên được so sánh riêng:</p>
<ul>
<li><b>Trạng thái</b> (FCI {y1}): lớp phủ trong khu tự nhiên đến đâu. Chỉ số này phản ánh sinh cảnh nhiều hơn hiệu quả bảo
vệ: khu sa mạc, đồng cỏ hay băng tuyết có FCI thấp vì phần lớn là “đất khác”. Vì vậy bài dùng thêm <b>FCI phần có rừng</b>
(chỉ tính trên các pixel rừng &amp; cây), cho biết rừng hiện có tự nhiên đến đâu, bất kể khu có bao nhiêu rừng.</li>
<li><b>Xu hướng</b> ({y0}→{y1}): ΔFCI, ΔFCI so với FCI {y0} (%, để khu có FCI thấp không bị thiệt; chỉ tính cho khu
có FCI {y0} ≥ {fmt_ha(REL_MIN_FCI, 0)}, vì ở khu sa mạc FCI gần 0 nên vài phần trăm điểm thay đổi đã thành hàng chục %),
tỷ lệ khu có ΔFCI âm và thay đổi ròng của diện tích rừng tự nhiên. Đây là phần quản lý bảo tồn có thể tác động.</li>
</ul>
<p>Mỗi chỉ tiêu được tính theo hai cách: <b>gộp</b> (coi 20 khu của một nước là một vùng, nên khu lớn có trọng số lớn) và
<b>trung vị các khu</b> (mỗi khu một phiếu, ít bị một khu rất lớn chi phối). Khoảng tin cậy 95% của ΔFCI trung vị tính bằng
bootstrap (10.000 lần lấy mẫu lại); khác biệt giữa hai nước được kiểm định bằng phép hoán vị (20.000 lần) trên ΔFCI trung
vị. <b>Xếp hạng:</b> mỗi nước được xếp hạng 1–3 theo từng chỉ tiêu (1 = tốt nhất); điểm trạng thái và điểm xu hướng là
trung bình thứ hạng trong nhóm; điểm chung là trung bình của hai điểm này, để bốn chỉ tiêu xu hướng không lấn át hai chỉ
tiêu trạng thái. Điểm càng thấp càng tốt.</p>
<p class='note'><b>Tính bất định:</b> ForTy V2 Beta là dữ liệu thử nghiệm; thứ tự band và định nghĩa lớp có thể đổi. Độ
chính xác 90%/95% là của bản 2020, chưa kiểm định cho chuỗi thời gian hay cho từng nước. ΔFCI của phần lớn các khu nhỏ
hơn 1 điểm, tức là cùng cỡ với nhiễu phân loại giữa các năm. Trọng số FCI là giả định; thứ hạng và chiều thay đổi đáng
tin hơn giá trị tuyệt đối. Mỗi nước chỉ có 20 khu lớn nhất, không đại diện cho toàn bộ hệ thống khu bảo tồn. Ba nhóm khu
khác nhau về sinh cảnh, quy mô và áp lực sử dụng đất, nên so sánh không phải là đánh giá hiệu quả quản lý của mỗi nước.</p>
<p><b>Tài liệu tham khảo</b></p>
<ul>
<li>Neumann, M., Raichuk, A., Potapov, P. et al. Global forest typology at 10-meter resolution for forest and land-use
monitoring. <i>Sci Data</i> 13, 1434 (2026). <a href='https://doi.org/10.1038/s41597-026-08299-5'>https://doi.org/10.1038/s41597-026-08299-5</a></li>
<li>Google DeepMind. Beyond tree cover: mapping the world’s forest types.
<a href='https://deepmind.google/blog/beyond-tree-cover-mapping-the-worlds-forest-types/'>https://deepmind.google/blog/beyond-tree-cover-mapping-the-worlds-forest-types/</a></li>
<li>UNEP-WCMC and IUCN ({pd.Timestamp.now().year}). Protected Planet: The World Database on Protected Areas (WDPA).
<a href='https://www.protectedplanet.net'>www.protectedplanet.net</a> (qua Google Earth Engine,
<code>WCMC/WDPA/current/polygons</code>, {pd.Timestamp.now():%m/%Y}).</li>
</ul></div>"""


def build_report(out_path, cfg, pas, areas, years, ind, table, rank, groups, tests, figures, country_figs,
                 overview, transitions=None, fci=None, failed=None, embed=False):
    """figures: {SITE_ID: {"map", "change", "chart"}}; country_figs: {"state_trend", "series", "composition"};
    overview: {ISO3: png}."""
    out_path = Path(out_path)
    base = out_path.parent
    y0, y1 = years[0], years[-1]
    title = f"So sánh chỉ số tình trạng rừng (FCI) trong khu bảo tồn Việt Nam, Mỹ và Úc, {y0}–{y1}"
    same_sign = 100 * (np.sign(fci.dfci) == np.sign(fci.trend)).mean() if fci is not None else float("nan")
    iso = [c for c in COUNTRIES.ISO3 if c in set(pas.ISO3)]
    name = COUNTRIES.set_index("ISO3").name
    toc = "".join(f"<a href='#{k}'>{v}</a>" for k, v in [("ketluan", "Kết luận"), ("sosanh", "So sánh"),
                                                          ("bando", "Bản đồ so sánh"), ("phuongphap", "Phương pháp")])
    toc += "".join(f"<a href='#nuoc{c}'>{html.escape(name[c])}</a>" for c in iso)
    p = [f"<!doctype html><html lang='vi'><head><meta charset='utf-8'>"
         f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>"
         f"<style>{CSS}{EXTRA_CSS}</style></head><body><main>",
         f"<h1>{html.escape(title)}</h1>",
         f"<p class='sub'>ForTy V2 Beta {y0}–{y1} · WDPA · {len(pas)} khu bảo tồn ({len(pas) // max(len(iso), 1)} khu lớn "
         f"nhất mỗi nước) · tạo ngày {pd.Timestamp.now():%d/%m/%Y %H:%M}</p><nav class='toc'>{toc}</nav>"]

    p.append(f"<div class='card' id='ketluan'><h2 style='margin-top:0'>Kết luận chính</h2>{_fci_scale(years)}"
             f"{_kpis(table, years)}{_findings(table, rank, tests, years, ind)}</div>")

    p.append(f"<h2 id='sosanh'>So sánh giữa các nước</h2>"
             f"<p class='meta'>“Gộp” = coi 20 khu của một nước là một vùng (khu lớn nặng ký hơn). “Trung vị” = mỗi khu "
             f"một phiếu. KTC = khoảng tin cậy bootstrap.</p>{_country_table(table, years)}")
    p.append("<h3>Xếp hạng theo từng chỉ tiêu (1 = tốt nhất)</h3>" + _rank_table(rank, groups))
    p.append("<h3>Kiểm định khác biệt ΔFCI giữa các nước</h3>" + _tests_table(tests))
    for k, alt in (("state_trend", "Trạng thái và xu hướng FCI từng khu theo nước"),
                   ("series", "FCI gộp theo năm của mỗi nước"),
                   ("composition", "Cơ cấu loại rừng của mỗi nước")):
        if country_figs.get(k):
            p.append("<div class='card'>" + _img(country_figs[k], embed, base, alt) + "</div>")

    p.append("<h2 id='bando'>Bản đồ so sánh</h2><p class='meta'>Mỗi khu tô màu theo ΔFCI "
             f"{y0}→{y1}: đỏ là giảm, xanh là tăng, xám là gần như không đổi. Số bên cạnh là thứ hạng diện tích của khu "
             "trong nước đó (khớp với cột # trong bảng từng nước). Bản đồ loại rừng và bản đồ thay đổi chi tiết của "
             "từng khu nằm ở mục của mỗi nước.</p>")
    for c in iso:
        if overview.get(c):
            p.append("<div class='card'>" + _img(overview[c], embed, base, f"Bản đồ ΔFCI các khu của {name[c]}")
                     + "</div>")

    p.append(_method(cfg, years, len(pas) // max(len(iso), 1), same_sign))

    if failed:
        p.append("<h2>Khu chưa tính được</h2><div class='card'><ul>" + "".join(
            f"<li>{k}: {html.escape(v[-1] if isinstance(v, list) else str(v))}</li>" for k, v in failed.items())
                 + "</ul></div>")

    fci_by_site = fci.set_index("SITE_ID") if fci is not None else None
    for c in iso:
        d = ind[ind.ISO3 == c]
        p.append(f"<h2 id='nuoc{c}'>{_dot(c)}: {len(d)} khu bảo tồn</h2>{_pa_table(d, years)}")
        for pa in pas[pas.ISO3 == c].sort_values("RANK").itertuples():
            if areas[areas.SITE_ID == pa.SITE_ID].empty:
                continue
            row = fci_by_site.loc[pa.SITE_ID] if fci_by_site is not None and pa.SITE_ID in fci_by_site.index else None
            p.append(_pa_section(pa.RANK, pa, areas, years, figures, row, transitions, embed, base))
    p.append("</main></body></html>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(p), encoding="utf-8")
    return out_path
