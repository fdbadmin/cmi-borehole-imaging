#!/usr/bin/env python3
"""
Automatic Coal Seam Detection from CMI Image
Detects low-conductivity (low intensity) zones indicating coal seams
INCLUDES DENSITY FILTER TO EXCLUDE SIDERITE
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d, label
from scipy.signal import find_peaks
import lasio
import csv

print("\n" + "="*80)
print("AUTOMATIC COAL SEAM DETECTION FROM CMI IMAGE")
print("High-resolution CMI with density filter for siderite bands")
print("="*80)

# Detection parameters
CONDUCTIVITY_CUTOFF = 178  # Midpoint between Otsu (164.2) and Median (191.2)
SIDERITE_DENSITY_CUTOFF = 2.5  # g/cc - density above this indicates siderite (exclude)
MIN_THICKNESS = 0.10       # 10cm minimum seam thickness

print(f"\nDetection parameters:")
print(f"  • Conductivity cutoff: {CONDUCTIVITY_CUTOFF} (Otsu-Median midpoint)")
print(f"  • Siderite density cutoff: {SIDERITE_DENSITY_CUTOFF} g/cc (exclude RHOB > {SIDERITE_DENSITY_CUTOFF})")
print(f"  • Density log resolution: ~1 foot (only removes thick siderite bands)")
print(f"  • Minimum thickness:   {MIN_THICKNESS*100:.0f} cm")

# Load the processed CMI image
print("\nLoading processed CMI image...")
cmi_data = pd.read_csv('CMI_NoInterpolation_Image.csv')

depth = cmi_data['DEPTH'].values
image = cmi_data.iloc[:, 1:].values  # All columns except depth

print(f"✓ Image loaded: {image.shape[0]} depths × {image.shape[1]} azimuth bins")
print(f"  Depth range: {depth.min():.2f} to {depth.max():.2f}m")
print(f"  Sampling: {np.median(np.diff(depth))*1000:.2f}mm")

# Calculate azimuthal average (ignore NaN gaps)
print("\nCalculating azimuthal average conductivity...")
avg_conductivity = np.nanmean(image, axis=1)
valid_samples = np.sum(~np.isnan(image), axis=1)

print(f"✓ Average coverage: {np.mean(valid_samples)/image.shape[1]*100:.1f}%")
print(f"  Mean conductivity: {np.nanmean(avg_conductivity):.1f}")
print(f"  Std conductivity: {np.nanstd(avg_conductivity):.1f}")

# Load density log
print("\nLoading density log...")
las = lasio.read('Raw dataset/qgc_anya_105_mai_mfe_mss_mpd_mdn_hires.las')
depth_las = las['DEPT']
rhob = las['HDEN']
print(f"✓ Density log loaded: {len(depth_las)} samples")

# Resample density to CMI depth grid
print("Resampling density to CMI depth grid...")
rhob_resampled = np.interp(depth, depth_las, rhob)
print(f"✓ Density resampled to {len(rhob_resampled)} samples")

# Smooth the curve to reduce noise
print("\nSmoothing conductivity curve...")
window_samples = int(0.05 / np.median(np.diff(depth)))  # 5cm smoothing window
smoothed = gaussian_filter1d(avg_conductivity, sigma=window_samples)
print(f"✓ Smoothing window: {window_samples} samples ({window_samples * np.median(np.diff(depth))*100:.1f}cm)")

# Coal detection: Low conductivity zones, then filter out siderite
# Step 1: Detect all low-conductivity zones (high-resolution CMI)
print("\nDetecting coal seams from high-resolution CMI...")

print(f"\n  Conductivity threshold: {CONDUCTIVITY_CUTOFF}")

# Initial coal mask based on conductivity only
coal_mask_conductivity = smoothed < CONDUCTIVITY_CUTOFF
print(f"  Initial coal fraction (conductivity only): {np.sum(coal_mask_conductivity)/len(coal_mask_conductivity)*100:.1f}%")

# Step 2: Identify siderite bands from low-resolution density log
# Siderite has high density (> 2.5 g/cc) but can have low conductivity
print(f"\n  Siderite density threshold: > {SIDERITE_DENSITY_CUTOFF} g/cc")
siderite_mask = rhob_resampled > SIDERITE_DENSITY_CUTOFF
print(f"  Siderite fraction (to exclude): {np.sum(siderite_mask)/len(siderite_mask)*100:.1f}%")

# Step 3: Final coal mask = low conductivity AND NOT siderite
coal_mask = coal_mask_conductivity & ~siderite_mask
print(f"\n  Final coal fraction (after siderite removal): {np.sum(coal_mask)/len(coal_mask)*100:.1f}%")
print(f"  Removed by density filter: {np.sum(coal_mask_conductivity & siderite_mask)/len(coal_mask)*100:.2f}%")

# Label connected regions
labeled_zones, num_zones = label(coal_mask)
print(f"✓ Found {num_zones} potential coal zones")

# Extract coal seam intervals with thickness filter
coal_seams = []

for zone_id in range(1, num_zones + 1):
    zone_mask = labeled_zones == zone_id
    zone_indices = np.where(zone_mask)[0]
    
    top_idx = zone_indices[0]
    base_idx = zone_indices[-1]
    
    top_depth = depth[top_idx]
    base_depth = depth[base_idx]
    thickness = base_depth - top_depth
    
    if thickness >= MIN_THICKNESS:
        # Calculate average conductivity in this zone
        zone_cond = np.nanmean(smoothed[zone_mask])
        
        coal_seams.append({
            'Top_m': top_depth,
            'Base_m': base_depth,
            'Thickness_m': thickness,
            'AvgConductivity': zone_cond,
            'NumSamples': len(zone_indices)
        })

print(f"\n✓ Detected {len(coal_seams)} coal seams (>{MIN_THICKNESS*100:.0f}cm thick)")

# Sort by depth
coal_seams_df = pd.DataFrame(coal_seams)
coal_seams_df = coal_seams_df.sort_values('Top_m')

# Display summary
print("\n" + "-"*80)
print("COAL SEAM SUMMARY")
print("-"*80)
print(f"{'Top (m)':<10} {'Base (m)':<10} {'Thickness (m)':<15} {'Avg Cond':<12} {'Samples':<10}")
print("-"*80)

total_thickness = 0
for _, seam in coal_seams_df.iterrows():
    print(f"{seam['Top_m']:<10.2f} {seam['Base_m']:<10.2f} {seam['Thickness_m']:<15.3f} "
          f"{seam['AvgConductivity']:<12.1f} {seam['NumSamples']:<10.0f}")
    total_thickness += seam['Thickness_m']

print("-"*80)
print(f"Total coal thickness: {total_thickness:.2f}m")
print(f"Net-to-Gross: {total_thickness/(depth.max()-depth.min())*100:.1f}%")
print("-"*80)

# Save to CSV
output_file = 'Coal_Seams_Detected.csv'
coal_seams_df.to_csv(output_file, index=False)
print(f"\n✓ Coal seams saved to: {output_file}")

# Create visualization
print("\nCreating visualization...")
fig, axes = plt.subplots(1, 3, figsize=(16, 12))

# Track 1: CMI Image with coal seams highlighted
ax1 = axes[0]
im1 = ax1.imshow(image, aspect='auto', cmap='YlOrBr_r', 
                 extent=[0, 360, depth.max(), depth.min()],
                 vmin=0, vmax=255, interpolation='nearest')
ax1.set_xlabel('Azimuth (degrees)', fontsize=10)
ax1.set_ylabel('Depth (m)', fontsize=10)
ax1.set_title('CMI Image', fontsize=11, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Highlight coal seams
for _, seam in coal_seams_df.iterrows():
    ax1.axhspan(seam['Top_m'], seam['Base_m'], 
                color='cyan', alpha=0.2, zorder=10)
    ax1.text(5, (seam['Top_m'] + seam['Base_m'])/2, 
             f"{seam['Thickness_m']:.2f}m", 
             fontsize=8, color='cyan', fontweight='bold',
             va='center', bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))

plt.colorbar(im1, ax=ax1, label='Conductivity (normalized)')

# Track 2: Average conductivity curve with threshold
ax2 = axes[1]
ax2.plot(avg_conductivity, depth, 'gray', linewidth=0.5, alpha=0.5, label='Raw')
ax2.plot(smoothed, depth, 'black', linewidth=1.5, label='Smoothed')
ax2.axvline(CONDUCTIVITY_CUTOFF, color='red', linestyle='--', linewidth=2, 
           label=f'Coal threshold ({CONDUCTIVITY_CUTOFF})')

# Shade coal zones
for _, seam in coal_seams_df.iterrows():
    ax2.axhspan(seam['Top_m'], seam['Base_m'], 
                color='brown', alpha=0.3)

ax2.set_xlabel('Avg Conductivity', fontsize=10)
ax2.set_ylabel('Depth (m)', fontsize=10)
ax2.set_title('Average Conductivity', fontsize=11, fontweight='bold')
ax2.invert_yaxis()
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=8)

# Track 3: Coal flag and cumulative thickness
ax3 = axes[2]
coal_flag = coal_mask.astype(float)
ax3.fill_betweenx(depth, 0, coal_flag, color='brown', alpha=0.5, step='mid')
ax3.set_xlim(-0.1, 1.1)
ax3.set_xlabel('Coal Flag', fontsize=10)
ax3.set_ylabel('Depth (m)', fontsize=10)
ax3.set_title('Coal Detection', fontsize=11, fontweight='bold')
ax3.invert_yaxis()
ax3.grid(True, alpha=0.3)
ax3.set_xticks([0, 1])
ax3.set_xticklabels(['Shale', 'Coal'])

# Add thickness annotations
for _, seam in coal_seams_df.iterrows():
    mid_depth = (seam['Top_m'] + seam['Base_m']) / 2
    ax3.text(0.5, mid_depth, f"{seam['Thickness_m']:.2f}m", 
             fontsize=8, ha='center', va='center', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()

# Save figure
output_png = 'Coal_Seams_Detected.png'
output_pdf = 'Coal_Seams_Detected.pdf'
plt.savefig(output_png, dpi=300, bbox_inches='tight')
plt.savefig(output_pdf, bbox_inches='tight')
print(f"✓ Figure saved: {output_png}")
print(f"✓ Figure saved: {output_pdf}")

print("\n" + "="*80)
print("COAL SEAM DETECTION COMPLETE")
print("="*80)
print(f"\nSummary:")
print(f"  • Total coal seams detected: {len(coal_seams_df)}")
print(f"  • Total coal thickness: {total_thickness:.2f}m")
print(f"  • Net-to-Gross ratio: {total_thickness/(depth.max()-depth.min())*100:.1f}%")
print(f"  • Average seam thickness: {total_thickness/len(coal_seams_df):.3f}m")
print(f"  • Thickest seam: {coal_seams_df['Thickness_m'].max():.3f}m")
print(f"  • Thinnest seam: {coal_seams_df['Thickness_m'].min():.3f}m")
print("="*80 + "\n")
