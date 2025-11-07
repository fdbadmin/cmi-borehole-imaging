#!/usr/bin/env python3
"""
Optimize Coal Detection Cutoffs using CMI Conductivity and Density Log
Uses cross-plot analysis to separate coal from siderite
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.ndimage import gaussian_filter1d
from scipy.stats import gaussian_kde
import lasio

print("\n" + "="*80)
print("COAL CUTOFF OPTIMIZATION - CMI CONDUCTIVITY vs DENSITY")
print("="*80)

# Load CMI data
print("\nLoading processed CMI image...")
cmi_data = pd.read_csv('CMI_NoInterpolation_Image.csv')
depth_cmi = cmi_data['DEPTH'].values
image = cmi_data.iloc[:, 1:].values
avg_conductivity = np.nanmean(image, axis=1)
print(f"✓ CMI data loaded: {len(depth_cmi)} samples")

# Load density log from LAS
print("\nLoading density log...")
las = lasio.read('Raw dataset/qgc_anya_105_mai_mfe_mss_mpd_mdn_hires.las')
depth_las = las['DEPT']
rhob = las['HDEN']  # High-resolution bulk density

print(f"✓ LAS data loaded: {len(depth_las)} samples")
print(f"  Depth range: {depth_las[0]:.2f} to {depth_las[-1]:.2f}m")

# Resample density to CMI depth grid
print("\nResampling density to CMI depth grid...")
rhob_resampled = np.interp(depth_cmi, depth_las, rhob)
print(f"✓ Density resampled to {len(rhob_resampled)} samples")

# Create valid data mask (remove NaN and invalid values)
valid_mask = (~np.isnan(avg_conductivity)) & (~np.isnan(rhob_resampled)) & (rhob_resampled > 0)
valid_cond = avg_conductivity[valid_mask]
valid_rhob = rhob_resampled[valid_mask]
valid_depth = depth_cmi[valid_mask]

print(f"✓ Valid samples: {len(valid_cond)} ({len(valid_cond)/len(depth_cmi)*100:.1f}%)")

# Calculate statistics
print("\n" + "-"*80)
print("DATA STATISTICS")
print("-"*80)
print(f"Conductivity:")
print(f"  Min: {valid_cond.min():.1f}")
print(f"  P10: {np.percentile(valid_cond, 10):.1f}")
print(f"  P25: {np.percentile(valid_cond, 25):.1f}")
print(f"  P50: {np.percentile(valid_cond, 50):.1f}")
print(f"  P75: {np.percentile(valid_cond, 75):.1f}")
print(f"  P90: {np.percentile(valid_cond, 90):.1f}")
print(f"  Max: {valid_cond.max():.1f}")

print(f"\nDensity (g/cc):")
print(f"  Min: {valid_rhob.min():.2f}")
print(f"  P10: {np.percentile(valid_rhob, 10):.2f}")
print(f"  P25: {np.percentile(valid_rhob, 25):.2f}")
print(f"  P50: {np.percentile(valid_rhob, 50):.2f}")
print(f"  P75: {np.percentile(valid_rhob, 75):.2f}")
print(f"  P90: {np.percentile(valid_rhob, 90):.2f}")
print(f"  Max: {valid_rhob.max():.2f}")
print("-"*80)

# Analyze coal vs siderite populations
# Coal: Low density (<1.8 g/cc) AND low conductivity
# Siderite: Low conductivity BUT higher density (>2.5 g/cc)
print("\nAnalyzing lithology populations...")

coal_mask = (valid_rhob < 1.8)
siderite_mask = (valid_rhob > 2.5) & (valid_cond < 200)
shale_mask = (valid_rhob >= 1.8) & (valid_rhob <= 2.5)

print(f"\nPreliminary classification:")
print(f"  Coal (RHOB < 1.8):      {np.sum(coal_mask):6d} samples ({np.sum(coal_mask)/len(valid_rhob)*100:5.1f}%)")
print(f"  Siderite (RHOB > 2.5):  {np.sum(siderite_mask):6d} samples ({np.sum(siderite_mask)/len(valid_rhob)*100:5.1f}%)")
print(f"  Shale (1.8-2.5):        {np.sum(shale_mask):6d} samples ({np.sum(shale_mask)/len(valid_rhob)*100:5.1f}%)")

# Conductivity statistics for each lithology
print(f"\nConductivity by lithology:")
print(f"  Coal:     Mean={np.mean(valid_cond[coal_mask]):.1f}, Median={np.median(valid_cond[coal_mask]):.1f}, Std={np.std(valid_cond[coal_mask]):.1f}")
print(f"  Siderite: Mean={np.mean(valid_cond[siderite_mask]):.1f}, Median={np.median(valid_cond[siderite_mask]):.1f}, Std={np.std(valid_cond[siderite_mask]):.1f}")
print(f"  Shale:    Mean={np.mean(valid_cond[shale_mask]):.1f}, Median={np.median(valid_cond[shale_mask]):.1f}, Std={np.std(valid_cond[shale_mask]):.1f}")

# Calculate optimal conductivity cutoff for coal
# Use P75 of coal population or P25 of shale population, whichever is lower
coal_cond_p75 = np.percentile(valid_cond[coal_mask], 75)
coal_cond_p90 = np.percentile(valid_cond[coal_mask], 90)
shale_cond_p25 = np.percentile(valid_cond[shale_mask], 25)

print(f"\nConductivity cutoff candidates:")
print(f"  Coal P75:  {coal_cond_p75:.1f}")
print(f"  Coal P90:  {coal_cond_p90:.1f}")
print(f"  Shale P25: {shale_cond_p25:.1f}")

# Recommend cutoff
recommended_cutoff = min(coal_cond_p90, shale_cond_p25)
print(f"\n>>> RECOMMENDED CONDUCTIVITY CUTOFF: {recommended_cutoff:.1f}")

# Create comprehensive visualization
fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 1. Cross-plot with density coloring
ax1 = fig.add_subplot(gs[0, 0])
scatter = ax1.scatter(valid_cond, valid_rhob, c=valid_rhob, s=0.5, alpha=0.3, 
                     cmap='viridis', vmin=1.0, vmax=3.0)
ax1.axhline(1.8, color='red', linestyle='--', linewidth=2, label='Coal density cutoff (1.8)')
ax1.axvline(recommended_cutoff, color='orange', linestyle='--', linewidth=2, 
           label=f'Conductivity cutoff ({recommended_cutoff:.0f})')
ax1.axvline(170, color='cyan', linestyle=':', linewidth=1.5, label='User suggestion (170)')
ax1.set_xlabel('CMI Conductivity (normalized)', fontsize=10)
ax1.set_ylabel('Density (g/cc)', fontsize=10)
ax1.set_title('Cross-plot: Conductivity vs Density', fontsize=11, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=8)
plt.colorbar(scatter, ax=ax1, label='Density (g/cc)')

# 2. 2D Histogram
ax2 = fig.add_subplot(gs[0, 1])
h = ax2.hist2d(valid_cond, valid_rhob, bins=[50, 50], cmap='YlOrRd', 
              norm=LogNorm(), cmin=1)
ax2.axhline(1.8, color='cyan', linestyle='--', linewidth=2, label='Coal cutoff')
ax2.axvline(recommended_cutoff, color='cyan', linestyle='--', linewidth=2)
ax2.axvline(170, color='blue', linestyle=':', linewidth=1.5)
ax2.set_xlabel('CMI Conductivity', fontsize=10)
ax2.set_ylabel('Density (g/cc)', fontsize=10)
ax2.set_title('2D Histogram (log scale)', fontsize=11, fontweight='bold')
ax2.grid(True, alpha=0.3)
plt.colorbar(h[3], ax=ax2, label='Count (log)')

# 3. Conductivity histogram by lithology
ax3 = fig.add_subplot(gs[0, 2])
ax3.hist(valid_cond[coal_mask], bins=50, alpha=0.5, color='brown', label='Coal (RHOB<1.8)', density=True)
ax3.hist(valid_cond[siderite_mask], bins=50, alpha=0.5, color='orange', label='Siderite (RHOB>2.5)', density=True)
ax3.hist(valid_cond[shale_mask], bins=50, alpha=0.5, color='gray', label='Shale (1.8-2.5)', density=True)
ax3.axvline(recommended_cutoff, color='red', linestyle='--', linewidth=2, label=f'Cutoff ({recommended_cutoff:.0f})')
ax3.axvline(170, color='blue', linestyle=':', linewidth=1.5, label='User (170)')
ax3.set_xlabel('CMI Conductivity', fontsize=10)
ax3.set_ylabel('Probability Density', fontsize=10)
ax3.set_title('Conductivity Distribution by Lithology', fontsize=11, fontweight='bold')
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3)

# 4. Depth track - Conductivity
ax4 = fig.add_subplot(gs[1:, 0])
ax4.plot(avg_conductivity, depth_cmi, 'black', linewidth=0.5)
ax4.axvline(recommended_cutoff, color='red', linestyle='--', linewidth=2)
ax4.axvline(170, color='blue', linestyle=':', linewidth=1.5)
ax4.fill_betweenx(depth_cmi, 0, avg_conductivity, where=(avg_conductivity < recommended_cutoff),
                  color='brown', alpha=0.3, label='Coal (conductivity)')
ax4.set_xlabel('CMI Conductivity', fontsize=10)
ax4.set_ylabel('Depth (m)', fontsize=10)
ax4.set_title('Conductivity Log', fontsize=11, fontweight='bold')
ax4.invert_yaxis()
ax4.grid(True, alpha=0.3)
ax4.legend(fontsize=8)

# 5. Depth track - Density
ax5 = fig.add_subplot(gs[1:, 1])
ax5.plot(rhob_resampled, depth_cmi, 'blue', linewidth=0.5)
ax5.axvline(1.8, color='red', linestyle='--', linewidth=2, label='Coal cutoff (1.8)')
ax5.axvline(2.5, color='orange', linestyle='--', linewidth=2, label='Siderite cutoff (2.5)')
ax5.fill_betweenx(depth_cmi, 0, rhob_resampled, where=(rhob_resampled < 1.8),
                  color='brown', alpha=0.3, label='Coal (density)')
ax5.fill_betweenx(depth_cmi, rhob_resampled, 3.5, where=(rhob_resampled > 2.5),
                  color='orange', alpha=0.3, label='Siderite')
ax5.set_xlabel('Density (g/cc)', fontsize=10)
ax5.set_ylabel('Depth (m)', fontsize=10)
ax5.set_title('Density Log', fontsize=11, fontweight='bold')
ax5.invert_yaxis()
ax5.set_xlim(1.0, 3.0)
ax5.grid(True, alpha=0.3)
ax5.legend(fontsize=8)

# 6. Depth track - Combined coal flag
ax6 = fig.add_subplot(gs[1:, 2])
coal_combined = (avg_conductivity < recommended_cutoff) & (rhob_resampled < 1.8)
ax6.fill_betweenx(depth_cmi, 0, coal_combined.astype(float), color='brown', alpha=0.5, step='mid')
ax6.set_xlim(-0.1, 1.1)
ax6.set_xlabel('Coal Flag', fontsize=10)
ax6.set_ylabel('Depth (m)', fontsize=10)
ax6.set_title('Combined Coal Detection\n(Cond < {} AND RHOB < 1.8)'.format(int(recommended_cutoff)), 
             fontsize=11, fontweight='bold')
ax6.invert_yaxis()
ax6.grid(True, alpha=0.3)
ax6.set_xticks([0, 1])
ax6.set_xticklabels(['Non-coal', 'Coal'])

# Add text box with recommendations
textstr = f"""RECOMMENDED CUTOFFS:
• Conductivity: {recommended_cutoff:.0f}
• Density: 1.8 g/cc

