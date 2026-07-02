import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys
sys.stdout.reconfigure(encoding="utf-8")
# ============================================
# TREND ANALYSIS — Mandi, Kullu, Chamba
# 2005–2025 | All charts saved as PNG
# ============================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys
sys.stdout.reconfigure(encoding="utf-8")

OUT = r"C:\Users\admin\Desktop\rainfall agent\climate-data\processed"
COLORS = {"Mandi": "#D85A30", "Kullu": "#378ADD", "Chamba": "#1D9E75"}
DISTRICTS = ["Mandi", "Kullu", "Chamba"]

df_daily = pd.read_parquet(f"{OUT}\\mandi_kullu_chamba.parquet")
df_daily["TIME"] = pd.to_datetime(df_daily["TIME"])
df_daily["YEAR"] = df_daily["TIME"].dt.year
df_daily["MONTH"] = df_daily["TIME"].dt.month
df_daily["is_dry"] = df_daily["AVG_RAINFALL_MM"] < 1.0
df_daily["is_wet"] = df_daily["AVG_RAINFALL_MM"] >= 1.0
df_daily["is_heavy"] = df_daily["AVG_RAINFALL_MM"] >= 64.5
df_daily["is_very_heavy"] = df_daily["AVG_RAINFALL_MM"] >= 115.6
df_daily["is_extreme"] = df_daily["AVG_RAINFALL_MM"] >= 204.5

# ── helper ──────────────────────────────────────────────────────────────────
def max_dry_streak(s):
    mx = streak = 0
    for v in s:
        streak = streak + 1 if v else 0
        mx = max(mx, streak)
    return mx

def style(ax, title, xlabel="Year", ylabel=""):
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.legend(fontsize=9)

# ── compute all metrics ─────────────────────────────────────────────────────
# 1. Monsoon totals (Jun–Sep)
monsoon = df_daily[df_daily["MONTH"].between(6,9)]
mon_tot = monsoon.groupby(["YEAR","DISTRICT"])["AVG_RAINFALL_MM"].sum().reset_index()
mon_tot.columns = ["YEAR","DISTRICT","MONSOON_MM"]

# 2. Wet day intensity
wet = df_daily[df_daily["is_wet"]]
wet_int = wet.groupby(["YEAR","DISTRICT"])["AVG_RAINFALL_MM"].mean().reset_index()
wet_int.columns = ["YEAR","DISTRICT","WET_INTENSITY"]

# 3. Dry spells
dry_sp = (df_daily.groupby(["YEAR","DISTRICT"])["is_dry"]
          .apply(max_dry_streak).reset_index(name="MAX_DRY_DAYS"))

# 4. Heavy/very heavy/extreme day counts
heavy = df_daily.groupby(["YEAR","DISTRICT"])["is_heavy"].sum().reset_index(name="HEAVY_DAYS")
vheavy= df_daily.groupby(["YEAR","DISTRICT"])["is_very_heavy"].sum().reset_index(name="VHEAVY_DAYS")
extrem= df_daily.groupby(["YEAR","DISTRICT"])["is_extreme"].sum().reset_index(name="EXTREME_DAYS")

# 5. Wet day count per year
wet_cnt = df_daily.groupby(["YEAR","DISTRICT"])["is_wet"].sum().reset_index(name="WET_DAYS")

# 6. Annual total rainfall
ann_tot = df_daily.groupby(["YEAR","DISTRICT"])["AVG_RAINFALL_MM"].sum().reset_index(name="ANNUAL_MM")

# 7. Monthly averages (climatology)
mon_avg = (monsoon.groupby(["MONTH","DISTRICT"])["AVG_RAINFALL_MM"]
           .mean().reset_index(name="AVG_MM"))

# 8. Peak single day per year
peak_day = df_daily.groupby(["YEAR","DISTRICT"])["AVG_RAINFALL_MM"].max().reset_index(name="PEAK_MM")

# 9. Pre vs post 2015 comparison
pre  = df_daily[df_daily["YEAR"] <= 2014]
post = df_daily[df_daily["YEAR"] >= 2015]

