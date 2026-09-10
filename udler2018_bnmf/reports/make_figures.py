#!/usr/bin/env python3
# Udler 2018 bNMF 재현 검증 — 보고서용 그림 생성
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

# 이 파일은 reports/ 안에 있고, 입력(refs/, results/)은 프로젝트 루트 기준이다.
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(PROJ, "reports", "figures")
os.makedirs(OUT, exist_ok=True)
os.chdir(PROJ)

from matplotlib import font_manager as fm
for _f in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
    try: fm.fontManager.addfont(_f)
    except Exception: pass
_KR = fm.FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc").get_name()
plt.rcParams.update({
    "font.family": _KR,
    "axes.unicode_minus": False,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "axes.edgecolor": "#C9D3D1",
    "axes.linewidth": .8,
    "text.color": "#152025",
    "axes.labelcolor": "#33454C",
    "xtick.color": "#5F7076",
    "ytick.color": "#5F7076",
})

INK, INK2, MUTED = "#152025", "#33454C", "#5F7076"
TEAL = ["#F2F7F6", "#CDE6DF", "#9BD0C3", "#63B0A0", "#2A8B77", "#0A6157"]
SEQ  = LinearSegmentedColormap.from_list("seq", TEAL)
DIV  = LinearSegmentedColormap.from_list(
    "div", ["#8A5E36", "#BE8A64", "#E4D3C4", "#EDF0F0", "#9BD0C3", "#2A8B77", "#0A6157"])

# ---------------------------------------------------------------- load
s4 = pd.read_csv("refs/udler2018_S4_trait_weights.csv")
s4["feat"] = s4.Trait.str.replace("_zscale2", "", regex=False)
s4 = s4.set_index("feat").drop(columns=["Trait"])
UC_H = list(s4.columns)                      # Beta-cell ... Liver/Lipid

s3 = pd.read_csv("refs/udler2018_S3_variant_weights.csv")
s3["lab"] = s3.Loci + " (" + s3.SNP + ")"
s3 = s3.set_index("SNP")
UC_W = [c for c in s3.columns if c not in ("Loci", "lab")]


def load(resdir, k):
    h = pd.read_csv(f"{resdir}/L2EU.H.mat.{k}.txt", sep="\t")
    h.index = [f"K{i+1}" for i in range(len(h))]
    w = pd.read_csv(f"{resdir}/L2EU.W.mat.{k}.txt", sep="\t")
    rs = pd.read_csv(f"{resdir}/rsID_map.txt", sep="\t")
    rs["cp"] = rs.VAR_ID.str.split("_").str[:2].str.join(":")
    w["rsID"] = w.variant.map(dict(zip(rs.cp, rs.rsID)))
    w = w.dropna(subset=["rsID"]).set_index("rsID")
    w = w[[c for c in w.columns if c.startswith("X")]]
    w.columns = [f"K{i+1}" for i in range(w.shape[1])]
    return h, w


V2 = "results/udler2018_eur_v2"
V1 = "results/udler2018_eur_v1"
h5, w5 = load(V2, 5)

featH = [f for f in h5.columns if f in s4.index]          # 62
varW  = [v for v in w5.index  if v in s3.index]           # 75


def corr(mine_T, truth):
    out = pd.DataFrame(index=mine_T.index, columns=truth.columns, dtype=float)
    for i in mine_T.index:
        for c in truth.columns:
            out.loc[i, c] = np.corrcoef(mine_T.loc[i].values.astype(float),
                                        truth[c].values.astype(float))[0, 1]
    return out


CH = corr(h5[featH], s4.loc[featH])
CW = corr(w5.loc[varW].T, s3.loc[varW, UC_W])

# our cluster order aligned to the paper's cluster order
ORDER   = ["K3", "K4", "K2", "K5", "K1"]
ORDLAB  = ["K3", "K4", "K2", "K5", "K1"]
MATCH   = ["Beta-cell (K3)", "Proinsulin (K4)", "Obesity/Lipodys. (K2)",
           "Liver/Lipid (K5)", "매칭 없음 (K1)"]


def norm_cols(df):
    return df / df.max(axis=0).replace(0, np.nan)


def block_order(truth):
    """정답지에서 argmax 클러스터별로 묶고, 그 안에서 가중치 내림차순."""
    dom = truth.idxmax(axis=1)
    mx  = truth.max(axis=1)
    o = []
    for c in truth.columns:
        idx = truth.index[dom == c]
        o += list(mx.loc[idx].sort_values(ascending=False).index)
    o += [i for i in truth.index if i not in o]
    return o


