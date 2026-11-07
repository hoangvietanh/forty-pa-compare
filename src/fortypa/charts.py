"""Static figures per PA (the 2017 / 2025 class maps side by side, the change map, the line chart of forest class
areas) and the country comparison figures."""
import math
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from .gee import CLASSES, FOREST  # noqa: E402

INK, MUTED, GRID = "#1F1F1F", "#6B6B6B", "#E6E6E3"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})


def fmt_ha(v, d=0):
    """Vietnamese number format: 12.345,6"""
    s = f"{v:,.{d}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def _title(pa):
    return f"{pa.NAME} – {pa.DESIG_ENG}"


def _signed(v, d=2):
    return ("+" if v > 0 else "") + fmt_ha(v, d)


def map_figure(pa, thumbs, years, out_path, fci=None):
    """Two class maps (first and last year) with a shared legend underneath. thumbs: {year: png path};
    fci: {year: FCI} to show each map's FCI and the change between them."""
    imgs = {y: plt.imread(thumbs[y]) for y in years if thumbs.get(y) and Path(thumbs[y]).exists()}
    aspect = max([im.shape[0] / im.shape[1] for im in imgs.values()] or [0.75])  # height / width of the maps
    map_w, top_in, bottom_in = 5.5, 0.9, 0.9  # inches: each map's width, title and legend bands
    fig_h = map_w * aspect + top_in + bottom_in
    fig, axes = plt.subplots(1, len(years), figsize=(map_w * len(years), fig_h))
    for ax, y in zip(axes, years):
        ax.set_axis_off()
        if y in imgs:
            ax.imshow(imgs[y])
        else:
            ax.text(0.5, 0.5, "Không tải được ảnh", ha="center", va="center", color=MUTED, transform=ax.transAxes)
        ax.set_title(f"{y} · FCI {fmt_ha(fci[y], 1)}" if fci else str(y), fontsize=13, fontweight="bold")
    handles = [Patch(facecolor=c.color, edgecolor="#BDBDBD", label=c.label) for c in CLASSES.itertuples()]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)
    delta = f" · ΔFCI {years[0]}→{years[-1]} = {_signed(fci[years[-1]] - fci[years[0]])} điểm" if fci else ""
    fig.suptitle(_title(pa) + delta, fontsize=13)
    fig.subplots_adjust(left=0.01, right=0.99, top=1 - top_in / fig_h, bottom=bottom_in / fig_h, wspace=0.03)
    fig.savefig(out_path, dpi=110, facecolor="white")
    plt.close(fig)
    return out_path


def change_figure(pa, change_png, trans_pa, years, out_path, map_scale=10):
    """Per-pixel ΔFCI map (gee.download_change_maps) with its 11-class legend, and the areas that lost and gained FCI
    from the transitions table."""
    from .gee import DFCI_PIXEL_BINS, UNCHANGED
    from .index import WEIGHTS
    img = plt.imread(change_png)
    aspect = img.shape[0] / img.shape[1]
    map_w, side = 6.5, 4.6
    fig = plt.figure(figsize=(map_w + side, max(map_w * aspect, 4.6) + 0.8))
    x_leg = map_w / (map_w + side)
    ax = fig.add_axes((0.005, 0.02, x_leg, 0.84))
    ax.imshow(img)
    ax.set_axis_off()
    handles = [Patch(facecolor=b.color, edgecolor="#BDBDBD", label=b.label)
               for b in DFCI_PIXEL_BINS.itertuples()][::-1]  # gains on top, losses at the bottom
    handles.append(Patch(facecolor=UNCHANGED, edgecolor="#BDBDBD", label="Không có pixel nào đổi lớp"))
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(x_leg + 0.01, 0.88), frameon=False, fontsize=9,
               title="ΔFCI tại chỗ (điểm)", title_fontsize=9, alignment="left", labelspacing=0.35)
    dw = trans_pa["to"].map(WEIGHTS) - trans_pa["from"].map(WEIGHTS)
    total = trans_pa.area_ha.sum()
    loss, gain = trans_pa.area_ha[dw < 0].sum(), trans_pa.area_ha[dw > 0].sum()
    s = int(trans_pa.scale_m.max()) if len(trans_pa) else 10
    m = int(map_scale or 10)
    pct = (lambda v: fmt_ha(100 * v / total, 1)) if total else (lambda v: "0")
    fig.text(x_leg + 0.015, 0.04,
             f"Giảm FCI: {fmt_ha(loss)} ha ({pct(loss)}%) · tăng FCI: {fmt_ha(gain)} ha ({pct(gain)}%)\n"
             f"(tính ở {s} m). Mỗi điểm ảnh trên bản đồ là trung bình\n"
             f"100 × (trọng số lớp {years[-1]} − trọng số lớp {years[0]}) của các\n"
             f"pixel {m} m bên dưới, tức ΔFCI tại chỗ.", fontsize=8.5, color=MUTED, va="bottom")
    fig.suptitle(f"ΔFCI {years[0]} → {years[-1]} từng điểm ảnh · {_title(pa)}", fontsize=12, x=0.01, ha="left")
    fig.savefig(out_path, dpi=110, facecolor="white")
    plt.close(fig)
    return out_path


