"""HTML report of the 13-country comparison (KHUNG_NGHIEN_CUU.md) in three tabs, one article each (summary for the
public, detailed report, data paper), written in markdown under scripts/bai_viet/. Every number an article quotes is a
{{KEY}} filled from facts(); figures and tables are blocks the articles place.

Unlike compare_report (top 30 PAs of 3 countries, a section with maps per PA), countries here are represented by
all their eligible PAs or a stratified sample of them, every country figure is weighted (compare.W), and there are no
per-PA maps."""
import html
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from .charts import fmt_ha
from .compare import CENSUS_MAX, COUNTRIES, REL_MIN_FCI, SAMPLE_N, SIZE_BINS
from .compare_report import EXTRA_CSS, _cls, _dot, _n, _pct, _s
from .gee import CHANGES, CLASSES
from .index import DECLINE, MAX_P, MIN_DELTA, RECOVERY, WEIGHTS
from .report import CSS, _img
from .screen import MIN_BIOME, MIN_FOREST

NOTABLE = 0.25  # |median ΔFCI| from which a country counts as clearly declining (facts tong.n_on_dinh / n_suy_giam)


def _name(iso):
    return COUNTRIES.set_index("ISO3").name[iso]


def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " và " + items[-1]


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
    p = [f"<h3 class='ctry-h' id='nuoc{iso}'>{_dot(iso)}</h3><p class='meta'>{tag} · ΔFCI trung vị {_s(r.dfci_median)} điểm · "
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


def _weights_table():
    lab = CLASSES.set_index("value").label
    rows = "".join(f"<tr><td>{html.escape(lab[v])}</td><td class='n'>{fmt_ha(w, 1)}</td></tr>"
                   for v, w in sorted(WEIGHTS.items(), key=lambda kv: -kv[1]))
    return (f"<div class='scroll'><table style='max-width:420px'><tr><th>Lớp</th><th class='n'>Trọng số w</th></tr>"
            f"{rows}</table></div>")


# Facts: every number the articles quote. Articles write {{KEY}}, never the number itself, so the three tabs agree
# with each other and with the data.

class Fact:
    def __init__(self, v, d=1, signed=False):
        self.v, self.d, self.signed = v, d, signed

    def fmt(self, d=None, absolute=False):
        if isinstance(self.v, str):
            return self.v
        v = abs(self.v) if absolute else self.v
        if v != v:
            raise ValueError("giá trị trống")
        s = fmt_ha(v, self.d if d is None else d).replace("-", "−")
        return "+" + s if self.signed and not absolute and v > 0 else s


def _table_fact(col, v):
    if col in ("n", "N", "n_decline", "n_recovery", "land_km2") or col.startswith("pct_"):
        return Fact(v, 0)
    if "dfci" in col or col == "natural_change_pct":
        return Fact(v, 2, signed=True)
    return Fact(v, 1)


def facts(table, ind, tests, series, trans, areas, pas, years, n_points, point_min_km2):
    """{KEY: Fact}. Per country, KEY = ISO3.name:
    - every numeric column of `table`;
    - dat_khac_pct: non-forest share in the last year (pooled);
    - lop<v>_pct, lop<v>_rung_pct: share of class v in all land / in forest, last year, pooled with W;
    - doi_<code>: share of land in each gee.CHANGES category first → last year, pooled with W;
    - nam_giam_manh: year step with the largest fall of the pooled FCI;
    - nam_giam_khu, n_khu_giam_nam_do: most common year of the largest fall among declining PAs, and how many had it.
    Global: tong.*; country names: ten.ISO3."""
    y0, y1 = years[0], years[-1]
    f = {}
    for r in table.itertuples(index=False):
        d = r._asdict()
        for col, v in d.items():
            if col not in ("ISO3", "country"):
                f[f"{r.ISO3}.{col}"] = _table_fact(col, float(v))
        f[f"{r.ISO3}.dat_khac_pct"] = Fact(100 - d[f"forest_pct_pooled_{y1}"], 0)

    site = pas.set_index("SITE_ID")
    a = areas[areas.year == y1]
    a = a.assign(aw=a.area_ha * a.SITE_ID.map(site.W), ISO3=a.SITE_ID.map(site.ISO3))
    cls = a.pivot_table(index="ISO3", columns="value", values="aw", aggfunc="sum").reindex(columns=range(1, 8)).fillna(0)
    forest = cls.drop(columns=6).sum(axis=1)
    t = trans.assign(aw=trans.area_ha * trans.SITE_ID.map(site.W), ISO3=trans.SITE_ID.map(site.ISO3))
    ch = (t.pivot_table(index="ISO3", columns="change", values="aw", aggfunc="sum")
          .reindex(columns=list(CHANGES.code)).fillna(0))
    steps = series.assign(step=series.groupby("ISO3").fci.diff())
    for iso in table.ISO3:
        for v in range(1, 8):
            f[f"{iso}.lop{v}_pct"] = Fact(100 * cls.loc[iso, v] / cls.loc[iso].sum(), 0)
            if v != 6:
                f[f"{iso}.lop{v}_rung_pct"] = Fact(100 * cls.loc[iso, v] / forest[iso], 0)
        for c in CHANGES.code:
            f[f"{iso}.doi_{c}"] = Fact(100 * ch.loc[iso, c] / ch.loc[iso].sum(), 1)
        s = steps[steps.ISO3 == iso]
        f[f"{iso}.nam_giam_manh"] = Fact(str(int(s.loc[s.step.idxmin(), "year"])))
        dec = ind[(ind.ISO3 == iso) & (ind.verdict == DECLINE)]
        if len(dec):
            mode = dec.drop_year.mode().iloc[0]
            f[f"{iso}.nam_giam_khu"] = Fact(str(int(mode)))
            f[f"{iso}.n_khu_giam_nam_do"] = Fact(int((dec.drop_year == mode).sum()), 0)

    tt = table.set_index("ISO3")
    stable = tt[tt.dfci_median > -NOTABLE]
    vn = _name("VNM")
    vt = tests[(tests.a == vn) | (tests.b == vn)]
    vt = vt.assign(other=[r.b if r.a == vn else r.a for r in vt.itertuples()],
                   vn_minus=[r.diff if r.a == vn else -r.diff for r in vt.itertuples()])
    sig = vt[vt.p < 0.05]
    worse, better = sig[sig.vn_minus < 0], sig[sig.vn_minus > 0]
    ff = tt[f"fci_forest_pooled_{y1}"]
    f.update({
        "tong.n_nuoc": Fact(len(table), 0), "tong.n_khu": Fact(len(ind), 0), "tong.N_khu": Fact(tt.N.sum(), 0),
        "tong.n_nam": Fact(len(years), 0), "tong.nam_dau": Fact(str(y0)), "tong.nam_cuoi": Fact(str(y1)),
        "tong.so_nam": Fact(y1 - y0, 0),
        "tong.n_khu_diem": Fact(int(ind.n_points.notna().sum()), 0), "tong.n_diem": Fact(n_points, 0),
        "tong.nguong_diem_km2": Fact(point_min_km2, 0), "tong.census_max": Fact(CENSUS_MAX, 0),
        "tong.min_forest_pct": Fact(100 * MIN_FOREST, 0), "tong.min_biome_pct": Fact(100 * MIN_BIOME, 0),
        "tong.min_delta": Fact(MIN_DELTA, 0), "tong.max_p": Fact(MAX_P, 2), "tong.rel_min_fci": Fact(REL_MIN_FCI, 0),
        "tong.n_cap": Fact(len(tests), 0), "tong.n_cap_khac_biet": Fact(int((tests.p < 0.05).sum()), 0),
        "tong.on_dinh_dfci_min": Fact(stable.dfci_median.min(), 2, True),
        "tong.on_dinh_dfci_max": Fact(stable.dfci_median.max(), 2, True),
        "tong.on_dinh_giam_min": Fact(stable.pct_negative.min(), 0),
        "tong.on_dinh_giam_max": Fact(stable.pct_negative.max(), 0),
        "tong.on_dinh_suy_giam_max": Fact(stable.pct_decline.max(), 0),
        "tong.n_on_dinh": Fact(len(stable), 0), "tong.n_suy_giam": Fact(len(tt) - len(stable), 0),
        "tong.vn_kem_hon": Fact(_join(worse.other) if len(worse) else "không nước nào"),
        "tong.vn_tot_hon": Fact(_join(better.other) if len(better) else "không nước nào"),
        "tong.vn_chenh_max": Fact(worse.vn_minus.abs().max() if len(worse) else 0.0, 2),
        "tong.lao_mdg_lan": Fact(tt.dfci_median["LAO"] / tt.dfci_median["MDG"], 0),
        "tong.vn_phl_rung": Fact(ff["VNM"] - ff["PHL"], 0),
    })
    for c in COUNTRIES.itertuples():
        f[f"ten.{c.ISO3}"] = Fact(c.name)
    return f


# Articles are a small markdown:
# - '# ' title, '## ' section (one entry in the tab's own navigation), '### ' subheading, '> ' lead paragraph,
#   '- ' list, '| ' table, **bold**, *italic*, `code`, [text](url);
# - numbers: {{KEY}}, {{KEY:d}} (d decimals), {{KEY|abs}};
# - on a paragraph of its own, a block: {{hinh:KEY|caption}}, {{ban_do:ISO3|caption}}, {{bang:KEY}}, {{kpi}},
#   {{cac_nuoc}}.

TABS = {"tom_tat": ("tom-tat", "Bài tóm tắt"), "chi_tiet": ("chi-tiet", "Bài chi tiết"),
        "bai_bao": ("bai-bao", "Bài báo khoa học")}
_TOKEN = re.compile(r"\{\{([^{}]+)\}\}")
_BLOCK = re.compile(r"\{\{(hinh|bang|kpi|ban_do|cac_nuoc)(?::([^|}]+))?(?:\|(.+))?\}\}", re.S)


def _slug(s):
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _value(token, f, where):
    key, _, d = token.partition(":")
    key, _, mod = key.partition("|")
    if key not in f:
        raise KeyError(f"{where}: không có số liệu '{key}'")
    return f[key].fmt(int(d) if d else None, absolute=(mod == "abs"))


def _inline(text, f, where):
    text = html.escape(_TOKEN.sub(lambda m: _value(m.group(1), f, where), text), quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r"<a href='\2'>\1</a>", text)


def render_article(text, tab_id, f, blocks):
    """(html, [(anchor, heading)]) of one article; a missing number or block stops with its name."""
    out, nav = [], []
    for i, block in enumerate(b.strip() for b in text.strip().split("\n\n")):
        where = f"{tab_id}, đoạn {i + 1}"
        if not block:
            continue
        m = _BLOCK.fullmatch(block)
        if m:
            kind, key, cap = m.groups()
            name = kind if key is None else f"{kind}:{key}"
            if name not in blocks:
                raise KeyError(f"{where}: không có khối '{name}'")
            cap = f"<figcaption>{_inline(' '.join(cap.split()), f, where)}</figcaption>" if cap else ""
            out.append(f"<figure class='card'>{blocks[name]}{cap}</figure>" if kind in ("hinh", "ban_do")
                       else blocks[name] + cap)
        elif block.startswith("# "):
            out.append(f"<h2 class='art-title'>{_inline(block[2:], f, where)}</h2>")
        elif block.startswith("## "):
            head = block[3:].strip()
            anchor = f"{tab_id}-{_slug(head)}"
            nav.append((anchor, head))
            out.append(f"<h2 id='{anchor}'>{_inline(head, f, where)}</h2>")
        elif block.startswith("### "):
            out.append(f"<h3 class='sub-h'>{_inline(block[4:], f, where)}</h3>")
        elif block.startswith("> "):
            out.append(f"<p class='lead'>{_inline(' '.join(block[2:].split()), f, where)}</p>")
        elif block.startswith("- "):
            items = re.split(r"\n- ", block[2:])
            out.append("<ul>" + "".join(f"<li>{_inline(' '.join(x.split()), f, where)}</li>" for x in items) + "</ul>")
        elif block.startswith("|"):
            rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in block.splitlines()
                    if not re.fullmatch(r"\|[\s:|-]+\|", ln.strip())]
            head = "".join(f"<th>{_inline(c, f, where)}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{_inline(c, f, where)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f"<div class='scroll'><table><tr>{head}</tr>{body}</table></div>")
        else:
            out.append(f"<p>{_inline(' '.join(block.split()), f, where)}</p>")
    return "".join(out), nav


TAB_CSS = """
.tabs{position:sticky;top:0;z-index:20;background:var(--bg);display:flex;gap:4px;border-bottom:2px solid var(--line);
margin:0 -16px;padding:0 16px;overflow-x:auto;scrollbar-width:thin}
.tabs a{padding:12px 18px 10px;text-decoration:none;color:var(--muted);font-weight:600;font-size:15px;white-space:nowrap;
border-bottom:3px solid transparent;margin-bottom:-2px}
.tabs a.on{color:var(--accent);border-bottom-color:var(--accent)}
nav.subnav{position:sticky;top:46px;z-index:10;background:var(--bg);display:flex;gap:18px;overflow-x:auto;
white-space:nowrap;font-size:14px;padding:9px 0;border-bottom:1px solid var(--line);margin-bottom:8px;
scrollbar-width:thin}
nav.subnav a{text-decoration:none;color:var(--ink)}nav.subnav a:hover{color:var(--accent)}
section.tab h2,section.tab h3{scroll-margin-top:100px}
section.tab>p,section.tab>ul{font-size:16px;line-height:1.7;max-width:760px}
p.lead{font-size:18px!important;line-height:1.6;color:#333}
h2.art-title{font-size:24px;margin:24px 0 8px;line-height:1.3}
h3.sub-h{font-size:17px;margin:22px 0 6px}
h3.ctry-h{font-size:19px;margin:32px 0 6px}
figure{margin:16px 0}figcaption{font-size:13.5px;color:var(--muted);margin-top:6px;line-height:1.5}
"""

TAB_JS = """(function(){var ids=%s;
function show(h){var p=(h||'').replace('#','').split('/'),t=ids.indexOf(p[0])>=0?p[0]:ids[0];
document.querySelectorAll('section.tab').forEach(function(s){s.hidden=s.id!==t});
document.querySelectorAll('.tabs a').forEach(function(a){a.classList.toggle('on',a.getAttribute('data-t')===t)});
var el=p[1]&&document.getElementById(p[1]);if(el)el.scrollIntoView();else window.scrollTo(0,0);}
window.addEventListener('hashchange',function(){show(location.hash)});show(location.hash);})();"""


def build_report(out_path, pas, ind, table, rank, groups, tests, series, trans, areas, years, figs, overview,
                 n_points, point_min_km2, articles, embed=False):
    """Three tabs (TABS), each one article from `articles` {tab key: markdown}, all rendered with the same facts and
    blocks. figs: {"ci", "strip", "pairwise", "series", "composition": png}; overview: {ISO3: png}."""
    out_path = Path(out_path)
    base = out_path.parent
    y0, y1 = years[0], years[-1]
    iso = [c for c in COUNTRIES.ISO3 if c in set(table.ISO3)]
    f = facts(table, ind, tests, series, trans, areas, pas, years, n_points, point_min_km2)
    vn_tests = tests[(tests.a == _name("VNM")) | (tests.b == _name("VNM"))]
    blocks = {f"hinh:{k}": _img(p, embed, base, k) for k, p in figs.items() if p}
    blocks.update({f"ban_do:{c}": _img(p, embed, base, f"Bản đồ ΔFCI các khu của {_name(c)}")
                   for c, p in overview.items() if p})
    blocks.update({
        "kpi": _kpis(table, years),
        "bang:chi_tieu": _country_table(table, years),
        "bang:xep_hang": _rank_table(rank, groups),
        "bang:kiem_dinh_vn": f"<div class='card'>{_tests_table(vn_tests)}<details><summary>Tất cả {len(tests)} cặp "
                             f"nước</summary>{_tests_table(tests)}</details></div>",
        "bang:tang_mau": _strata_table(pas, ind),
        "bang:trong_so_fci": _weights_table(),
        "cac_nuoc": "".join(_country_section(c, ind, table, years, overview, embed, base) for c in iso),
    })
    title = f"Rừng trong khu bảo tồn của 13 nước, {y0}–{y1}"
    tabs, sections = [], []
    for key, (tab_id, label) in TABS.items():
        body, nav = render_article(articles[key], tab_id, f, blocks)
        tabs.append(f"<a href='#{tab_id}' data-t='{tab_id}'>{label}</a>")
        subnav = "".join(f"<a href='#{tab_id}/{a}'>{html.escape(h)}</a>" for a, h in nav)
        sections.append(f"<section class='tab' id='{tab_id}'><nav class='subnav'>{subnav}</nav>{body}</section>")
    page = (f"<!doctype html><html lang='vi'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>"
            f"<style>{CSS}{EXTRA_CSS}{TAB_CSS}</style></head><body><main>"
            f"<h1>{html.escape(title)}</h1>"
            f"<p class='sub'>Forest Typology (ForTy) V2 Beta {y0}–{y1} · WDPA · {len(ind)} khu bảo tồn phân tích, đại "
            f"diện cho {fmt_ha(round(table.N.sum()))} khu quốc gia, trên cạn, có rừng · tạo ngày "
            f"{pd.Timestamp.now():%d/%m/%Y}</p>"
            f"<nav class='tabs'>{''.join(tabs)}</nav>{''.join(sections)}"
            f"<script>{TAB_JS % json.dumps([t for t, _ in TABS.values()])}</script></main></body></html>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return out_path