# ================================================================ FIG 2/3
def side_by_side(truth, mine, order_rows, row_labels, fname, title_l, title_r,
                 ylab, figsize, fontsize):
    T = norm_cols(truth.loc[order_rows]).fillna(0).values
    M = norm_cols(mine.loc[order_rows, ORDER]).fillna(0).values
    fig, axes = plt.subplots(1, 2, figsize=figsize,
                             gridspec_kw={"wspace": .06})
    for ax, D, cols, ttl in [(axes[0], T, list(truth.columns), title_l),
                             (axes[1], M, MATCH,              title_r)]:
        ax.imshow(D, cmap=SEQ, aspect="auto", vmin=0, vmax=1,
                  interpolation="nearest")
        ax.set_xticks(range(D.shape[1]))
        ax.set_xticklabels(cols, rotation=38, ha="right", fontsize=fontsize + .5)
        ax.set_title(ttl, fontsize=fontsize + 3, pad=10, color=INK, fontweight="bold")
        ax.set_yticks(range(len(order_rows)))
        for s in ax.spines.values():
            s.set_color("#C9D3D1")
        ax.tick_params(length=0)
        for x in range(1, D.shape[1]):
            ax.axvline(x - .5, color="white", lw=1.1)
    axes[0].set_yticklabels(row_labels, fontsize=fontsize)
    axes[0].set_ylabel(ylab, fontsize=fontsize + 3, color=INK2, labelpad=8)
    axes[1].set_yticklabels([])
    cb = fig.colorbar(plt.cm.ScalarMappable(cmap=SEQ), ax=axes, fraction=.018, pad=.015)
    cb.set_label("가중치 (클러스터별 최대값 = 1로 정규화)", fontsize=fontsize + 1, color=MUTED)
    cb.ax.tick_params(labelsize=fontsize, length=0)
    cb.outline.set_edgecolor("#C9D3D1")
    fig.savefig(f"{OUT}/{fname}", bbox_inches="tight", facecolor="white")
    plt.close(fig)


ordH = block_order(s4.loc[featH])
side_by_side(s4.loc[featH], h5[featH].T, ordH, ordH,
             "fig3_형질가중치_정답지대조.png",
             "정답지 — 논문 S4 형질 가중치", "우리 결과 — H 행렬 (K=5)",
             "형질 feature 62개", (7.0, 11.9), 8.6)

lab_map = dict(zip(s3.index, s3.lab))
ordW = block_order(s3.loc[varW, UC_W])
half = 38
for part, rows_ in [("a", ordW[:half]), ("b", ordW[half:])]:
    n0 = 1 if part == "a" else half + 1
    n1 = half if part == "a" else len(ordW)
    side_by_side(s3.loc[varW, UC_W], w5.loc[varW], rows_, [lab_map[v] for v in rows_],
                 f"fig4{part}_변이가중치_정답지대조_{1 if part == 'a' else 2}of2.png",
                 "정답지 — 논문 S3 변이 가중치", "우리 결과 — W 행렬 (K=5)",
                 f"변이 {n0}–{n1} / 75 (유전자 / rsID)", (7.2, 11.0), 10.0)


# ================================================================ FIG 4  상관행렬
fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.5), gridspec_kw={"wspace": .34})
for ax, C, cols, ttl, sub in [
        (axes[0], CH.loc[ORDER], UC_H, "형질축  H vs S4", "공유 형질 feature 62개"),
        (axes[1], CW.loc[ORDER], UC_W, "변이축  W vs S3", "공유 변이 75개")]:
    D = C.values.astype(float)
    ax.imshow(D, cmap=DIV, vmin=-1, vmax=1, aspect="auto", interpolation="nearest")
    ax.set_xticks(range(5)); ax.set_xticklabels(cols, rotation=32, ha="right", fontsize=9)
    ax.set_yticks(range(5)); ax.set_yticklabels(ORDLAB, fontsize=9.5)
    ax.set_title(ttl, fontsize=11.5, fontweight="bold", pad=22, color=INK)
    ax.text(.5, 1.045, sub, transform=ax.transAxes, ha="center", fontsize=8.5, color=MUTED)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_color("#C9D3D1")
    for i in range(5):
        for j in range(5):
            v = D[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8.8,
                    color="white" if abs(v) > .55 else INK2,
                    fontweight="bold" if abs(v) > .55 else "normal")
    for i in range(5):
        for j in range(5):
            if abs(D[i, j]) > .55:
                ax.add_patch(Rectangle((j - .5, i - .5), 1, 1, fill=False,
                                       edgecolor=INK, lw=1.6))
cb = fig.colorbar(plt.cm.ScalarMappable(cmap=DIV, norm=plt.Normalize(-1, 1)),
                  ax=axes, fraction=.017, pad=.02)
cb.set_label("Pearson r", fontsize=9, color=MUTED)
cb.ax.tick_params(labelsize=8, length=0); cb.outline.set_edgecolor("#C9D3D1")
fig.savefig(f"{OUT}/fig5_상관행렬.png", bbox_inches="tight", facecolor="white")
plt.close(fig)


# ================================================================ FIG 5  산점도
pairs = [("K3", "Beta-cell",  "Beta-cell",  s4.loc[featH], h5[featH].T, "형질", featH),
         ("K5", "Liver/Lipid","Liver/Lipid",s4.loc[featH], h5[featH].T, "형질", featH),
         ("K3", "Beta-Cell",  "Beta-cell",  s3.loc[varW, UC_W], w5.loc[varW], "변이", varW),
         ("K5", "Liver",      "Liver/Lipid",s3.loc[varW, UC_W], w5.loc[varW], "변이", varW)]
