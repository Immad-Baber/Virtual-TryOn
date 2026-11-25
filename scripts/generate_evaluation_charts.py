import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("app_assets/charts", exist_ok=True)
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

# 1. CFG Latency Chart
fig, ax1 = plt.subplots(figsize=(7, 4), dpi=150)
cfgs = [1.5, 2.5, 3.5, 5.0]
lats = [96.41, 104.13, 108.63, 110.88]
bars = ax1.bar([str(c) for c in cfgs], lats, color="#2563eb", width=0.5, edgecolor="#1e40af", alpha=0.85)
ax1.set_title("CatVTON: Inference Latency vs Classifier-Free Guidance (CFG)", fontsize=12, fontweight="bold", pad=12)
ax1.set_xlabel("CFG Guidance Scale (s)", fontsize=10, fontweight="bold")
ax1.set_ylabel("Inference Latency (Seconds on Tesla T4)", fontsize=10, fontweight="bold")
ax1.set_ylim(80, 125)
for bar in bars:
    y = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, y + 1.2, f"{y:.1f}s", ha="center", va="bottom", fontsize=10, fontweight="bold")
plt.tight_layout()
plt.savefig("app_assets/charts/cfg_latency_chart.png")
plt.close()
print("Generated cfg_latency_chart.png")

# 2. Steps Latency & Speedup Chart
fig, ax1 = plt.subplots(figsize=(7, 4), dpi=150)
steps = ["20 Steps", "35 Steps", "50 Steps"]
step_lats = [45.25, 78.17, 111.22]
speedups = [111.22/45.25, 111.22/78.17, 1.0]

ax2 = ax1.twinx()
bars = ax1.bar(steps, step_lats, color="#059669", width=0.45, edgecolor="#047857", alpha=0.85, label="Latency (s)")
lines = ax2.plot(steps, speedups, color="#dc2626", marker="o", linewidth=2.5, markersize=8, label="Speedup Factor")

ax1.set_title("CatVTON: DDIM Denoising Steps vs Latency & Speedup", fontsize=12, fontweight="bold", pad=12)
ax1.set_xlabel("DDIM Inference Steps", fontsize=10, fontweight="bold")
ax1.set_ylabel("Latency (Seconds on T4)", fontsize=10, fontweight="bold", color="#059669")
ax2.set_ylabel("Relative Speedup Factor (vs 50 steps)", fontsize=10, fontweight="bold", color="#dc2626")
ax1.set_ylim(0, 130)
ax2.set_ylim(0.8, 3.0)

for bar in bars:
    y = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, y + 2, f"{y:.1f}s", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#059669")
for i, txt in enumerate(speedups):
    ax2.annotate(f"{txt:.2f}x", (steps[i], speedups[i]), textcoords="offset points", xytext=(0, 10), ha="center", fontweight="bold", color="#dc2626")

plt.tight_layout()
plt.savefig("app_assets/charts/steps_latency_chart.png")
plt.close()
print("Generated steps_latency_chart.png")

# 3. Identity Preservation SSIM Comparison Chart
fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=150)
categories = ["Head / Face Region", "Lower Body (Pants/Shoes)", "Overall Protected Non-Inpaint"]
catvton_ssim = [0.7644, 0.9977, 0.8811]
idm_ssim = [0.6144, 0.9903, 0.8024]

x = np.arange(len(categories))
width = 0.35

rects1 = ax.bar(x - width/2, catvton_ssim, width, label="CatVTON (Proposed Base)", color="#2563eb", edgecolor="#1e40af")
rects2 = ax.bar(x + width/2, idm_ssim, width, label="IDM-VTON (Benchmark)", color="#f59e0b", edgecolor="#d97706")

ax.set_title("Identity Preservation SSIM: CatVTON vs IDM-VTON\n(Measured on Non-Inpainted Protected Anatomy)", fontsize=11, fontweight="bold", pad=10)
ax.set_ylabel("Structural Similarity Index (SSIM)", fontsize=10, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=9, fontweight="bold")
ax.set_ylim(0.4, 1.1)
ax.legend(loc="lower right", frameon=True)

for rect in rects1:
    h = rect.get_height()
    ax.annotate(f"{h:.4f}", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")
for rect in rects2:
    h = rect.get_height()
    ax.annotate(f"{h:.4f}", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

plt.tight_layout()
plt.savefig("app_assets/charts/ssim_identity_chart.png")
plt.close()
print("Generated ssim_identity_chart.png")

# 4. Mask Coverage Area Comparison
fig, ax = plt.subplots(figsize=(7, 3.8), dpi=150)
mask_labels = ["Geometric Polygon", "Unclipped SegFormer ATR", "Hand-Aware Anatomical (Ours)"]
coverages = [28.40, 41.20, 19.56]
colors = ["#ef4444", "#f59e0b", "#10b981"]

bars = ax.barh(mask_labels, coverages, color=colors, height=0.5, edgecolor="#374151")
ax.set_title("Mask Coverage Area (% of 768x1024 Image Space)", fontsize=11, fontweight="bold", pad=10)
ax.set_xlabel("Percentage Coverage (%)", fontsize=10, fontweight="bold")
ax.set_xlim(0, 50)

for bar in bars:
    w_val = bar.get_width()
    ax.text(w_val + 0.8, bar.get_y() + bar.get_height()/2.0, f"{w_val:.2f}%", ha="left", va="center", fontsize=9, fontweight="bold")

plt.tight_layout()
plt.savefig("app_assets/charts/mask_coverage_chart.png")
plt.close()
print("Generated mask_coverage_chart.png")

print("All charts successfully generated in app_assets/charts/!")
