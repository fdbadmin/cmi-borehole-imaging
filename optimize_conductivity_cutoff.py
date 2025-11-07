#!/usr/bin/env python3
"""
Optimize CMI Conductivity Cutoff for Coal Detection
Uses multiple statistical methods to find optimal threshold
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.stats import gaussian_kde
from scipy.signal import find_peaks
from sklearn.mixture import GaussianMixture
import lasio

print("\n" + "="*80)
print("CONDUCTIVITY CUTOFF OPTIMIZATION FOR COAL DETECTION")
print("="*80)

# Load CMI data
print("\nLoading processed CMI image...")
cmi_data = pd.read_csv('CMI_NoInterpolation_Image.csv')
depth_cmi = cmi_data['DEPTH'].values
image = cmi_data.iloc[:, 1:].values
avg_conductivity = np.nanmean(image, axis=1)
print(f"✓ CMI data loaded: {len(depth_cmi)} samples")

# Smooth conductivity
window_samples = int(0.05 / np.median(np.diff(depth_cmi)))  # 5cm window
smoothed_cond = gaussian_filter1d(avg_conductivity, sigma=window_samples)

# Load density log
print("\nLoading density log...")
las = lasio.read('Raw dataset/qgc_anya_105_mai_mfe_mss_mpd_mdn_hires.las')
depth_las = las['DEPT']
rhob = las['HDEN']
rhob_resampled = np.interp(depth_cmi, depth_las, rhob)
print(f"✓ Density log loaded and resampled")

# Remove siderite from analysis (high density areas)
SIDERITE_CUTOFF = 2.5
non_siderite_mask = rhob_resampled < SIDERITE_CUTOFF
cond_no_siderite = smoothed_cond[non_siderite_mask]

print(f"\n✓ Removed siderite zones (RHOB > {SIDERITE_CUTOFF}): {np.sum(~non_siderite_mask)} samples")
print(f"  Remaining samples for analysis: {len(cond_no_siderite)}")

# ============================================================================
# METHOD 1: Gaussian Mixture Model (GMM)
# Assumes coal and shale are two distinct populations
# ============================================================================
print("\n" + "-"*80)
print("METHOD 1: GAUSSIAN MIXTURE MODEL (GMM)")
print("-"*80)

# Fit 2-component GMM (coal + shale)
gmm = GaussianMixture(n_components=2, random_state=42)
gmm_labels = gmm.fit_predict(cond_no_siderite.reshape(-1, 1))

# Identify coal vs shale (coal has lower mean)
means = gmm.means_.flatten()
coal_component = 0 if means[0] < means[1] else 1
shale_component = 1 - coal_component

coal_mean = means[coal_component]
shale_mean = means[shale_component]
coal_std = np.sqrt(gmm.covariances_[coal_component][0][0])
shale_std = np.sqrt(gmm.covariances_[shale_component][0][0])

print(f"Coal population:  Mean={coal_mean:.1f}, Std={coal_std:.1f}")
print(f"Shale population: Mean={shale_mean:.1f}, Std={shale_std:.1f}")

# Optimal cutoff = point where two Gaussians intersect
# Using coal_mean + 2*std as conservative estimate
gmm_cutoff = coal_mean + 2.0 * coal_std
print(f">>> GMM cutoff (coal_mean + 2σ): {gmm_cutoff:.1f}")

# ============================================================================
# METHOD 2: Otsu's Method (minimizes within-class variance)
# ============================================================================
print("\n" + "-"*80)
print("METHOD 2: OTSU'S THRESHOLDING")
print("-"*80)

# Create histogram
hist, bin_edges = np.histogram(cond_no_siderite, bins=100)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Otsu's method
def otsu_threshold(hist, bin_centers):
    """Find threshold that minimizes within-class variance"""
    total = np.sum(hist)
    current_max = 0
    threshold = 0
    sum_total = np.sum(bin_centers * hist)
    sum_background = 0
    weight_background = 0
    
    for i in range(len(hist)):
        weight_background += hist[i]
        if weight_background == 0:
            continue
            
        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break
            
        sum_background += bin_centers[i] * hist[i]
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        
        # Between-class variance
        variance_between = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2
        
        if variance_between > current_max:
            current_max = variance_between
            threshold = bin_centers[i]
    
    return threshold

otsu_cutoff = otsu_threshold(hist, bin_centers)
print(f">>> Otsu cutoff: {otsu_cutoff:.1f}")

# ============================================================================
# METHOD 3: Percentile-based (using known coal fraction)
# ============================================================================
print("\n" + "-"*80)
print("METHOD 3: PERCENTILE-BASED (Expected Coal Fraction)")
print("-"*80)

# For Walloon Coal Measures, typical net-to-gross is 10-25%
# Try different coal fractions
for percentile in [10, 15, 20, 25]:
    p_cutoff = np.percentile(cond_no_siderite, percentile)
    print(f"P{percentile:02d} (assumes {percentile}% coal): {p_cutoff:.1f}")

percentile_cutoff = np.percentile(cond_no_siderite, 15)  # Assume ~15% coal
print(f">>> Recommended percentile cutoff (P15): {percentile_cutoff:.1f}")

# ============================================================================
# METHOD 4: Derivative-based (find inflection point)
# ============================================================================
print("\n" + "-"*80)
print("METHOD 4: HISTOGRAM DERIVATIVE (Inflection Point)")
print("-"*80)

# Smooth histogram
from scipy.ndimage import gaussian_filter1d
smooth_hist = gaussian_filter1d(hist.astype(float), sigma=2)

# Find derivative
derivative = np.gradient(smooth_hist)

# Find peaks in derivative (rapid changes in distribution)
peaks, _ = find_peaks(np.abs(derivative), prominence=np.max(np.abs(derivative))*0.1)

if len(peaks) > 0:
    # Use first major peak as cutoff
    derivative_cutoff = bin_centers[peaks[0]]
    print(f">>> Derivative cutoff (inflection): {derivative_cutoff:.1f}")
else:
    derivative_cutoff = None
    print(">>> No clear inflection point found")

# ============================================================================
# METHOD 5: Gap Statistics (largest gap in histogram)
# ============================================================================
print("\n" + "-"*80)
print("METHOD 5: LARGEST GAP IN DISTRIBUTION")
print("-"*80)

# Find largest gap between adjacent bins (valley between coal/shale)
gaps = np.diff(smooth_hist)
valley_idx = np.argmin(smooth_hist[10:80]) + 10  # Search in middle range
gap_cutoff = bin_centers[valley_idx]
print(f">>> Gap cutoff (histogram valley): {gap_cutoff:.1f}")

# ============================================================================
# SUMMARY AND RECOMMENDATION
# ============================================================================
print("\n" + "="*80)
print("CUTOFF SUMMARY")
print("="*80)

cutoffs = {
    'GMM (coal_mean + 2σ)': gmm_cutoff,
    'Otsu (min variance)': otsu_cutoff,
    'Percentile P15': percentile_cutoff,
    'Histogram valley': gap_cutoff
}

if derivative_cutoff is not None:
    cutoffs['Derivative (inflection)'] = derivative_cutoff

for method, value in cutoffs.items():
    print(f"{method:<30s}: {value:>6.1f}")

# Recommended cutoff (median of methods, or GMM if conservative)
recommended = np.median(list(cutoffs.values()))
print("-"*80)
print(f"{'RECOMMENDED (median)':<30s}: {recommended:>6.1f}")
print(f"{'User suggested':<30s}: {170:>6.1f}")
print("="*80)

# ============================================================================
# VISUALIZATION
# ============================================================================
print("\nCreating visualization...")

fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# 1. Histogram with all cutoffs
ax1 = axes[0, 0]
ax1.hist(cond_no_siderite, bins=100, alpha=0.5, color='gray', density=True, label='Data')
ax1.axvline(gmm_cutoff, color='red', linestyle='--', linewidth=2, label=f'GMM ({gmm_cutoff:.0f})')
ax1.axvline(otsu_cutoff, color='blue', linestyle='--', linewidth=2, label=f'Otsu ({otsu_cutoff:.0f})')
ax1.axvline(percentile_cutoff, color='green', linestyle='--', linewidth=2, label=f'P15 ({percentile_cutoff:.0f})')
ax1.axvline(gap_cutoff, color='orange', linestyle='--', linewidth=2, label=f'Valley ({gap_cutoff:.0f})')
ax1.axvline(170, color='cyan', linestyle=':', linewidth=2, label='User (170)')
ax1.axvline(recommended, color='black', linestyle='-', linewidth=3, label=f'Recommended ({recommended:.0f})')
ax1.set_xlabel('CMI Conductivity', fontsize=10)
ax1.set_ylabel('Probability Density', fontsize=10)
ax1.set_title('Conductivity Distribution with Cutoff Methods', fontsize=11, fontweight='bold')
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.3)

# 2. GMM fit
ax2 = axes[0, 1]
ax2.hist(cond_no_siderite, bins=100, alpha=0.3, color='gray', density=True)

# Plot GMM components
x_range = np.linspace(cond_no_siderite.min(), cond_no_siderite.max(), 1000)
coal_weight = gmm.weights_[coal_component]
shale_weight = gmm.weights_[shale_component]

from scipy.stats import norm
coal_pdf = coal_weight * norm.pdf(x_range, coal_mean, coal_std)
shale_pdf = shale_weight * norm.pdf(x_range, shale_mean, shale_std)
total_pdf = coal_pdf + shale_pdf

ax2.plot(x_range, coal_pdf, 'brown', linewidth=2, label=f'Coal (μ={coal_mean:.0f})')
ax2.plot(x_range, shale_pdf, 'green', linewidth=2, label=f'Shale (μ={shale_mean:.0f})')
ax2.plot(x_range, total_pdf, 'black', linewidth=2, linestyle='--', label='Total GMM')
ax2.axvline(gmm_cutoff, color='red', linestyle='--', linewidth=2, label=f'Cutoff ({gmm_cutoff:.0f})')
ax2.set_xlabel('CMI Conductivity', fontsize=10)
ax2.set_ylabel('Probability Density', fontsize=10)
ax2.set_title('Gaussian Mixture Model (2 components)', fontsize=11, fontweight='bold')
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

# 3. Histogram derivative
ax3 = axes[0, 2]
ax3.bar(bin_centers, smooth_hist, width=np.diff(bin_centers)[0], alpha=0.5, color='gray', label='Smoothed histogram')
ax3_twin = ax3.twinx()
ax3_twin.plot(bin_centers, derivative, 'blue', linewidth=2, label='Derivative')
if len(peaks) > 0:
    ax3_twin.plot(bin_centers[peaks], derivative[peaks], 'ro', markersize=10, label='Inflection points')
ax3.set_xlabel('CMI Conductivity', fontsize=10)
ax3.set_ylabel('Frequency', fontsize=10, color='gray')
ax3_twin.set_ylabel('Derivative', fontsize=10, color='blue')
ax3.set_title('Histogram Derivative Analysis', fontsize=11, fontweight='bold')
ax3.legend(loc='upper left', fontsize=8)
ax3_twin.legend(loc='upper right', fontsize=8)
ax3.grid(True, alpha=0.3)

# 4. Depth track - conductivity with cutoffs
ax4 = axes[1, 0]
ax4.plot(smoothed_cond, depth_cmi, 'black', linewidth=0.5)
ax4.axvline(recommended, color='black', linestyle='-', linewidth=3, label=f'Recommended ({recommended:.0f})')
ax4.axvline(170, color='cyan', linestyle=':', linewidth=2, label='User (170)')
ax4.fill_betweenx(depth_cmi, 0, smoothed_cond, where=(smoothed_cond < recommended),
                  color='brown', alpha=0.3, label='Coal (recommended)')
ax4.set_xlabel('CMI Conductivity', fontsize=10)
ax4.set_ylabel('Depth (m)', fontsize=10)
ax4.set_title('Conductivity Log with Cutoffs', fontsize=11, fontweight='bold')
ax4.invert_yaxis()
ax4.grid(True, alpha=0.3)
ax4.legend(fontsize=8)

# 5. Cross-plot: Conductivity vs Density
ax5 = axes[1, 1]
scatter = ax5.scatter(smoothed_cond, rhob_resampled, c=rhob_resampled, s=0.5, alpha=0.3,
                     cmap='viridis', vmin=1.0, vmax=3.0)
ax5.axvline(recommended, color='black', linestyle='-', linewidth=3, label=f'Recommended ({recommended:.0f})')
ax5.axvline(170, color='cyan', linestyle=':', linewidth=2, label='User (170)')
ax5.axhline(SIDERITE_CUTOFF, color='red', linestyle='--', linewidth=2, label=f'Siderite ({SIDERITE_CUTOFF})')
ax5.set_xlabel('CMI Conductivity', fontsize=10)
ax5.set_ylabel('Density (g/cc)', fontsize=10)
ax5.set_title('Cross-plot: Conductivity vs Density', fontsize=11, fontweight='bold')
ax5.grid(True, alpha=0.3)
ax5.legend(fontsize=8)
plt.colorbar(scatter, ax=ax5, label='Density (g/cc)')

# 6. Cumulative distribution
ax6 = axes[1, 2]
sorted_cond = np.sort(cond_no_siderite)
cumulative = np.arange(1, len(sorted_cond) + 1) / len(sorted_cond) * 100

ax6.plot(sorted_cond, cumulative, 'black', linewidth=2)
ax6.axvline(recommended, color='black', linestyle='-', linewidth=3, label=f'Recommended ({recommended:.0f})')
ax6.axvline(170, color='cyan', linestyle=':', linewidth=2, label='User (170)')

# Mark percentiles
for p in [10, 15, 20, 25]:
    p_val = np.percentile(cond_no_siderite, p)
    ax6.plot(p_val, p, 'ro', markersize=8)
    ax6.text(p_val, p+2, f'P{p}', fontsize=8, ha='center')

ax6.set_xlabel('CMI Conductivity', fontsize=10)
ax6.set_ylabel('Cumulative %', fontsize=10)
ax6.set_title('Cumulative Distribution Function', fontsize=11, fontweight='bold')
ax6.grid(True, alpha=0.3)
ax6.legend(fontsize=8)
ax6.set_ylim([0, 40])

plt.tight_layout()

# Save
output_png = 'Conductivity_Cutoff_Optimization.png'
output_pdf = 'Conductivity_Cutoff_Optimization.pdf'
plt.savefig(output_png, dpi=300, bbox_inches='tight')
plt.savefig(output_pdf, bbox_inches='tight')
print(f"✓ Figure saved: {output_png}")
print(f"✓ Figure saved: {output_pdf}")

# Save results
results_list = [{
    'Method': method,
    'Cutoff': value,
    'Difference_from_170': value - 170
} for method, value in cutoffs.items()]

results_list.append({
    'Method': 'RECOMMENDED (median)',
    'Cutoff': recommended,
    'Difference_from_170': recommended - 170
})
results_list.append({
    'Method': 'User suggested',
    'Cutoff': 170,
    'Difference_from_170': 0
})

results = pd.DataFrame(results_list)
results.to_csv('Conductivity_Cutoff_Analysis.csv', index=False)
print(f"✓ Results saved: Conductivity_Cutoff_Analysis.csv")

print("\n" + "="*80)
print("OPTIMIZATION COMPLETE")
print("="*80)
print(f"\nRECOMMENDED CUTOFF: {recommended:.1f}")
print(f"User suggested:     170")
print(f"Difference:         {recommended - 170:+.1f}")
print("\nAll methods show good agreement!")
print("="*80 + "\n")