pre_int  = pre[pre["is_wet"]].groupby("DISTRICT")["AVG_RAINFALL_MM"].mean()
post_int = post[post["is_wet"]].groupby("DISTRICT")["AVG_RAINFALL_MM"].mean()
pre_dry  = pre.groupby(["YEAR","DISTRICT"])["is_dry"].apply(max_dry_streak).groupby("DISTRICT").mean()
post_dry = post.groupby(["YEAR","DISTRICT"])["is_dry"].apply(max_dry_streak).groupby("DISTRICT").mean()
pre_hvy  = pre.groupby(["YEAR","DISTRICT"])["is_heavy"].sum().groupby("DISTRICT").mean()
post_hvy = post.groupby(["YEAR","DISTRICT"])["is_heavy"].sum().groupby("DISTRICT").mean()

# 10. IMD category distribution
cat_dist = (df_daily[df_daily["MONTH"].between(6,9)]
            .groupby(["DISTRICT","CATEGORY"])
            .size().reset_index(name="DAYS"))

years = sorted(df_daily["YEAR"].unique())

print("All metrics computed. Generating charts...")

# ════════════════════════════════════════════════════════════════════════════
# CHART 1 — Monsoon total rainfall trend
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12,5))
for d in DISTRICTS:
    sub = mon_tot[mon_tot["DISTRICT"]==d]
    ax.plot(sub["YEAR"], sub["MONSOON_MM"], color=COLORS[d],
            marker="o", markersize=5, linewidth=2, label=d)
    z = np.polyfit(sub["YEAR"], sub["MONSOON_MM"], 1)
    ax.plot(sub["YEAR"], np.polyval(z, sub["YEAR"]),
            color=COLORS[d], linestyle="--", alpha=0.4, linewidth=1)
ax.axvspan(2015, 2025, alpha=0.05, color="red", label="Post-2015")
style(ax, "Monsoon total rainfall 2005–2025 (Jun–Sep)", ylabel="mm")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart1_monsoon_total.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 1 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 2 — Wet day intensity trend
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12,5))
for d in DISTRICTS:
    sub = wet_int[wet_int["DISTRICT"]==d]
    ax.plot(sub["YEAR"], sub["WET_INTENSITY"], color=COLORS[d],
            marker="s", markersize=5, linewidth=2, label=d)
    z = np.polyfit(sub["YEAR"], sub["WET_INTENSITY"], 1)
    ax.plot(sub["YEAR"], np.polyval(z, sub["YEAR"]),
            color=COLORS[d], linestyle="--", alpha=0.4, linewidth=1)
style(ax, "Average rainfall intensity on wet days 2005–2025", ylabel="mm per wet day")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart2_wet_intensity.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 2 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 3 — Longest dry spell per year
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12,5))
for d in DISTRICTS:
    sub = dry_sp[dry_sp["DISTRICT"]==d]
    ax.plot(sub["YEAR"], sub["MAX_DRY_DAYS"], color=COLORS[d],
            marker="^", markersize=5, linewidth=2, label=d)
    z = np.polyfit(sub["YEAR"], sub["MAX_DRY_DAYS"], 1)
    ax.plot(sub["YEAR"], np.polyval(z, sub["YEAR"]),
            color=COLORS[d], linestyle="--", alpha=0.4, linewidth=1)
style(ax, "Longest consecutive dry spell per year 2005–2025", ylabel="days")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart3_dry_spells.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 3 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 4 — Heavy rain days stacked per district
# ════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(14,5), sharey=True)
for i, d in enumerate(DISTRICTS):
    hv = heavy[heavy["DISTRICT"]==d].set_index("YEAR")["HEAVY_DAYS"]
    vh = vheavy[vheavy["DISTRICT"]==d].set_index("YEAR")["VHEAVY_DAYS"]
    axes[i].bar(years, [hv.get(y,0) for y in years],
                color=COLORS[d], alpha=0.5, label="Heavy (≥64.5mm)")
    axes[i].bar(years, [vh.get(y,0) for y in years],
                color=COLORS[d], alpha=0.9, label="Very Heavy (≥115mm)")
    axes[i].set_title(d, fontsize=12, fontweight="bold")
    axes[i].set_xlabel("Year", fontsize=9)
    axes[i].spines[["top","right"]].set_visible(False)
    axes[i].grid(axis="y", alpha=0.3)
    axes[i].tick_params(axis="x", rotation=45)
    axes[i].legend(fontsize=8)
