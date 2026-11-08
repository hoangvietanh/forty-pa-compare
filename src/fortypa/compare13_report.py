"""HTML report of the 13-country comparison (KHUNG_NGHIEN_CUU.md): key findings, comparison figures and tables,
overview maps, method, then per country its most declining PAs and the full table of analysed PAs.

Unlike compare_report (top 30 PAs of 3 countries, a section with maps per PA), countries here are represented by
all their eligible PAs or a stratified sample of them, every country figure is weighted (compare.W), and there are no
per-PA maps."""
import html
from pathlib import Path

import pandas as pd

from .charts import fmt_ha
from .compare import CENSUS_MAX, COUNTRIES, REL_MIN_FCI, SAMPLE_N, SIZE_BINS
from .compare_report import EXTRA_CSS, _cls, _dot, _n, _pct, _s
from .gee import CLASSES
from .index import DECLINE, MAX_P, MIN_DELTA, RECOVERY, WEIGHTS
from .report import CSS, _img
from .screen import MIN_BIOME, MIN_FOREST

NOTABLE = 0.25  # |median ΔFCI| from which a country's trend is called out in the findings


def _name(iso):
    return COUNTRIES.set_index("ISO3").name[iso]


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " và " + items[-1]


def _findings(table, tests, years):
    y0, y1 = years[0], years[-1]
    t = table.set_index("ISO3")
    fm = t[f"fci_median_{y1}"].sort_values(ascending=False)
    ff = t[f"fci_forest_pooled_{y1}"].sort_values(ascending=False)
    lines = [
        f"<b>Trạng thái {y1}.</b> FCI trung vị các khu cao nhất ở {_join(f'{html.escape(_name(i))} ({_n(v)})' for i, v in fm.head(3).items())}, "
        f"thấp nhất ở {_join(f'{html.escape(_name(i))} ({_n(v)})' for i, v in fm.tail(3).items())}. "
        f"Tính riêng phần có rừng, rừng tự nhiên nhất ở {_join(f'{html.escape(_name(i))} ({_n(v)})' for i, v in ff.head(3).items())}, "
        f"kém tự nhiên nhất ở {_join(f'{html.escape(_name(i))} ({_n(v)})' for i, v in ff.tail(3).items())}, nơi rừng tái sinh, "
        "rừng trồng hoặc cây công nghiệp chiếm phần đáng kể. FCI chung phụ thuộc nhiều vào tỷ lệ đất không phải rừng trong "
        "khu, nên phản ánh sinh cảnh nhiều hơn hiệu quả bảo vệ."]
    bad = t[t.dfci_median <= -NOTABLE].sort_values("dfci_median")
    rest = t[t.dfci_median > -NOTABLE]
    if len(bad):
        lines.append(
            f"<b>Suy giảm rõ {y0}→{y1}.</b> "
            + "; ".join(f"{html.escape(_name(i))}: ΔFCI trung vị {_s(r.dfci_median)} điểm (KTC 95% {_s(r.dfci_ci_lo)} "
                        f"đến {_s(r.dfci_ci_hi)}), {_n(r.pct_negative, 0)}% số khu giảm, {r.n_decline}/{r.n} khu suy "
                        f"giảm rõ, rừng tự nhiên thay đổi ròng {_pct(r.natural_change_pct, 1)}"
                        for i, r in bad.iterrows()) + ".")
    if len(rest):
        lines.append(
            f"<b>Các nước còn lại gần như ổn định:</b> ΔFCI trung vị từ {_s(rest.dfci_median.min())} đến "
            f"{_s(rest.dfci_median.max())} điểm ({_join(html.escape(_name(i)) for i in rest.index)}). Phần lớn khu vẫn có "
            f"ΔFCI âm (tỷ lệ khu giảm {_n(rest.pct_negative.min(), 0)}–{_n(rest.pct_negative.max(), 0)}%), nhưng mức giảm "
            f"chỉ vài phần trăm điểm, nhỏ hơn nhiều so với sai số có thể có của dữ liệu.")
    if "VNM" in t.index:
        v = t.loc["VNM"]
        vt = tests[(tests.a == _name("VNM")) | (tests.b == _name("VNM"))]
        vt = vt.assign(other=[r.b if r.a == _name("VNM") else r.a for r in vt.itertuples()],
                       vn_minus=[r.diff if r.a == _name("VNM") else -r.diff for r in vt.itertuples()])
        sig = vt[vt.p < 0.05]
        worse, better = list(sig[sig.vn_minus < 0].other), list(sig[sig.vn_minus > 0].other)
        gap = sig[sig.vn_minus < 0].vn_minus.abs().max() if worse else 0
        lines.append(
            f"<b>Việt Nam</b> ({v.n} khu, điều tra toàn bộ): FCI {y1} trung vị {_n(v[f'fci_median_{y1}'])}, FCI phần có rừng "
            f"{_n(v[f'fci_forest_pooled_{y1}'])}, ΔFCI trung vị {_s(v.dfci_median)} điểm (KTC 95% {_s(v.dfci_ci_lo)} đến "
            f"{_s(v.dfci_ci_hi)}). Về ΔFCI, Việt Nam tốt hơn có ý nghĩa thống kê so với "
            f"{_join(html.escape(x) for x in better) if better else 'không nước nào'}, và kém hơn so với "
            f"{_join(html.escape(x) for x in worse) if worse else 'không nước nào'}"
            + (f"; chênh lệch với nhóm sau lớn nhất chỉ {fmt_ha(gap, 2)} điểm FCI." if worse else "."))
    lines.append("Trung vị có trọng số cho mỗi khu một phiếu và ổn định với cách rút mẫu. Các chỉ tiêu <b>gộp</b> theo "
                 "diện tích (ΔFCI gộp, thay đổi ròng rừng tự nhiên) ở các nước rút mẫu do một vài khu rất lớn quyết định, "
                 "vì tầng khu ≥ 1.000 km² chỉ có vài khu trong mẫu; nên đọc chúng thận trọng.")
    return "<ul>" + "".join(f"<li>{x}</li>" for x in lines) + "</ul>"


