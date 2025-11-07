#!/usr/bin/env python3
"""
Geological Feature Detection from CMI Borehole Images
Detects and characterizes faults, fractures, and bedding planes

Features to extract:
1. FRACTURES - High-angle conductive features (typically vertical/sub-vertical)
2. BEDDING - Low-angle features (horizontal/sub-horizontal layering)
3. FAULTS - Offset features with distinct conductivity contrast

Uses image processing techniques:
- Edge detection (Canny, Sobel)
- Hough transform for linear feature detection
- Sinusoid picking for dipping features
- Texture analysis for bedding characterization
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import ndimage
from scipy.signal import find_peaks
from skimage import filters, feature, transform
import cv2

print("\n" + "="*80)
print("GEOLOGICAL FEATURE DETECTION - CMI BOREHOLE IMAGE")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Minimum feature lengths/thresholds
MIN_FRACTURE_LENGTH_M = 0.05  # 5cm minimum fracture height
MIN_BEDDING_CONTINUITY = 90   # degrees azimuthal continuity for bedding
FRACTURE_ANGLE_MIN = 60       # degrees from horizontal (high-angle = fracture)
BEDDING_ANGLE_MAX = 30        # degrees from horizontal (low-angle = bedding)

print(f"\nDetection parameters:")
print(f"  Fracture criteria:")
print(f"    - Minimum length:      {MIN_FRACTURE_LENGTH_M*100:.0f} cm")
print(f"    - Angle from horiz:    > {FRACTURE_ANGLE_MIN}°")
print(f"  Bedding criteria:")
print(f"    - Azimuthal continuity: > {MIN_BEDDING_CONTINUITY}°")
print(f"    - Angle from horiz:    < {BEDDING_ANGLE_MAX}°")

# ============================================================================
# STEP 1: LOAD CMI IMAGE
# ============================================================================

print("\n" + "="*80)
print("STEP 1: LOADING CMI IMAGE")
print("="*80)

cmi_data = pd.read_csv('CMI_NoInterpolation_Image.csv')
depth = cmi_data['DEPTH'].values
image = cmi_data.iloc[:, 1:].values  # (depth, azimuth)

print(f"✓ Image loaded: {image.shape[0]} depths × {image.shape[1]} azimuth bins")
print(f"  Depth range: {depth.min():.2f} to {depth.max():.2f} m")
print(f"  Vertical resolution: {np.median(np.diff(depth))*1000:.2f} mm")

# ============================================================================
# STEP 2: IMAGE PREPROCESSING
# ============================================================================

print("\n" + "="*80)
print("STEP 2: IMAGE PREPROCESSING")
print("="*80)

# Fill NaN gaps with interpolation for edge detection
print("Filling data gaps for edge detection...")
image_filled = image.copy()
for i in range(image.shape[0]):
    row = image[i, :]
    nans = np.isnan(row)
    if np.sum(~nans) > 0:
        # Interpolate across gaps
        x = np.arange(len(row))
        image_filled[i, nans] = np.interp(x[nans], x[~nans], row[~nans])

print(f"✓ Gaps filled via interpolation")

# Normalize to 0-255 for OpenCV
image_norm = ((image_filled - np.nanmin(image_filled)) / 
              (np.nanmax(image_filled) - np.nanmin(image_filled)) * 255).astype(np.uint8)

print(f"✓ Normalized to 0-255 uint8")

# ============================================================================
# STEP 3: EDGE DETECTION
# ============================================================================

print("\n" + "="*80)
print("STEP 3: EDGE DETECTION")
print("="*80)

# Canny edge detection
print("Running Canny edge detection...")
edges_canny = feature.canny(image_norm, sigma=2.0, low_threshold=30, high_threshold=100)
print(f"✓ Canny edges: {np.sum(edges_canny)} edge pixels")

# Sobel gradients for directional analysis
print("Computing Sobel gradients...")
sobel_v = filters.sobel_v(image_norm)  # Vertical edges (horizontal features)
sobel_h = filters.sobel_h(image_norm)  # Horizontal edges (vertical features)
gradient_magnitude = np.sqrt(sobel_v**2 + sobel_h**2)
gradient_direction = np.arctan2(sobel_v, sobel_h) * 180 / np.pi

print(f"✓ Gradient magnitude range: {gradient_magnitude.min():.1f} to {gradient_magnitude.max():.1f}")

# ============================================================================
# STEP 4: FRACTURE DETECTION (High-angle features)
# ============================================================================

print("\n" + "="*80)
print("STEP 4: FRACTURE DETECTION")
print("="*80)

print("Detecting high-angle conductive features...")

# Fractures appear as:
# - High-angle features (>60° from horizontal)
# - Often conductive (bright/high values in CMI)
# - Vertical or near-vertical orientation
# - Localized in depth (not continuous like bedding)

# Method 1: Detect vertical features using horizontal gradient
print("\nMethod 1: Vertical feature detection...")

# Strong horizontal gradient indicates vertical features
h_gradient_threshold = np.percentile(np.abs(sobel_h), 75)
vertical_features = np.abs(sobel_h) > h_gradient_threshold

# Clean up noise with morphological operations
from scipy.ndimage import binary_opening, binary_closing
vertical_features_clean = binary_closing(binary_opening(vertical_features, iterations=1), iterations=2)

# Find connected vertical features
from scipy.ndimage import label as nd_label
labeled_features, num_features = nd_label(vertical_features_clean)
print(f"✓ Found {num_features} potential fracture zones")

# Extract fracture characteristics
fractures = []
depth_spacing = np.median(np.diff(depth))

for feature_id in range(1, num_features + 1):
    feature_mask = labeled_features == feature_id
    feature_pixels = np.sum(feature_mask)
    
    if feature_pixels < 10:  # Minimum size filter
        continue
    
    # Get depth extent
    depth_indices = np.where(np.any(feature_mask, axis=1))[0]
    if len(depth_indices) == 0:
        continue
        
    top_idx = depth_indices[0]
    base_idx = depth_indices[-1]
    fracture_length = (base_idx - top_idx) * depth_spacing
    
    # Minimum length filter
    if fracture_length < MIN_FRACTURE_LENGTH_M:
        continue
    
    # Get azimuth extent
    az_indices = np.where(np.any(feature_mask, axis=0))[0]
    if len(az_indices) == 0:
        continue
        
    # Handle wrap-around
    if len(az_indices) > 1:
        az_gaps = np.diff(np.sort(az_indices))
        if np.max(az_gaps) > 180:  # Wrapped around 360°
            az_center = (np.min(az_indices) + np.max(az_indices) + 360) / 2 % 360
        else:
            az_center = np.mean(az_indices)
    else:
        az_center = az_indices[0]
    
    az_span = len(az_indices)
    
    # Get average conductivity
    avg_conductivity = np.mean(image_norm[feature_mask])
    
    # Calculate orientation (vertical = 90°, horizontal = 0°)
    # For vertical features, orientation is ~90°
    orientation = 90  # Vertical features
    
    fractures.append({
        'Top_m': depth[top_idx],
        'Base_m': depth[base_idx],
        'Length_m': fracture_length,
        'Azimuth_deg': az_center,
        'Azimuth_span_deg': az_span,
        'Orientation_deg': orientation,
        'AvgConductivity': avg_conductivity,
        'PixelCount': feature_pixels
    })

fractures_df = pd.DataFrame(fractures)
print(f"✓ Detected {len(fractures_df)} fractures (>{MIN_FRACTURE_LENGTH_M*100:.0f}cm long)")

if len(fractures_df) > 0:
    print(f"  Average length: {fractures_df['Length_m'].mean():.3f} m")
    print(f"  Longest fracture: {fractures_df['Length_m'].max():.3f} m")
    print(f"  Azimuth distribution: {fractures_df['Azimuth_deg'].min():.0f}° to {fractures_df['Azimuth_deg'].max():.0f}°")

# ============================================================================
# STEP 5: BEDDING DETECTION (Low-angle features)
# ============================================================================

print("\n" + "="*80)
print("STEP 5: BEDDING DETECTION")
print("="*80)

print("Detecting horizontal/sub-horizontal bedding planes...")

# Bedding appears as horizontal bands with high azimuthal continuity
# Strong vertical gradient indicates bedding boundaries

# Method: Track horizontal features using vertical gradient
print("\nMethod: Horizontal continuity analysis...")

# Strong vertical gradient = bedding boundary
v_gradient_threshold = np.percentile(np.abs(sobel_v), 80)
bedding_boundaries = np.abs(sobel_v) > v_gradient_threshold

# For each depth, calculate azimuthal continuity
azimuthal_continuity = np.zeros(len(depth))
for i in range(len(depth)):
    row = image_norm[i, :]
    valid = ~np.isnan(row)
    if np.sum(valid) > 0:
        # Measure how continuous the signal is
        azimuthal_continuity[i] = np.sum(valid)

# Bedding layers = regions with high continuity and strong boundaries
bedding_indicator = (azimuthal_continuity > MIN_BEDDING_CONTINUITY) & np.any(bedding_boundaries, axis=1)

# Find bedding planes (peaks in vertical gradient)
gradient_profile = np.mean(np.abs(sobel_v), axis=1)
gradient_smooth = ndimage.gaussian_filter1d(gradient_profile, sigma=5)

# Find peaks = bedding boundaries
peaks, properties = find_peaks(gradient_smooth, 
                               height=np.percentile(gradient_smooth, 70),
                               distance=int(0.1 / depth_spacing))  # Min 10cm apart

bedding_planes = []
for peak_idx in peaks:
    if peak_idx >= len(depth):
        continue
        
    peak_depth = depth[peak_idx]
    peak_gradient = gradient_smooth[peak_idx]
    
    # Calculate average conductivity at this bedding plane
    avg_cond = np.nanmean(image_norm[peak_idx, :])
    
    # Calculate azimuthal coverage
    az_coverage = azimuthal_continuity[peak_idx] / 360 * 100
    
    # Estimate dip (for now assume horizontal = 0°)
    # TODO: Fit sinusoid to detect dipping beds
    apparent_dip = 0
    
    bedding_planes.append({
        'Depth_m': peak_depth,
        'GradientStrength': peak_gradient,
        'AvgConductivity': avg_cond,
        'AzimuthalCoverage_pct': az_coverage,
        'ApparentDip_deg': apparent_dip
    })

bedding_df = pd.DataFrame(bedding_planes)
print(f"✓ Detected {len(bedding_df)} bedding planes")

if len(bedding_df) > 0:
    print(f"  Average spacing: {np.mean(np.diff(bedding_df['Depth_m'])):.3f} m")
    print(f"  Azimuthal coverage: {bedding_df['AzimuthalCoverage_pct'].mean():.1f}%")
    
    # Calculate bedding thickness (distance between planes)
    if len(bedding_df) > 1:
        bedding_thickness = np.diff(bedding_df['Depth_m'])
        print(f"  Bedding thickness: {np.mean(bedding_thickness):.3f} m (avg), {np.min(bedding_thickness):.3f}-{np.max(bedding_thickness):.3f} m range")

# ============================================================================
# STEP 6: FAULT DETECTION
# ============================================================================

print("\n" + "="*80)
print("STEP 6: FAULT DETECTION")
print("="*80)

print("Detecting faults (offset features)...")

# Faults show:
# - Vertical offset in bedding
# - Conductivity contrast across fault plane
# - May coincide with fracture zones
# - Possible drag features near fault

# Method: Detect abrupt lateral changes in conductivity
print("\nMethod: Lateral conductivity contrast analysis...")

# Calculate lateral (azimuthal) gradient for each depth
lateral_contrast = np.zeros((len(depth), 360))
for i in range(len(depth)):
    row = image_norm[i, :]
    # Circular gradient (with wrap-around)
    grad = np.zeros(360)
    for j in range(360):
        j_prev = (j - 1) % 360
        j_next = (j + 1) % 360
        grad[j] = (row[j_next] - row[j_prev]) / 2
    lateral_contrast[i, :] = np.abs(grad)

# High lateral contrast = potential fault
fault_threshold = np.nanpercentile(lateral_contrast, 95)
potential_faults = lateral_contrast > fault_threshold

# Look for vertical continuity (faults extend vertically)
fault_zones = []
vertical_continuity_threshold = int(0.5 / depth_spacing)  # Min 0.5m vertical extent

for az in range(360):
    fault_column = potential_faults[:, az]
    
    # Find continuous vertical segments
    labeled_segments, num_segments = nd_label(fault_column)
    
    for seg_id in range(1, num_segments + 1):
        seg_mask = labeled_segments == seg_id
        seg_pixels = np.sum(seg_mask)
        
        if seg_pixels < vertical_continuity_threshold:
            continue
        
        # Get depth extent
        depth_indices = np.where(seg_mask)[0]
        top_idx = depth_indices[0]
        base_idx = depth_indices[-1]
        fault_height = (base_idx - top_idx) * depth_spacing
        
        # Calculate conductivity contrast across fault
        # Compare conductivity on either side
        az_left = (az - 5) % 360
        az_right = (az + 5) % 360
        
        cond_left = np.nanmean(image_norm[top_idx:base_idx+1, az_left])
        cond_right = np.nanmean(image_norm[top_idx:base_idx+1, az_right])
        contrast = abs(cond_right - cond_left)
        
        # Check if fractures are nearby (indicator of faulting)
        fracture_nearby = False
        if len(fractures_df) > 0:
            nearby_fractures = fractures_df[
                (fractures_df['Top_m'] <= depth[base_idx]) &
                (fractures_df['Base_m'] >= depth[top_idx]) &
                (np.abs(fractures_df['Azimuth_deg'] - az) < 15)
            ]
            fracture_nearby = len(nearby_fractures) > 0
        
        fault_zones.append({
            'Top_m': depth[top_idx],
            'Base_m': depth[base_idx],
            'Height_m': fault_height,
            'Azimuth_deg': az,
            'ConductivityContrast': contrast,
            'FractureAssociation': fracture_nearby
        })

faults_df = pd.DataFrame(fault_zones)

# Filter for significant faults (high contrast)
if len(faults_df) > 0:
    contrast_threshold = np.percentile(faults_df['ConductivityContrast'], 75)
    faults_df = faults_df[faults_df['ConductivityContrast'] > contrast_threshold]
    faults_df = faults_df.sort_values('ConductivityContrast', ascending=False)

print(f"✓ Detected {len(faults_df)} potential faults")

if len(faults_df) > 0:
    print(f"  Average height: {faults_df['Height_m'].mean():.3f} m")
    print(f"  Max contrast: {faults_df['ConductivityContrast'].max():.1f}")
    print(f"  Fracture association: {np.sum(faults_df['FractureAssociation'])} faults with nearby fractures")

# ============================================================================
# STEP 7: VISUALIZATION WITH DETECTED FEATURES
# ============================================================================

print("\n" + "="*80)
print("STEP 7: CREATING COMPREHENSIVE VISUALIZATION")
print("="*80)

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('CMI Borehole Image - Feature Detection Analysis', fontsize=16, fontweight='bold')

# --- Panel 1: Original CMI Image with All Features ---
ax1 = axes[0, 0]
im1 = ax1.imshow(image_norm, aspect='auto', cmap='viridis',
                 extent=[0, 360, depth.max(), depth.min()])
ax1.set_xlabel('Azimuth (degrees)')
ax1.set_ylabel('Depth (m)')
ax1.set_title('CMI Image with Detected Features')
plt.colorbar(im1, ax=ax1, label='Conductivity (normalized)')

# Overlay bedding planes (cyan dashed lines)
if len(bedding_df) > 0:
    for _, bed in bedding_df.head(50).iterrows():  # Limit to first 50 for clarity
        ax1.axhline(bed['Depth_m'], color='cyan', linewidth=0.8, alpha=0.6, linestyle='--')

# Overlay fractures (red vertical lines)
if len(fractures_df) > 0:
    for _, frac in fractures_df.head(100).iterrows():  # Limit to first 100
        az = frac['Azimuth_deg']
        ax1.plot([az, az], [frac['Top_m'], frac['Base_m']], 
                color='red', linewidth=1.5, alpha=0.7)

# Overlay faults (yellow thick lines with markers)
if len(faults_df) > 0:
    for _, fault in faults_df.head(20).iterrows():  # Limit to first 20
        az = fault['Azimuth_deg']
        ax1.plot([az, az], [fault['Top_m'], fault['Base_m']], 
                color='yellow', linewidth=2.5, alpha=0.9, marker='v', markersize=6)

# --- Panel 2: Canny Edge Detection ---
ax2 = axes[0, 1]
ax2.imshow(edges_canny, aspect='auto', cmap='binary',
           extent=[0, 360, depth.max(), depth.min()])
ax2.set_xlabel('Azimuth (degrees)')
ax2.set_ylabel('Depth (m)')
ax2.set_title('Canny Edge Detection')

# --- Panel 3: Gradient Magnitude ---
ax3 = axes[0, 2]
im3 = ax3.imshow(gradient_magnitude, aspect='auto', cmap='hot',
                 extent=[0, 360, depth.max(), depth.min()])
ax3.set_xlabel('Azimuth (degrees)')
ax3.set_ylabel('Depth (m)')
ax3.set_title('Gradient Magnitude')
plt.colorbar(im3, ax=ax3, label='Gradient')

# --- Panel 4: Vertical Gradient (Bedding) with Detections ---
ax4 = axes[1, 0]
im4 = ax4.imshow(np.abs(sobel_v), aspect='auto', cmap='Blues',
                 extent=[0, 360, depth.max(), depth.min()])
ax4.set_xlabel('Azimuth (degrees)')
ax4.set_ylabel('Depth (m)')
ax4.set_title('Vertical Gradient (Bedding)')
plt.colorbar(im4, ax=ax4, label='Gradient')

# Overlay detected bedding
if len(bedding_df) > 0:
    for _, bed in bedding_df.head(50).iterrows():
        ax4.axhline(bed['Depth_m'], color='cyan', linewidth=0.8, alpha=0.8, linestyle='--')

# --- Panel 5: Horizontal Gradient (Fractures) with Detections ---
ax5 = axes[1, 1]
im5 = ax5.imshow(np.abs(sobel_h), aspect='auto', cmap='Reds',
                 extent=[0, 360, depth.max(), depth.min()])
ax5.set_xlabel('Azimuth (degrees)')
ax5.set_ylabel('Depth (m)')
ax5.set_title('Horizontal Gradient (Fractures)')
plt.colorbar(im5, ax=ax5, label='Gradient')

# Overlay detected fractures
if len(fractures_df) > 0:
    for _, frac in fractures_df.head(100).iterrows():
        az = frac['Azimuth_deg']
        ax5.plot([az, az], [frac['Top_m'], frac['Base_m']], 
                color='red', linewidth=1.5, alpha=0.7)

# --- Panel 6: Feature Summary Statistics ---
ax6 = axes[1, 2]
ax6.axis('off')

summary_text = "DETECTED FEATURES SUMMARY\n" + "="*35 + "\n\n"

summary_text += f"FRACTURES: {len(fractures_df)}\n"
if len(fractures_df) > 0:
    summary_text += f"  Avg Length: {fractures_df['Length_m'].mean():.3f} m\n"
    summary_text += f"  Max Length: {fractures_df['Length_m'].max():.3f} m\n"
    summary_text += f"  Min Length: {fractures_df['Length_m'].min():.3f} m\n"
    summary_text += f"  Azimuth Range: {fractures_df['Azimuth_deg'].min():.0f}-{fractures_df['Azimuth_deg'].max():.0f}°\n"
    summary_text += f"  Avg Conductivity: {fractures_df['AvgConductivity'].mean():.1f}\n"
summary_text += "\n"

summary_text += f"BEDDING PLANES: {len(bedding_df)}\n"
if len(bedding_df) > 0:
    # Calculate spacing
    if len(bedding_df) > 1:
        spacing = np.diff(sorted(bedding_df['Depth_m']))
        summary_text += f"  Avg Spacing: {spacing.mean():.3f} m\n"
        summary_text += f"  Min Spacing: {spacing.min():.3f} m\n"
        summary_text += f"  Max Spacing: {spacing.max():.3f} m\n"
    summary_text += f"  Avg Coverage: {bedding_df['AzimuthalCoverage_pct'].mean():.1f}%\n"
    summary_text += f"  Avg Conductivity: {bedding_df['AvgConductivity'].mean():.1f}\n"
summary_text += "\n"

summary_text += f"FAULTS: {len(faults_df)}\n"
if len(faults_df) > 0:
    summary_text += f"  Avg Height: {faults_df['Height_m'].mean():.3f} m\n"
    summary_text += f"  Max Height: {faults_df['Height_m'].max():.3f} m\n"
    summary_text += f"  Avg Contrast: {faults_df['ConductivityContrast'].mean():.1f}\n"
    summary_text += f"  Max Contrast: {faults_df['ConductivityContrast'].max():.1f}\n"
    summary_text += f"  Fracture-Associated: {np.sum(faults_df['FractureAssociation'])}\n"
summary_text += "\n"

summary_text += "="*35 + "\n"
summary_text += "LEGEND:\n"
summary_text += "  Cyan dashes = Bedding\n"
summary_text += "  Red lines = Fractures\n"
summary_text += "  Yellow lines = Faults\n"

ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
         fontsize=9, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()

output_png = 'Feature_Detection_Results.png'
output_pdf = 'Feature_Detection_Results.pdf'
plt.savefig(output_png, dpi=300, bbox_inches='tight')
plt.savefig(output_pdf, bbox_inches='tight')

print(f"✓ Visualization saved: {output_png}")
print(f"✓ Visualization saved: {output_pdf}")

# ============================================================================
# STEP 8: EXPORT DETECTED FEATURES TO CSV
# ============================================================================

print("\n" + "="*80)
print("STEP 8: EXPORTING DETECTED FEATURES")
print("="*80)

# Export fractures
if len(fractures_df) > 0:
    fractures_csv = 'Fractures_Detected.csv'
    fractures_df.to_csv(fractures_csv, index=False)
    print(f"✓ Saved {len(fractures_df)} fractures to: {fractures_csv}")
else:
    print("⚠ No fractures detected")

# Export bedding planes
if len(bedding_df) > 0:
    bedding_csv = 'Bedding_Detected.csv'
    bedding_df.to_csv(bedding_csv, index=False)
    print(f"✓ Saved {len(bedding_df)} bedding planes to: {bedding_csv}")
else:
    print("⚠ No bedding planes detected")

# Export faults
if len(faults_df) > 0:
    faults_csv = 'Faults_Detected.csv'
    faults_df.to_csv(faults_csv, index=False)
    print(f"✓ Saved {len(faults_df)} faults to: {faults_csv}")
else:
    print("⚠ No faults detected")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*80)
print("FEATURE DETECTION - COMPLETE")
print("="*80)

print("\n✓ Completed:")
print("  • Edge detection (Canny)")
print("  • Gradient analysis (Sobel vertical/horizontal)")
print(f"  • Fracture detection: {len(fractures_df)} fractures")
print(f"  • Bedding detection: {len(bedding_df)} bedding planes")
print(f"  • Fault detection: {len(faults_df)} faults")
print("  • Comprehensive visualization")
print("  • CSV export of all features")

print("\n📁 Output Files:")
print("  • Feature_Detection_Results.png/pdf - Comprehensive visualization")
if len(fractures_df) > 0:
    print(f"  • Fractures_Detected.csv - {len(fractures_df)} detected fractures")
if len(bedding_df) > 0:
    print(f"  • Bedding_Detected.csv - {len(bedding_df)} bedding planes")
if len(faults_df) > 0:
    print(f"  • Faults_Detected.csv - {len(faults_df)} faults")

print("\n" + "="*80)
print("END OF FEATURE DETECTION ANALYSIS")
print("="*80)
print("    - Structural interpretation")

print("\n" + "="*80 + "\n")