RATIONALE:
• Coal P90: {coal_cond_p90:.0f}
• Shale P25: {shale_cond_p25:.0f}
• Cutoff = min(P90_coal, P25_shale)

This separates coal from both
shale and siderite"""

props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
fig.text(0.98, 0.02, textstr, fontsize=9, verticalalignment='bottom', 
         horizontalalignment='right', bbox=props, family='monospace')

plt.suptitle('Coal Detection Cutoff Optimization - CMI Conductivity vs Density', 
            fontsize=14, fontweight='bold', y=0.995)

# Save figure
output_png = 'Coal_Cutoff_Optimization.png'
output_pdf = 'Coal_Cutoff_Optimization.pdf'
plt.savefig(output_png, dpi=300, bbox_inches='tight')
plt.savefig(output_pdf, bbox_inches='tight')
print(f"\n✓ Figure saved: {output_png}")
print(f"✓ Figure saved: {output_pdf}")

# Save cutoff recommendations to file
cutoffs = {
    'Recommended_Conductivity': recommended_cutoff,
    'Recommended_Density': 1.8,
    'Coal_Cond_P75': coal_cond_p75,
    'Coal_Cond_P90': coal_cond_p90,
    'Shale_Cond_P25': shale_cond_p25,
    'User_Suggested_Cond': 170,
    'Coal_Samples': int(np.sum(coal_mask)),
    'Siderite_Samples': int(np.sum(siderite_mask)),
    'Shale_Samples': int(np.sum(shale_mask))
}

cutoffs_df = pd.DataFrame([cutoffs])
cutoffs_df.to_csv('Coal_Cutoff_Recommendations.csv', index=False)
print(f"✓ Cutoff recommendations saved: Coal_Cutoff_Recommendations.csv")

print("\n" + "="*80)
print("CUTOFF OPTIMIZATION COMPLETE")
print("="*80)
print(f"\nRECOMMENDATIONS:")
print(f"  • Conductivity cutoff: {recommended_cutoff:.0f} (data-driven)")
print(f"  • User suggested:      170 (manual)")
print(f"  • Density cutoff:      1.8 g/cc (separates coal from siderite)")
print(f"\nUse these cutoffs in coal detection to exclude siderite bands")
print("="*80 + "\n")