def _kpis(table, years):
    y1 = years[-1]
    cards = []
    for r in table.itertuples():
        d = r._asdict()
        tag = "toàn bộ" if r.n == round(r.N) else f"mẫu {r.n}/{fmt_ha(r.N)}"
        cards.append(
            f"<div class='kpi'><div class='k'>{_dot(r.ISO3)} · {tag} khu</div>"
            f"<div class='v'>FCI {_n(d[f'fci_median_{y1}'])} <span class='{_cls(r.dfci_median)}' "
            f"style='font-size:16px'>({_s(r.dfci_median)})</span></div>"
            f"<div class='d'>trung vị FCI {y1} (ΔFCI trung vị) · {_n(r.pct_negative, 0)}% khu giảm</div></div>")
    return "<div class='kpis'>" + "".join(cards) + "</div>"


def _country_table(table, years):
    y0, y1 = years[0], years[-1]
    rows = [
        ("Khu phân tích / khu đủ điều kiện", lambda r: f"{r.n} / {fmt_ha(r.N)}"),
        ("Diện tích đất các khu đủ điều kiện (km², ước tính)", lambda r: fmt_ha(r.land_km2)),
        (f"Tỷ lệ rừng &amp; cây {y1} (gộp)", lambda r: _n(r[f"forest_pct_pooled_{y1}"]) + "%"),
        (f"FCI {y1} trung vị (KTC 95%)", lambda r: f"{_n(r[f'fci_median_{y1}'])} ({_n(r[f'fci_median_{y1}_lo'])}–"
                                                   f"{_n(r[f'fci_median_{y1}_hi'])})"),
        (f"FCI phần có rừng {y1} (gộp)", lambda r: _n(r[f"fci_forest_pooled_{y1}"])),
        (f"FCI gộp {y0} → {y1}", lambda r: f"{_n(r[f'fci_pooled_{y0}'], 2)} → {_n(r[f'fci_pooled_{y1}'], 2)}"),
        ("ΔFCI trung vị (KTC 95%)", lambda r: f"<span class='{_cls(r.dfci_median)}'>{_s(r.dfci_median, 3)}</span>"
                                             f" ({_s(r.dfci_ci_lo, 3)} đến {_s(r.dfci_ci_hi, 3)})"),
        ("ΔFCI trung bình", lambda r: _s(r.dfci_mean, 3)),
        ("ΔFCI gộp", lambda r: f"<span class='{_cls(r.dfci_pooled)}'>{_s(r.dfci_pooled, 3)}</span>"),
        (f"ΔFCI so với FCI {y0} (trung vị)", lambda r: _pct(r.dfci_rel_median)),
        ("% khu có ΔFCI âm", lambda r: _n(r.pct_negative, 0) + "%"),
        ("% khu suy giảm rõ (trong mẫu: số khu)", lambda r: f"{_n(r.pct_decline, 1)}% ({r.n_decline})"),
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
    head += ("<th class='n'>Điểm trạng thái</th><th class='n'>Hạng trạng thái</th><th class='n'>Điểm xu hướng</th>"
             "<th class='n'>Điểm chung</th><th class='n'>Hạng</th>")
    body = ""
    for c, r in rank.iterrows():
        body += (f"<tr><td>{html.escape(c)}</td>" + "".join(
            f"<td class='n{' best' if r[k] == 1 else ''}'>{int(r[k])}</td>" for k in cols)
                 + f"<td class='n'>{_n(r['Điểm trạng thái'])}</td><td class='n'>{int(r['Hạng trạng thái'])}</td>"
                 + f"<td class='n'>{fmt_ha(r['Điểm xu hướng'], 2)}</td><td class='n'>{fmt_ha(r['Điểm chung'], 2)}</td>"
                 + f"<td class='n'><b>{int(r['Hạng chung'])}</b></td></tr>")
    return f"<div class='card scroll'><table><tr><th>Nước</th>{head}</tr>{body}</table></div>"


def _tests_table(tests):
    body = "".join(f"<tr><td>{html.escape(r.a)} – {html.escape(r.b)}</td><td class='n'>{_s(r.median_a, 3)}</td>"
                   f"<td class='n'>{_s(r.median_b, 3)}</td><td class='n'>{_s(r['diff'], 3)}</td>"
                   f"<td class='n'>{_s(r.ci_lo, 3)} đến {_s(r.ci_hi, 3)}</td>"
                   f"<td class='n{' best' if r.p < 0.05 else ''}'>{fmt_ha(r.p, 3)}</td></tr>"
                   for _, r in tests.iterrows())
    return (f"<div class='scroll'><table><tr><th>Cặp nước (A – B)</th><th class='n'>ΔFCI trung vị A</th>"
            f"<th class='n'>ΔFCI trung vị B</th><th class='n'>Chênh A − B</th><th class='n'>KTC 95% của chênh</th>"
            f"<th class='n'>p</th></tr>{body}</table></div>")


def _strata_table(pas, ind):
    labels = [f"{fmt_ha(a, 0)}–{fmt_ha(b, 0)} km²" if b != float("inf") else f"≥ {fmt_ha(a, 0)} km²"
              for a, b in zip(SIZE_BINS[:-1], SIZE_BINS[1:])]
    head = "".join(f"<th class='n'>{x}</th>" for x in labels)
    body = ""
    for c in COUNTRIES.itertuples():
        d = pas[pas.ISO3 == c.ISO3]
        if d.empty:
            continue
        g = d.groupby("STRATUM").agg(N=("N_H", "first"), n=("N_DRAWN", "first"))
        cells = "".join(f"<td class='n'>{int(g.n[h])} / {fmt_ha(int(g.N[h]))}</td>" if h in g.index
                        else "<td class='n'>–</td>" for h in range(len(labels)))
        npts = int(ind[ind.ISO3 == c.ISO3].n_points.notna().sum()) if "n_points" in ind else 0
        body += (f"<tr><td>{_dot(c.ISO3)}</td>{cells}<td class='n'><b>{len(d)} / {fmt_ha(int(round(d.W.sum())))}</b>"
                 f"</td><td class='n'>{npts}</td></tr>")
    return (f"<div class='scroll'><table><tr><th>Nước</th>{head}<th class='n'>Tổng</th>"
            f"<th class='n'>Khu tính bằng mẫu điểm</th></tr>{body}</table></div>")


def _pa_rows(d, years):
    y0, y1 = years[0], years[-1]
    body = ""
    for r in d.itertuples():
        dd = r._asdict()
        cls = "down" if r.verdict == DECLINE else "up" if r.verdict == RECOVERY else ""
        how = f"{int(r.n_points):,} điểm".replace(",", ".") if r.n_points == r.n_points else f"toàn bộ, {int(r.scale_m)} m"
        body += (f"<tr><td>{html.escape(str(r.NAME))}</td><td>{html.escape(str(r.DESIG_ENG))}</td>"
                 f"<td class='n'>{fmt_ha(r.LAND_KM2, 1)}</td><td class='n'>{fmt_ha(r.W, 1)}</td>"
                 f"<td class='n'>{_n(dd[f'fci_{y0}'])}</td><td class='n'>{_n(dd[f'fci_{y1}'])}</td>"
                 f"<td class='n'><span class='{_cls(r.dfci)}'>{_s(r.dfci)}</span></td>"
                 f"<td class='n'>{fmt_ha(r.mk_p, 3)}</td><td><span class='badge {cls}'>{html.escape(r.verdict)}</span></td>"
                 f"<td class='n'>{_n(dd[f'forest_pct_{y1}'], 0)}%</td><td class='n'>{_pct(r.natural_change_pct, 1)}</td>"
                 f"<td class='n'>{how}</td></tr>")
    return (f"<div class='scroll'><table><tr><th>Khu bảo tồn</th><th>Loại</th><th class='n'>Đất (km²)</th>"
            f"<th class='n'>Trọng số W</th><th class='n'>FCI {y0}</th><th class='n'>FCI {y1}</th><th class='n'>ΔFCI</th>"
            f"<th class='n'>p MK</th><th>Kết luận</th><th class='n'>Rừng &amp; cây {y1}</th>"
            f"<th class='n'>Rừng tự nhiên</th><th class='n'>Cách tính</th></tr>{body}</table></div>")


def _country_section(iso, ind, table, years, overview, embed, base):
    d = ind[ind.ISO3 == iso].sort_values("LAND_KM2", ascending=False)
    r = table.set_index("ISO3").loc[iso]
    tag = (f"điều tra toàn bộ {r.n} khu" if r.n == round(r.N)
           else f"mẫu {r.n} khu đại diện cho {fmt_ha(r.N)} khu đủ điều kiện")
    p = [f"<h2 id='nuoc{iso}'>{_dot(iso)}</h2><p class='meta'>{tag} · ΔFCI trung vị {_s(r.dfci_median)} điểm · "
         f"{_n(r.pct_negative, 0)}% khu có ΔFCI âm</p>"]
    if overview.get(iso):
        p.append("<div class='card'>" + _img(overview[iso], embed, base, f"Bản đồ ΔFCI các khu của {_name(iso)}")
                 + "</div>")
    worst = d[d.dfci < 0].sort_values("dfci").head(10)
    if len(worst):
        p.append(f"<div class='card'><h3>{len(worst)} khu có ΔFCI giảm nhiều nhất</h3>{_pa_rows(worst, years)}</div>")
    p.append(f"<details class='card'><summary>Tất cả {len(d)} khu đã phân tích (xếp theo diện tích)</summary>"
             f"{_pa_rows(d, years)}</details>")
    return "".join(p)


def _method(years, pas, ind, n_points, point_min_km2):
    y0, y1 = years[0], years[-1]
    lab = CLASSES.set_index("value").label
    weights = "".join(f"<tr><td>{html.escape(lab[v])}</td><td class='n'>{fmt_ha(w, 1)}</td></tr>"
                      for v, w in sorted(WEIGHTS.items(), key=lambda kv: -kv[1]))
    samp = ", ".join(f"{html.escape(_name(k))} {v}" for k, v in SAMPLE_N.items())
    return f"""<div class='card' id='phuongphap'><h2 style='margin-top:0'>Dữ liệu và phương pháp</h2>
<h3>Chọn nước</h3>
<p>13 nước được chọn theo hai trục khách quan: vùng địa sinh học (Indo-Malaya, Australasia, Neotropic, Afrotropic,
Nearctic, Palearctic) và nhóm thu nhập của Ngân hàng Thế giới, cộng với các láng giềng chung vùng sinh thái với Việt Nam
(Lào, Campuchia, Thái Lan). Trong mỗi ô, nước có nhiều khu bảo tồn có rừng ≥ 100 km² nhất được chọn; Mỹ và Úc được giữ
cố định từ đợt so sánh trước, Gabon và Cameroon đại diện châu Phi rừng ẩm. Chi tiết và các trường hợp lệch quy tắc:
<code>KHUNG_NGHIEN_CUU.md</code>, mục 5.</p>
<h3 style='margin-top:18px'>Tổng thể khu bảo tồn của mỗi nước</h3>
<p>Từ <code>WCMC/WDPA/current/polygons</code>: <code>DESIG_TYPE = National</code>, trạng thái Designated/Inscribed,
bỏ khu thuần biển, phần đất ≥ 1 km²; các bản ghi cùng <code>SITE_ID</code> được gộp thành một khu, bản ghi lặp cùng
<code>SITE_PID</code> chỉ tính một lần. Chỉ giữ khu do nhà nước quản lý hoặc đồng quản lý (<code>GOV_TYPE</code>; bỏ khu
tư nhân, bản địa, cộng đồng). Khu được coi là <b>có rừng</b> khi rừng ForTy {y0} (lớp 1, 2, 3, 4, 7) chiếm ≥
{fmt_ha(100 * MIN_FOREST, 0)}% diện tích <b>và</b> ≥ {fmt_ha(100 * MIN_BIOME, 0)}% diện tích nằm trong biome rừng của
RESOLVE Ecoregions 2017.</p>
<h3 style='margin-top:18px'>Số khu mỗi nước</h3>
<p>Nước có ≤ {CENSUS_MAX} khu đủ điều kiện được điều tra toàn bộ. Nước nhiều khu hơn được rút ngẫu nhiên phân tầng theo
diện tích đất (4 tầng), phân bổ theo tỷ lệ số khu, mỗi tầng ít nhất 2 khu: {samp}. Cỡ mẫu chọn bằng mô phỏng để sai số
95% của chỉ tiêu trung bình theo khu khoảng ±3 điểm. Mỗi khu mang trọng số <b>W = số khu của tầng / số khu rút từ
tầng</b> (W = 1 khi điều tra toàn bộ); mọi chỉ tiêu cấp nước đều tính theo W. Số khu rút / số khu đủ điều kiện:</p>
{_strata_table(pas, ind)}
<h3 style='margin-top:18px'>Diện tích các lớp trong mỗi khu</h3>
<p>Khu có polygon &lt; {fmt_ha(point_min_km2, 0)} km²: đếm toàn bộ pixel ForTy (<code>frequencyHistogram</code>, hệ UTM
của khu, 10 m). Khu lớn hơn: rút ngẫu nhiên {fmt_ha(n_points)} điểm trong polygon, đọc lớp của từng điểm ở 10 m cho cả
{len(years)} năm (cùng bộ điểm), mỗi điểm đại diện cho diện tích khu / {fmt_ha(n_points)}. Sai số FCI của một khu do lấy
mẫu điểm tối đa ±1,4 điểm (95%); thử trên 8 khu Việt Nam 150–1.200 km², FCI {y1} lệch tối đa 0,77 điểm và ΔFCI lệch tối
đa 0,11 điểm so với đếm toàn bộ. Việt Nam dùng kết quả đếm toàn bộ pixel đã có cho cả 116 khu.</p>
<h3 style='margin-top:18px'>Chỉ số FCI</h3>
<p style='text-align:center'>FCI<sub>t</sub> = 100 × Σ<sub>c</sub> w<sub>c</sub>·A<sub>c,t</sub> / Σ<sub>c</sub>
A<sub>c,t</sub> &nbsp;&nbsp;&nbsp; ΔFCI = FCI<sub>{y1}</sub> − FCI<sub>{y0}</sub></p>
<div class='scroll'><table style='max-width:420px'><tr><th>Lớp</th><th class='n'>Trọng số w</th></tr>{weights}</table></div>
<p>Khu được kết luận <b>suy giảm</b> hoặc <b>phục hồi</b> khi |ΔFCI| ≥ {fmt_ha(MIN_DELTA, 0)} điểm và Mann–Kendall trên
chuỗi {len(years)} năm có p &lt; {fmt_ha(MAX_P, 2)}; còn lại là <b>ổn định / không rõ</b>.</p>
<h3 style='margin-top:18px'>So sánh giữa các nước</h3>
<p><b>Trung vị các khu</b> là trung vị có trọng số W (mỗi khu đủ điều kiện một phiếu). <b>Gộp</b> coi mọi khu đủ điều
kiện của một nước là một vùng (diện tích từng lớp × W). ΔFCI so với FCI {y0} chỉ tính cho khu có FCI {y0} ≥
{fmt_ha(REL_MIN_FCI, 0)}. Khoảng tin cậy 95% và kiểm định từng cặp nước dùng <b>bootstrap phân tầng</b> (2.000 lần, rút
lại các khu trong từng tầng, giữ trọng số); p hai phía = 2 × tỷ lệ lần rút mà chênh lệch đổi dấu. Xếp hạng giữ cách làm
của đợt trước: điểm trạng thái = trung bình FCI {y1} trung vị và FCI phần có rừng; điểm xu hướng = trung bình hạng của 4
chỉ tiêu xu hướng; điểm chung = trung bình hạng trạng thái và điểm xu hướng.</p>
<p class='note'><b>Tính bất định:</b> ForTy V2 Beta là dữ liệu thử nghiệm; độ chính xác công bố (90% loại rừng, 95%
rừng/không rừng) là của bản 2020, chưa kiểm định cho chuỗi thời gian hay cho từng nước. Ở hầu hết các nước ΔFCI trung vị
chỉ vài phần trăm điểm, cùng cỡ với nhiễu phân loại giữa các năm. Thứ hạng giữa các nước có ΔFCI chênh nhau dưới
khoảng 0,1 điểm không có ý nghĩa thực tế, dù kiểm định có thể báo khác biệt. Trọng số FCI là giả định. So sánh chưa
điều chỉnh theo sinh cảnh, độ cao, áp lực dân số hay tuổi khu, nên không phải đánh giá hiệu quả quản lý của từng nước.</p>
<p><b>Tài liệu tham khảo</b></p>
<ul>
<li>Neumann, M., Raichuk, A., Potapov, P. et al. Global forest typology at 10-meter resolution for forest and land-use
monitoring. <i>Sci Data</i> 13, 1434 (2026). <a href='https://doi.org/10.1038/s41597-026-08299-5'>https://doi.org/10.1038/s41597-026-08299-5</a></li>
<li>UNEP-WCMC and IUCN ({pd.Timestamp.now().year}). Protected Planet: The World Database on Protected Areas (WDPA).
<a href='https://www.protectedplanet.net'>www.protectedplanet.net</a> (qua Google Earth Engine,
<code>WCMC/WDPA/current/polygons</code>, {pd.Timestamp.now():%m/%Y}).</li>
<li>Dinerstein, E. et al. An ecoregion-based approach to protecting half the terrestrial realm. <i>BioScience</i> 67,
534–545 (2017) (RESOLVE Ecoregions 2017).</li>
</ul></div>"""


def _narrative(text):
    """The written assessment: '## ' lines become headings, blank lines separate paragraphs."""
    out = []
    for block in (b.strip() for b in text.strip().split("\n\n")):
        if block.startswith("## "):
            out.append(f"<h3 style='margin-top:18px'>{html.escape(block[3:])}</h3>")
        elif block:
            out.append(f"<p style='font-size:16px;line-height:1.65;margin:0 0 10px'>{html.escape(' '.join(block.split()))}</p>")
    return "".join(out)


def build_report(out_path, pas, ind, table, rank, groups, tests, years, figs, overview, n_points, point_min_km2,
                 embed=False, narrative=None):
    """figs: {"ci", "strip", "pairwise", "series", "composition": png}; overview: {ISO3: png}; narrative: the written
    assessment (see _narrative), placed after the key findings. Its numbers are written by hand and do not update."""
    out_path = Path(out_path)
    base = out_path.parent
    y0, y1 = years[0], years[-1]
    iso = [c for c in COUNTRIES.ISO3 if c in set(table.ISO3)]
    title = f"Tình trạng rừng (FCI) trong khu bảo tồn của 13 nước, {y0}–{y1}"
    toc = "".join(f"<a href='#{k}'>{v}</a>" for k, v in [("ketluan", "Kết luận"), ("danhgia", "Đánh giá tổng hợp"),
                                                          ("sosanh", "So sánh"), ("phuongphap", "Phương pháp")]
                  if k != "danhgia" or narrative)
    toc += "".join(f"<a href='#nuoc{c}'>{html.escape(_name(c))}</a>" for c in iso)
    vn_tests = tests[(tests.a == _name("VNM")) | (tests.b == _name("VNM"))]
    p = [f"<!doctype html><html lang='vi'><head><meta charset='utf-8'>"
         f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>"
         f"<style>{CSS}{EXTRA_CSS}</style></head><body><main>",
         f"<h1>{html.escape(title)}</h1>",
         f"<p class='sub'>Forest Typology (ForTy) V2 Beta {y0}–{y1} · WDPA · {len(ind)} khu bảo tồn phân tích, đại diện "
         f"cho {fmt_ha(round(table.N.sum()))} khu quốc gia, trên cạn, có rừng · tạo ngày "
         f"{pd.Timestamp.now():%d/%m/%Y %H:%M}</p><nav class='toc'>{toc}</nav>",
         f"<div class='card' id='ketluan'><h2 style='margin-top:0'>Kết luận chính</h2>"
         f"<p class='meta' style='font-size:14px'><b>FCI</b> (chỉ số tình trạng rừng, 0–100) là điểm trung bình của mọi "
         f"pixel trong khu theo mức độ tự nhiên của lớp phủ: 100 khi toàn khu là rừng nguyên sinh trưởng thành, 0 khi "
         f"không có rừng. <b>ΔFCI</b> = FCI {y1} − FCI {y0}: âm là mất hoặc suy thoái rừng. Ô dưới: FCI {y1} trung vị "
         f"các khu (ΔFCI trung vị trong ngoặc).</p>{_kpis(table, years)}{_findings(table, tests, years)}</div>",
         (f"<div class='card' id='danhgia'><h2 style='margin-top:0'>Đánh giá tổng hợp</h2>{_narrative(narrative)}</div>"
          if narrative else ""),
         "<h2 id='sosanh'>So sánh giữa các nước</h2>"]
    for k, alt in (("ci", "Trung vị FCI và ΔFCI kèm khoảng tin cậy của mỗi nước"),
                   ("strip", "FCI và ΔFCI của từng khu theo nước"),
                   ("series", "Thay đổi FCI theo năm của mỗi nước"),
                   ("composition", "Cơ cấu loại rừng của mỗi nước"),
                   ("pairwise", "Chênh lệch ΔFCI giữa từng cặp nước")):
        if figs.get(k):
            p.append("<div class='card'>" + _img(figs[k], embed, base, alt) + "</div>")
    p.append("<h3 style='margin-top:24px'>Bảng chỉ tiêu</h3>" + _country_table(table, years))
    p.append("<h3 style='margin-top:24px'>Việt Nam so với từng nước (ΔFCI trung vị)</h3>"
             f"<div class='card'>{_tests_table(vn_tests)}<details><summary>Tất cả {len(tests)} cặp nước</summary>"
             f"{_tests_table(tests)}</details></div>")
    p.append("<h3 style='margin-top:24px'>Xếp hạng theo từng chỉ tiêu (1 = tốt nhất)</h3>"
             "<p class='meta'>Giữ cách xếp hạng của đợt so sánh 3 nước để đối chiếu. Với 13 nước, điểm xu hướng (trung "
             "bình thứ hạng) phóng đại những chênh lệch rất nhỏ: các nước có ΔFCI từ −0,11 đến −0,01 điểm vẫn bị xếp "
             "cách nhau nhiều bậc. Nên đọc hình khoảng tin cậy ở trên trước bảng này.</p>" + _rank_table(rank, groups))
    p.append(_method(years, pas, ind, n_points, point_min_km2))
    for c in iso:
        p.append(_country_section(c, ind, table, years, overview, embed, base))
    p.append("</main></body></html>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(p), encoding="utf-8")
    return out_path