def area_table(areas_pa, years):
    """year × forest class (ha), columns in FOREST order; classes absent from the PA are 0."""
    t = (areas_pa[areas_pa.value != 6].pivot_table(index="year", columns="value", values="area_ha", aggfunc="sum")
         .reindex(index=list(years), columns=list(FOREST.value)).fillna(0))
    return t


def _style(ax, years, ylabel):
    ax.set_xlim(years[0] - 0.3, years[-1] + 0.3)
    ax.set_xticks(list(years))
    ax.tick_params(axis="x", labelsize=8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_ha(v)))
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)


def area_chart(pa, areas_pa, years, out_path):
    """Line chart per forest class: area (ha) on the left, change since the first year (ha) on the right.

    Classes differ by orders of magnitude (hundreds of thousands of ha of primary forest next to a few ha of tree
    crops), so on the area panel small classes sit flat on the baseline; the change panel puts every class on the
    same footing, in the same unit, without a second y-axis.
    """
    t = area_table(areas_pa, years)
    keep = [v for v in t.columns if t[v].max() > 0]
    if not keep:  # e.g. a desert park: every pixel is other land in every year
        return None
    meta = FOREST.set_index("value")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8))
    for v in keep:
        kw = dict(color=meta.color[v], linewidth=2, marker="o", markersize=4)
        ax1.plot(t.index, t[v], label=meta.label[v], **kw)
        ax2.plot(t.index, t[v] - t[v].iloc[0], **kw)
    ax1.set_ylim(bottom=0)
    ax2.axhline(0, color=MUTED, linewidth=0.8)
    _style(ax1, years, "Diện tích (ha)")
    _style(ax2, years, "ha")
    ax1.set_title("Diện tích theo loại rừng", fontsize=11, loc="left")
    ax2.set_title(f"Thay đổi so với năm {years[0]}", fontsize=11, loc="left")
    fig.suptitle(f"{_title(pa)} · {years[0]}–{years[-1]}", fontsize=12, x=0.01, ha="left")
    # legend ordered by area in the last year, largest first, so it matches the vertical order of the lines
    order = sorted(keep, key=lambda v: -t[v].iloc[-1])
    h = {lab: hd for hd, lab in zip(*ax1.get_legend_handles_labels())}
    fig.legend([h[meta.label[v]] for v in order], [meta.label[v] for v in order], loc="lower center",
               ncol=min(len(order), 3), frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0.12 if len(order) > 3 else 0.07, 1, 0.95))
    fig.savefig(out_path, dpi=110, facecolor="white")
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------------------------------------------------
# Country comparison

# ΔFCI classes for the overview maps: ColorBrewer RdYlBu 5, red (loss) ↔ blue (gain); ±1 point is the
# threshold of index.MIN_DELTA.
DFCI_BINS = [(-1e9, -1.0, "#D7191C", "≤ −1 (giảm rõ)"), (-1.0, -0.25, "#FDAE61", "−1 đến −0,25"),
             (-0.25, 0.25, "#FFFFBF", "−0,25 đến +0,25"), (0.25, 1.0, "#ABD9E9", "+0,25 đến +1"),
             (1.0, 1e9, "#2C7BB6", "≥ +1 (tăng rõ)")]


def dfci_color(v):
    return next(c for lo, hi, c, _ in DFCI_BINS if lo <= v < hi)


def _countries(df):
    from .compare import COUNTRIES
    return COUNTRIES[COUNTRIES.ISO3.isin(set(df.ISO3))].reset_index(drop=True)


