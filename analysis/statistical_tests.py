# ==============================================================================
# STATISTICAL FOUNDATION — Himachal Climate Digital Twin
# Districts : Mandi, Kullu, Chamba
# Period    : 2005 to 2025
# Output    : TABLE 2 in research paper + publication-quality charts
# Run with  : python analysis/statistical_tests.py
# ==============================================================================

import pandas as pd
import numpy as np
from scipy import stats
import pymannkendall as mk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import os
import warnings
warnings.filterwarnings("ignore")

# ── paths ─────────────────────────────────────────────────────────────────────
DATA = r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed\mandi_kullu_chamba.parquet"
OUT  = r"C:\Users\admin\Desktop\rainfall agent\climate-data\outputs"
os.makedirs(OUT, exist_ok=True)

DISTRICTS = ["Mandi", "Kullu", "Chamba"]
COLORS    = {"Mandi": "#D85A30", "Kullu": "#378ADD", "Chamba": "#1D9E75"}
SPLIT     = 2015

# ── publication style ─────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.25,
    "grid.linestyle":    "--",
    "figure.dpi":        150,
    "axes.labelsize":    12,
    "axes.titlesize":    14,
    "axes.titleweight":  "bold",
    "legend.frameon":    False,
    "legend.fontsize":   10,
})

# ── load ──────────────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_parquet(DATA)
df["TIME"]      = pd.to_datetime(df["TIME"])
df["YEAR"]      = df["TIME"].dt.year
df["MONTH"]     = df["TIME"].dt.month
df["is_wet"]    = df["AVG_RAINFALL_MM"] >= 1.0
df["is_heavy"]  = df["AVG_RAINFALL_MM"] >= 64.5
df["is_dry"]    = df["AVG_RAINFALL_MM"] < 1.0
df["is_monsoon"]= df["MONTH"].between(6, 9)
print(f"Loaded {len(df):,} rows")

def max_dry_streak(series):
    mx = streak = 0
    for v in series:
        streak = streak + 1 if v else 0
        mx = max(mx, streak)
    return mx

# ── PHASE 1: Annual metrics ───────────────────────────────────────────────────
print("Computing annual metrics...")
records = []
for year in range(2005, 2026):
    for district in DISTRICTS:
        sub = df[(df["YEAR"] == year) & (df["DISTRICT"] == district)]
        mon = sub[sub["is_monsoon"]]
        records.append({
            "YEAR":          year,
            "DISTRICT":      district,
            "MONSOON_TOTAL": round(mon["AVG_RAINFALL_MM"].sum(), 2),
            "WET_INTENSITY": round(sub[sub["is_wet"]]["AVG_RAINFALL_MM"].mean(), 2) if sub["is_wet"].any() else 0,
            "HEAVY_DAYS":    int(sub["is_heavy"].sum()),
            "PEAK_DAY":      round(sub["AVG_RAINFALL_MM"].max(), 2),
            "DRY_STREAK":    max_dry_streak(sub["is_dry"].tolist()),
            "ANNUAL_TOTAL":  round(sub["AVG_RAINFALL_MM"].sum(), 2),
            "WET_DAY_COUNT": int(sub["is_wet"].sum()),
        })

annual = pd.DataFrame(records)
annual.to_csv(f"{OUT}\\annual_metrics.csv", index=False)
print(f"Annual metrics: {len(annual)} rows")

# ── PHASE 2: Statistical tests ────────────────────────────────────────────────
print("Running statistical tests...")
METRICS = {
    "Monsoon Total (mm)":     "MONSOON_TOTAL",
    "Wet Day Intensity (mm)": "WET_INTENSITY",
    "Heavy Rain Days":        "HEAVY_DAYS",
    "Peak Single Day (mm)":   "PEAK_DAY",
    "Max Dry Streak (days)":  "DRY_STREAK",
    "Annual Total (mm)":      "ANNUAL_TOTAL",
    "Wet Day Count":          "WET_DAY_COUNT",
}