fig, axes = plt.subplots(1, 4, figsize=(13.4, 3.5))
for ax, (kk, uc, disp, truth, mine, kind, idx) in zip(axes, pairs):
    x = truth[uc].values.astype(float)
    y = mine.loc[idx, kk].values.astype(float)
    r = np.corrcoef(x, y)[0, 1]
    ax.scatter(x, y, s=17, color="#0A6157", alpha=.62, linewidths=0)
    ax.set_xlabel(f"논문 {disp} 가중치", fontsize=9, color=INK2)
    ax.set_ylabel(f"우리 {kk} 가중치", fontsize=9, color=INK2)
    ax.set_title(f"{disp} · {kind}축", fontsize=10.5, fontweight="bold", color=INK, pad=8)
    ax.text(.04, .93, f"r = {r:.2f}", transform=ax.transAxes, fontsize=11.5,
            color="#0A6157", fontweight="bold", va="top")
    ax.text(.04, .845, f"n = {len(idx)}", transform=ax.transAxes, fontsize=8.5,
            color=MUTED, va="top")
    ax.tick_params(labelsize=8, length=3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=.22, lw=.6, color="#C9D3D1")
    ax.set_axisbelow(True)
fig.tight_layout(w_pad=2.4)
fig.savefig(f"{OUT}/fig6_산점도.png", bbox_inches="tight", facecolor="white")
plt.close(fig)


# ================================================================ FIG 6  v1->v2 + K분포
h1, w1 = load(V1, 3)
f1 = [f for f in h1.columns if f in s4.index]
C1 = corr(h1[f1], s4.loc[f1])
best1 = C1.max(axis=0)
best2 = CH.max(axis=0)

fig, axes = plt.subplots(1, 2, figsize=(11.6, 3.9),
                         gridspec_kw={"width_ratios": [1.65, 1], "wspace": .3})
ax = axes[0]
names = UC_H[::-1]
yy = np.arange(len(names))
a = [best1[n] for n in names]; b = [best2[n] for n in names]
for i, n in enumerate(names):
    ax.plot([a[i], b[i]], [i, i], color="#CDE6DF", lw=3.4, solid_capstyle="round", zorder=1)
ax.scatter(a, yy, s=62, color="#63BFAF", zorder=3, label="v1 · 형질 35개", linewidths=0)
ax.scatter(b, yy, s=62, color="#0A6157", zorder=3, label="v2 · 형질 44개", linewidths=0)
for i in range(len(names)):
    ax.text(a[i] - .035, i, f"{a[i]:.2f}", ha="right", va="center", fontsize=8.5, color=MUTED)
    ax.text(b[i] + .035, i, f"{b[i]:.2f}", ha="left", va="center", fontsize=9,
            color="#0A6157", fontweight="bold")
ax.set_yticks(yy); ax.set_yticklabels(names, fontsize=9.5)
ax.set_xlim(-.16, 1.16); ax.set_xticks([0, .25, .5, .75, 1.0])
ax.tick_params(labelsize=8.5, length=0)
ax.set_xlabel("형질축 최고 상관 r", fontsize=9, color=INK2)
ax.set_title("입력 형질을 채우자 축이 살아났다", fontsize=11.5, fontweight="bold", color=INK, pad=10)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=.22, lw=.6, color="#C9D3D1"); ax.set_axisbelow(True)
ax.legend(fontsize=8.5, frameon=False, loc="upper left", handletextpad=.3, bbox_to_anchor=(0, 1.02), ncol=2)

ax = axes[1]
ks, cnt = ["K=3", "K=4", "K=5"], [3, 70, 27]
bars = ax.barh(range(3), cnt, height=.55,
               color=["#9BD0C3", "#0A6157", "#0A6157"])
for i, c in enumerate(cnt):
    ax.text(c + 1.8, i, f"{c}회", va="center", fontsize=9, color=MUTED)
ax.set_yticks(range(3)); ax.set_yticklabels(ks, fontsize=9.5)
ax.set_xlim(0, 84); ax.tick_params(labelsize=8.5, length=0)
ax.set_xlabel("100 replicate 중 선택 횟수", fontsize=9, color=INK2)
ax.set_title("K는 ARD가 스스로 골랐다", fontsize=11.5, fontweight="bold", color=INK, pad=10)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=.22, lw=.6, color="#C9D3D1"); ax.set_axisbelow(True)
fig.savefig(f"{OUT}/fig7_v1v2_K분포.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------- 콘솔 확인
print("featH", len(featH), "varW", len(varW))
print("v1 best H:", {n: round(best1[n], 2) for n in UC_H})
print("v2 best H:", {n: round(best2[n], 2) for n in UC_H})
print("saved:", sorted(os.listdir(OUT)))