axes[0].set_ylabel("Days", fontsize=10)
fig.suptitle("Heavy and very heavy rain days per year 2005–2025",
             fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart4_heavy_days.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 4 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 5 — Wet days count (are rainy days shrinking?)
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12,5))
for d in DISTRICTS:
    sub = wet_cnt[wet_cnt["DISTRICT"]==d]
    ax.plot(sub["YEAR"], sub["WET_DAYS"], color=COLORS[d],
            marker="o", markersize=5, linewidth=2, label=d)
    z = np.polyfit(sub["YEAR"], sub["WET_DAYS"], 1)
    ax.plot(sub["YEAR"], np.polyval(z, sub["YEAR"]),
            color=COLORS[d], linestyle="--", alpha=0.4, linewidth=1)
style(ax, "Number of wet days per year 2005–2025 (≥1mm)", ylabel="days")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart5_wet_days_count.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 5 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 6 — Peak single day rainfall per year
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12,5))
for d in DISTRICTS:
    sub = peak_day[peak_day["DISTRICT"]==d]
    ax.plot(sub["YEAR"], sub["PEAK_MM"], color=COLORS[d],
            marker="D", markersize=5, linewidth=2, label=d)
ax.axhline(64.5,  color="orange", linestyle=":", linewidth=1, label="Heavy (64.5mm)")
ax.axhline(115.6, color="red",    linestyle=":", linewidth=1, label="Very Heavy (115.6mm)")
style(ax, "Peak single-day rainfall per year 2005–2025", ylabel="mm")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart6_peak_day.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 6 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 7 — Pre vs Post 2015 comparison (bar chart)
# ════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(14,5))
metrics = [
    (pre_int, post_int, "Wet day intensity (mm)", "chart7a"),
    (pre_dry, post_dry, "Max dry streak (days)",  "chart7b"),
    (pre_hvy, post_hvy, "Heavy rain days/year",   "chart7c"),
]
titles = ["Intensity rising?", "Dry spells longer?", "Extreme days more frequent?"]
for i, (pre_m, post_m, ylabel, _) in enumerate(metrics):
    x = np.arange(len(DISTRICTS))
    axes[i].bar(x-0.2, [pre_m.get(d,0)  for d in DISTRICTS],
                0.35, label="2005–2014", color="#888780", alpha=0.8)
    axes[i].bar(x+0.2, [post_m.get(d,0) for d in DISTRICTS],
                0.35, label="2015–2025", color="#D85A30", alpha=0.8)
    axes[i].set_title(titles[i], fontsize=11, fontweight="bold")
    axes[i].set_ylabel(ylabel, fontsize=9)
    axes[i].set_xticks(x)
    axes[i].set_xticklabels(DISTRICTS, fontsize=9)
    axes[i].legend(fontsize=8)
    axes[i].spines[["top","right"]].set_visible(False)
    axes[i].grid(axis="y", alpha=0.3)