def _strip(ax, ind, col, countries, ci=None):
    """One row per country (first on top): a dot per PA with a little vertical jitter, the median as a bar."""
    rng = np.random.default_rng(1)
    n = len(countries)
    for i, c in enumerate(countries.itertuples()):
        y = n - 1 - i
        v = ind.loc[ind.ISO3 == c.ISO3, col].dropna()
        ax.scatter(v, y + rng.uniform(-0.22, 0.22, len(v)), s=34, color=c.color, alpha=0.85,
                   edgecolor="white", linewidth=0.8, zorder=3)
        m = v.median()
        if ci is not None:
            lo, hi = ci[c.ISO3]
            ax.plot([lo, hi], [y - 0.36, y - 0.36], color=INK, linewidth=2, solid_capstyle="round", zorder=4)
        ax.plot([m, m], [y - 0.3, y + 0.3], color=INK, linewidth=2.5, solid_capstyle="round", zorder=4)
        ax.text(m, y + 0.36, f"trung vị {fmt_ha(m, 2 if abs(m) < 10 else 1)}", ha="center", va="bottom",
                fontsize=8.5, color=INK)
    ax.set_yticks(range(n))
    ax.set_yticklabels(list(countries.name)[::-1], fontsize=11, color=INK)
    ax.set_ylim(-0.7, n - 0.3)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_ha(v, 0 if abs(v) >= 1 or v == 0 else 1)))


def state_trend_figure(ind, ci, years, out_path, min_delta=1.0):
    """Left: FCI of the last year per PA (state). Right: ΔFCI per PA (trend), with the median, its bootstrap interval
    and the ±min_delta band inside which a change is not called a decline or recovery."""
    y0, y1 = years[0], years[-1]
    countries = _countries(ind)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    _strip(a1, ind, f"fci_{y1}", countries)
    a1.set_xlim(0, 100)
    a1.set_title(f"Trạng thái: FCI {y1} của từng khu (0–100)", fontsize=11, loc="left")
    a2.axvspan(-min_delta, min_delta, color="#F1F1EE", zorder=0)
    a2.axvline(0, color=MUTED, linewidth=0.8, zorder=1)
    _strip(a2, ind, "dfci", countries, ci)
    a2.set_title(f"Xu hướng: ΔFCI {y0}→{y1} của từng khu (điểm)", fontsize=11, loc="left")
    fig.text(0.01, 0.01, "Mỗi chấm là một khu bảo tồn. Vạch đứng = trung vị; vạch ngang dưới = khoảng tin cậy 95% "
             f"của trung vị (bootstrap). Dải xám: |ΔFCI| < {fmt_ha(min_delta, 0)} điểm.", fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(out_path, dpi=110, facecolor="white")
    plt.close(fig)
    return out_path


def _end_labels(ax, x, ys, labels, colors):
    """Direct labels at the right end of lines, nudged apart so they do not overlap."""
    lo, hi = ax.get_ylim()
    gap = (hi - lo) * 0.07
    placed = None
    for i in sorted(range(len(ys)), key=lambda i: ys[i]):
        y = ys[i] if placed is None else max(ys[i], placed + gap)
        placed = y
        ax.text(x + 0.25, y, labels[i], fontsize=9.5, color=INK, va="center")
        ax.plot([x], [ys[i]], "o", color=colors[i], markersize=6, zorder=4)


def series_figure(series, years, out_path):
    """Left: pooled FCI per country and year. Right: the same minus the first year, on a common zero."""
    countries = _countries(series)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.6))
    for ax, col, title, ylab in ((a1, "fci", "FCI gộp của 20 khu mỗi nước", "FCI"),
                                 (a2, "dfci_pooled", f"Thay đổi FCI gộp so với {years[0]}", "điểm FCI")):
        for c in countries.itertuples():
            s = series[series.ISO3 == c.ISO3].set_index("year")[col].reindex(years)
            ax.plot(years, s, color=c.color, linewidth=2, marker="o", markersize=4, label=c.name)
        if col == "dfci_pooled":
            ax.axhline(0, color=MUTED, linewidth=0.8)
        else:
            ax.set_ylim(0, 100)
        _style(ax, years, ylab)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _, col=col: fmt_ha(v, 0 if col == "fci" else 2)))
        ax.set_xlim(years[0] - 0.3, years[-1] + 1.4)
        ax.set_title(title, fontsize=11, loc="left")
        last = [series[(series.ISO3 == c.ISO3) & (series.year == years[-1])][col].iloc[0]
                for c in countries.itertuples()]
        _end_labels(ax, years[-1], last, list(countries.name), list(countries.color))
    h, l = a1.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=len(l), frameon=False, fontsize=9.5)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(out_path, dpi=110, facecolor="white")
    plt.close(fig)
    return out_path