results = []
for metric_name, col in METRICS.items():
    for district in DISTRICTS:
        sub    = annual[annual["DISTRICT"] == district].sort_values("YEAR")
        values = sub[col].values
        years  = sub["YEAR"].values
        early  = sub[sub["YEAR"] < SPLIT][col].values
        late   = sub[sub["YEAR"] >= SPLIT][col].values

        try:
            mkr       = mk.original_test(values)
            mk_trend  = mkr.trend
            mk_p      = round(mkr.p, 4)
            mk_tau    = round(mkr.Tau, 4)
            mk_sig    = mk_p < 0.05
        except:
            mk_trend, mk_p, mk_tau, mk_sig = "error", 1.0, 0.0, False

        try:
            sen            = stats.theilslopes(values, years)
            sens_yr        = round(sen.slope, 4)
            sens_dec       = round(sen.slope * 10, 2)
        except:
            sens_yr = sens_dec = 0.0

        try:
            _, tp     = stats.ttest_ind(early, late, equal_var=False)
            t_sig     = tp < 0.05
            t_p       = round(tp, 4)
            m_early   = round(early.mean(), 2)
            m_late    = round(late.mean(), 2)
            pct       = round(((m_late - m_early) / m_early) * 100, 1) if m_early else 0
        except:
            t_sig = False
            t_p = m_early = m_late = pct = 0.0

        results.append({
            "Metric":         metric_name,
            "District":       district,
            "MK Trend":       mk_trend,
            "MK p-value":     mk_p,
            "MK Tau":         mk_tau,
            "MK Sig":         mk_sig,
            "Sens/yr":        sens_yr,
            "Sens/decade":    sens_dec,
            "Mean 2005-2014": m_early,
            "Mean 2015-2025": m_late,
            "Change %":       pct,
            "T-test p":       t_p,
            "T-test Sig":     t_sig,
        })

res = pd.DataFrame(results)
res.to_csv(f"{OUT}\\statistical_results_table.csv", index=False)

# ── PHASE 3: Print clean table ────────────────────────────────────────────────
print("\n" + "="*95)
print("TABLE 2 — STATISTICAL RESULTS")
print("="*95)
fmt = "{:<28} {:<10} {:<14} {:<8} {:<12} {:<10} {:<10} {:<10} {}"
print(fmt.format("Metric","District","MK Trend","p-val","Sens/dec","2005-14","2015-25","Change%","Sig"))
print("-"*95)
for _, r in res.iterrows():
    sig = "*** p<0.05" if r["T-test Sig"] else ""
    print(fmt.format(
        r["Metric"], r["District"], r["MK Trend"],
        r["MK p-value"], r["Sens/decade"],
        r["Mean 2005-2014"], r["Mean 2015-2025"],
        f"{r['Change %']}%", sig
    ))

# ── PHASE 4: CHART 1 — Trend significance heatmap ────────────────────────────
print("\nGenerating Chart 1: Statistical significance heatmap...")

pivot_p    = res.pivot_table(index="Metric", columns="District", values="MK p-value")
pivot_sig  = res.pivot_table(index="Metric", columns="District", values="MK Sig")
pivot_chg  = res.pivot_table(index="Metric", columns="District", values="Change %")

fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor("#F8F9FA")
ax.set_facecolor("#F8F9FA")

cmap = LinearSegmentedColormap.from_list("sig", ["#D6EAF8", "#1a3a5c"])
im   = ax.imshow(pivot_p.values, cmap=cmap, aspect="auto", vmin=0, vmax=0.5)

for i in range(pivot_p.shape[0]):
    for j in range(pivot_p.shape[1]):
        p    = pivot_p.values[i, j]
        chg  = pivot_chg.values[i, j]
        sig  = pivot_sig.values[i, j]
        clr  = "white" if p < 0.15 else "#1a3a5c"
        cell = f"p={p:.3f}\n{'+' if chg > 0 else ''}{chg:.1f}%"
        ax.text(j, i, cell, ha="center", va="center",
                fontsize=9, color=clr,
                fontweight="bold" if sig else "normal")
        if sig:
            ax.add_patch(mpatches.FancyBboxPatch(
                (j - 0.48, i - 0.48), 0.96, 0.96,
                boxstyle="round,pad=0.02",
                fill=False, edgecolor="#D85A30", linewidth=2.5
            ))

ax.set_xticks(range(len(pivot_p.columns)))
ax.set_yticks(range(len(pivot_p.index)))
ax.set_xticklabels(pivot_p.columns, fontsize=12, fontweight="bold")
ax.set_yticklabels(pivot_p.index, fontsize=10)
ax.set_title("Statistical Significance Heatmap — Mann-Kendall Trend Test\n"
             "Orange border = significant trend (p < 0.05)  ·  Darker blue = lower p-value",
             fontsize=13, fontweight="bold", pad=15)