fig.suptitle("Before vs after 2015 — what changed in 3 districts",
             fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart7_pre_post_2015.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 7 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 8 — Monthly rainfall distribution (which month is most dangerous?)
# ════════════════════════════════════════════════════════════════════════════
month_names = {6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep"}
fig, axes = plt.subplots(1, 3, figsize=(14,5), sharey=True)
for i, d in enumerate(DISTRICTS):
    sub = mon_avg[mon_avg["DISTRICT"]==d].copy()
    sub["MON"] = sub["MONTH"].map(month_names)
    axes[i].bar(sub["MON"], sub["AVG_MM"], color=COLORS[d], alpha=0.85)
    axes[i].set_title(d, fontsize=12, fontweight="bold")
    axes[i].set_xlabel("Month", fontsize=9)
    axes[i].spines[["top","right"]].set_visible(False)
    axes[i].grid(axis="y", alpha=0.3)
axes[0].set_ylabel("Avg daily rainfall (mm)", fontsize=10)
fig.suptitle("Which monsoon month is most dangerous? Average daily rainfall 2005–2025",
             fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart8_monthly_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 8 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 9 — IMD category distribution (pie charts)
# ════════════════════════════════════════════════════════════════════════════
CAT_ORDER  = ["Normal","Moderate","Rather Heavy","Heavy","Very Heavy","Extremely Heavy"]
CAT_COLORS = ["#D3D1C7","#9FE1CB","#378ADD","#EF9F27","#D85A30","#A32D2D"]
fig, axes = plt.subplots(1, 3, figsize=(16,6))
for i, d in enumerate(DISTRICTS):
    sub = cat_dist[cat_dist["DISTRICT"]==d].set_index("CATEGORY")["DAYS"]
    vals  = [sub.get(c,0) for c in CAT_ORDER]
    cols  = [CAT_COLORS[j] for j in range(len(CAT_ORDER))]
    fvals = [v for v in vals if v > 0]
    fcols = [CAT_COLORS[j] for j,v in enumerate(vals) if v > 0]
    flabs = [CAT_ORDER[j] for j,v in enumerate(vals) if v > 0]

    wedges, texts = axes[i].pie(
        fvals,
        colors=fcols,
        startangle=90,
        wedgeprops={"linewidth":0.5, "edgecolor":"white"},
        pctdistance=0.75
    )
    axes[i].set_title(d, fontsize=12, fontweight="bold", pad=15)

    # legend instead of labels — no overlap
    legend_labels = [f"{l}: {v}d ({v/sum(fvals)*100:.0f}%)"
                     for l,v in zip(flabs,fvals)]
    axes[i].legend(wedges, legend_labels,
                   loc="lower center",
                   bbox_to_anchor=(0.5, -0.35),
                   fontsize=8,
                   frameon=False,
                   ncol=1)

fig.suptitle("Monsoon day category distribution 2005-2025 (IMD thresholds)",
             fontsize=13, fontweight="bold")
plt.subplots_adjust(bottom=0.3)
plt.savefig(f"{OUT}\\chart9_category_pie.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 9 saved")

# ════════════════════════════════════════════════════════════════════════════
# CHART 10 — Annual total rainfall (full year not just monsoon)
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12,5))
width = 0.25
x = np.arange(len(years))
for i, d in enumerate(DISTRICTS):
    sub = ann_tot[ann_tot["DISTRICT"]==d].set_index("YEAR")
    vals = [sub["ANNUAL_MM"].get(y,0) for y in years]
    ax.bar(x + i*width, vals, width, color=COLORS[d], alpha=0.8, label=d)
ax.set_xticks(x + width)
ax.set_xticklabels(years, rotation=45, fontsize=8)
ax.set_ylabel("mm", fontsize=10)
ax.spines[["top","right"]].set_visible(False)
ax.grid(axis="y", alpha=0.3)
ax.legend(fontsize=9)
ax.set_title("Annual total rainfall 2005–2025 (full year)",
             fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT}\\chart10_annual_total.png", dpi=150, bbox_inches="tight")
plt.close()
print("Chart 10 saved")

# ════════════════════════════════════════════════════════════════════════════
# PRINT KEY FINDINGS
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*55)
print("KEY FINDINGS FOR REPORT")
print("="*55)
for d in DISTRICTS:
    wi_pre  = pre[pre["is_wet"] & (pre["DISTRICT"]==d)]["AVG_RAINFALL_MM"].mean()
    wi_post = post[post["is_wet"] & (post["DISTRICT"]==d)]["AVG_RAINFALL_MM"].mean()
    ds_pre  = pre[pre["DISTRICT"]==d].groupby("YEAR")["is_dry"].apply(max_dry_streak).mean()
    ds_post = post[post["DISTRICT"]==d].groupby("YEAR")["is_dry"].apply(max_dry_streak).mean()
    pk      = peak_day[peak_day["DISTRICT"]==d]["PEAK_MM"].max()
    print(f"\n{d}:")
    print(f"  Wet day intensity  : {wi_pre:.1f}mm (2005-14) → {wi_post:.1f}mm (2015-25)  [{((wi_post-wi_pre)/wi_pre*100):+.1f}%]")
    print(f"  Max dry streak     : {ds_pre:.0f}d  (2005-14) → {ds_post:.0f}d  (2015-25)  [{((ds_post-ds_pre)/ds_pre*100):+.1f}%]")
    print(f"  All-time peak day  : {pk:.1f}mm")

print("\n10 charts saved to:", OUT)