def composition_figure(areas, pas, years, out_path):
    """Share of each ForTy class in the pooled area of each country's PAs, first and last year, as stacked bars."""
    countries = _countries(pas)
    t = (areas[areas.year.isin([years[0], years[-1]])].merge(pas[["SITE_ID", "ISO3"]], on="SITE_ID")
         .pivot_table(index=["ISO3", "year"], columns="value", values="area_ha", aggfunc="sum").fillna(0))
    t = 100 * t.div(t.sum(axis=1), axis=0)
    rows = [(c, y) for c in countries.itertuples() for y in (years[0], years[-1])]
    fig, ax = plt.subplots(figsize=(13, 0.5 * len(rows) + 1.9))
    for i, (c, y) in enumerate(rows):
        yy = -(i + (i // 2) * 0.4)
        left = 0
        for k in CLASSES.itertuples():
            w = t.loc[(c.ISO3, y)].get(k.value, 0)
            if w <= 0:
                continue
            ax.barh(yy, w, left=left, height=0.7, color=k.color, edgecolor="white", linewidth=1.5)
            if w >= 6:
                ax.text(left + w / 2, yy, fmt_ha(w, 0) + "%", ha="center", va="center", fontsize=8,
                        color="white" if k.value in (1, 7, 3) else INK)
            left += w
        ax.text(-1, yy, f"{c.name} {y}", ha="right", va="center", fontsize=10, color=INK)
    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    handles = [Patch(facecolor=k.color, edgecolor="#BDBDBD", label=k.label) for k in CLASSES.itertuples()]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)
    ax.set_title("Cơ cấu loại rừng và sử dụng đất trong 20 khu của mỗi nước (% diện tích phân tích)", fontsize=11,
                 loc="left")
    fig.subplots_adjust(left=0.12, right=0.97, top=0.9, bottom=0.27)
    fig.savefig(out_path, dpi=110, facecolor="white")
    plt.close(fig)
    return out_path


def overview_figure(country, png, extent, pas, out_path):
    """Country overview map (from gee.overview_thumb) with each PA's rank number next to its centroid and the ΔFCI
    legend. extent: (x0, y0, x1, y1) of the image in EPSG:3857 metres."""
    img = plt.imread(png)
    x0, y0, x1, y1 = extent
    h, w = img.shape[:2]
    map_w, map_h, legend_h = 11, 11 * h / w, 1.1
    fig = plt.figure(figsize=(map_w, map_h + legend_h + 0.5))
    H = map_h + legend_h + 0.5
    ax = fig.add_axes((0, legend_h / H, 1, map_h / H))
    ax.imshow(img, extent=(x0, x1, y0, y1))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_axis_off()
    R = 6378137.0
    placed = []  # label boxes in points from the axes origin, to keep labels apart
    to_pt = ax.transData + fig.dpi_scale_trans.inverted()
    for pa in pas.sort_values("LAT", ascending=False).itertuples():
        x = R * math.radians(pa.LON)
        y = R * math.log(math.tan(math.pi / 4 + math.radians(pa.LAT) / 2))
        px, py = (v * 72 for v in to_pt.transform((x, y)))
        dx, dy, w, h = 5, 5, 8 + 6 * len(str(pa.RANK)), 13
        while any(abs(px + dx - qx) < (w + qw) / 2 + 1 and abs(py + dy - qy) < h + 1 for qx, qy, qw in placed):
            dy -= h + 1
        placed.append((px + dx, py + dy, w))
        ax.annotate(str(pa.RANK), (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=8.5,
                    fontweight="bold", color=INK, arrowprops=dict(arrowstyle="-", color="#6B6B6B", lw=0.6)
                    if dy < -5 else None,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#9A9A9A", lw=0.6, alpha=0.9))
    handles = [Patch(facecolor=c, edgecolor="#333333", label=lab) for _, _, c, lab in DFCI_BINS]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=9, title="ΔFCI (điểm)",
               title_fontsize=9)
    fig.suptitle(f"{country}: 20 khu bảo tồn lớn nhất tô màu theo ΔFCI · số = thứ hạng diện tích", fontsize=12,
                 x=0.01, y=1 - 0.12 / H, ha="left", va="top")
    fig.savefig(out_path, dpi=110, facecolor="white")
    plt.close(fig)
    return out_path