plt.colorbar(im, ax=ax, label="p-value (lower = more significant)", shrink=0.8)
plt.tight_layout()
plt.savefig(f"{OUT}\\chart_stat_heatmap.png", dpi=180, bbox_inches="tight",
            facecolor="#F8F9FA")
plt.close()
print("  Saved: chart_stat_heatmap.png")

# ── PHASE 5: CHART 2 — Pre vs Post 2015 comparison bars ──────────────────────
print("Generating Chart 2: Pre vs Post 2015 comparison...")

key_metrics = ["Monsoon Total (mm)", "Wet Day Intensity (mm)",
               "Heavy Rain Days", "Max Dry Streak (days)"]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor("#F8F9FA")
axes = axes.flatten()

for idx, metric in enumerate(key_metrics):
    ax  = axes[idx]
    ax.set_facecolor("#F8F9FA")
    sub = res[res["Metric"] == metric]
    x   = np.arange(len(DISTRICTS))
    w   = 0.35

    bars_early = ax.bar(x - w/2,
                        [sub[sub["District"] == d]["Mean 2005-2014"].values[0] for d in DISTRICTS],
                        w, label="2005-2014", color="#B0BEC5", edgecolor="white", linewidth=1.5)
    bars_late  = ax.bar(x + w/2,
                        [sub[sub["District"] == d]["Mean 2015-2025"].values[0] for d in DISTRICTS],
                        w, label="2015-2025",
                        color=[COLORS[d] for d in DISTRICTS],
                        edgecolor="white", linewidth=1.5)

    for i, district in enumerate(DISTRICTS):
        row = sub[sub["District"] == district].iloc[0]
        if row["T-test Sig"]:
            ymax = max(row["Mean 2005-2014"], row["Mean 2015-2025"])
            ax.annotate("*", xy=(i + w/2, ymax),
                        xytext=(i + w/2, ymax * 1.05),
                        ha="center", fontsize=16,
                        color="#D85A30", fontweight="bold")
        pct = row["Change %"]
        ax.text(i + w/2,
                row["Mean 2015-2025"] * 0.5,
                f"{'+' if pct > 0 else ''}{pct:.0f}%",
                ha="center", va="center",
                fontsize=8, color="white", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(DISTRICTS, fontsize=11, fontweight="bold")
    ax.set_title(metric, fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linestyle="--")

fig.suptitle("Pre vs Post 2015 Climate Shift — Mandi, Kullu, Chamba\n"
             "* = statistically significant shift (Welch t-test p < 0.05)  "
             "· % = magnitude of change",
             fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(f"{OUT}\\chart_pre_post_comparison.png", dpi=180,
            bbox_inches="tight", facecolor="#F8F9FA")
plt.close()
print("  Saved: chart_pre_post_comparison.png")

# ── PHASE 6: CHART 3 — Sen's slope trend lines ───────────────────────────────
print("Generating Chart 3: Sen slope trend lines...")

plot_metrics = [
    ("MONSOON_TOTAL", "Monsoon Total (mm)"),
    ("WET_INTENSITY", "Wet Day Intensity (mm)"),
    ("HEAVY_DAYS",    "Heavy Rain Days"),
    ("DRY_STREAK",    "Max Dry Streak (days)"),
]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor("#F8F9FA")
axes = axes.flatten()

for idx, (col, label) in enumerate(plot_metrics):
    ax = axes[idx]
    ax.set_facecolor("#F8F9FA")

    for district in DISTRICTS:
        sub    = annual[annual["DISTRICT"] == district].sort_values("YEAR")
        years  = sub["YEAR"].values
        values = sub[col].values
        color  = COLORS[district]

        ax.plot(years, values, "o-", color=color, linewidth=2,
                markersize=5, alpha=0.8, label=district)

        try:
            sen   = stats.theilslopes(values, years)
            trend = sen.slope * years + (sen.intercept)
            ax.plot(years, trend, "--", color=color,
                    linewidth=1.5, alpha=0.5)
            slope_dec = sen.slope * 10
            mk_r      = mk.original_test(values)
            sig_str   = f"({'+' if slope_dec > 0 else ''}{slope_dec:.1f}/dec{'*' if mk_r.p < 0.05 else ''})"
            ax.text(years[-1] + 0.2,
                    trend[-1],
                    sig_str,
                    fontsize=7.5,
                    color=color,
                    va="center")
        except:
            pass

    ax.axvspan(SPLIT, 2025, alpha=0.06, color="#D85A30",
               label="Post-2015 period")
    ax.axvline(SPLIT, color="#D85A30", linestyle=":",
               linewidth=1.5, alpha=0.7)
    ax.set_title(label, fontsize=12, fontweight="bold")
    ax.set_xlabel("Year", fontsize=10)
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.25, linestyle="--")

fig.suptitle("20-Year Trend Analysis with Sen's Slope — Mandi, Kullu, Chamba\n"
             "Dashed line = Sen trend  ·  * = Mann-Kendall significant (p < 0.05)"
             "  ·  Shaded = post-2015 period",
             fontsize=13, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(f"{OUT}\\chart_sens_slope_trends.png", dpi=180,
            bbox_inches="tight", facecolor="#F8F9FA")
plt.close()
print("  Saved: chart_sens_slope_trends.png")

# ── PHASE 7: CHART 4 — Statistical summary dashboard ─────────────────────────
print("Generating Chart 4: Summary dashboard...")

sig_results = res[res["MK Sig"] == True].copy()
total_tests = len(res)
sig_count   = len(sig_results)

fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor("#0D1B2A")
gs  = gridspec.GridSpec(2, 4, figure=fig, hspace=0.45, wspace=0.4)

title_ax = fig.add_subplot(gs[0, :])
title_ax.axis("off")
title_ax.text(0.5, 0.7,
              "HIMACHAL CLIMATE DIGITAL TWIN",
              transform=title_ax.transAxes,
              ha="center", va="center",
              fontsize=22, fontweight="bold", color="white",
              fontfamily="DejaVu Sans")
title_ax.text(0.5, 0.2,
              "Statistical Proof of Climate Shift  ·  Mandi · Kullu · Chamba  ·  2005–2025",
              transform=title_ax.transAxes,
              ha="center", va="center",
              fontsize=13, color="#90CAF9")

stat_boxes = [
    (f"{sig_count}/{total_tests}", "Significant\nTrends", "#D85A30"),
    ("2015",                       "Climate\nBreakpoint", "#378ADD"),
    ("3",                          "Districts\nAnalysed",  "#1D9E75"),
    ("7",                          "Metrics\nTested",      "#F59E0B"),
]

for i, (val, lbl, col) in enumerate(stat_boxes):
    ax = fig.add_subplot(gs[1, i])
    ax.set_facecolor("#1a2744")
    ax.axis("off")
    ax.text(0.5, 0.65, val, transform=ax.transAxes,
            ha="center", va="center",
            fontsize=36, fontweight="bold", color=col)
    ax.text(0.5, 0.2, lbl, transform=ax.transAxes,
            ha="center", va="center",
            fontsize=11, color="white", alpha=0.85)
    for spine in ["top","bottom","left","right"]:
        ax.spines[spine].set_visible(False)

plt.savefig(f"{OUT}\\chart_stat_dashboard.png", dpi=180,
            bbox_inches="tight", facecolor="#0D1B2A")
plt.close()
print("  Saved: chart_stat_dashboard.png")

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("KEY FINDINGS FOR PAPER")
print("="*60)
sig = res[res["MK Sig"]]
print(f"\nSignificant trends (p < 0.05): {len(sig)} of {total_tests} tests")
for _, r in sig.iterrows():
    d = "RISING" if r["Sens/yr"] > 0 else "FALLING"
    print(f"  {r['District']:8} {r['Metric']:30} {d} "
          f"{abs(r['Sens/decade']):.2f}/decade (p={r['MK p-value']})")

print("\nPre vs Post 2015 (significant shifts):")
tsig = res[res["T-test Sig"]]
for _, r in tsig.iterrows():
    print(f"  {r['District']:8} {r['Metric']:30} "
          f"{r['Mean 2005-2014']} to {r['Mean 2015-2025']} "
          f"({'+' if r['Change %'] > 0 else ''}{r['Change %']}%)")

print(f"\nOutputs saved to: {OUT}")
print("  annual_metrics.csv")
print("  statistical_results_table.csv  <- TABLE 2 in paper")
print("  chart_stat_heatmap.png")
print("  chart_pre_post_comparison.png")
print("  chart_sens_slope_trends.png")
print("  chart_stat_dashboard.png")
print("\nDone.")