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

# High-angle features appear as vertical lines in unwrapped image
# Use Hough transform to detect lines

# TODO: Implement Hough line detection for fractures
# Fractures characteristics:
# - High angle (>60° from horizontal)
# - Often conductive (bright in CMI)
# - May show as sinusoids if dipping
# - Typically localized in depth (not continuous like bedding)

print("⚠ Fracture detection - TO BE IMPLEMENTED")
print("  Approach:")
print("  1. Hough line transform for high-angle features")
print("  2. Sinusoid fitting for dipping fractures")
print("  3. Conductivity contrast analysis")
print("  4. Classify natural vs induced fractures")

# ============================================================================
# STEP 5: BEDDING DETECTION (Low-angle features)
# ============================================================================

print("\n" + "="*80)
print("STEP 5: BEDDING DETECTION")
print("="*80)

print("Detecting horizontal/sub-horizontal bedding planes...")

# Bedding appears as horizontal bands with azimuthal continuity
# Approach: Horizontal gradient analysis

# Calculate horizontal continuity
horizontal_variance = np.var(image_norm, axis=1)  # Variance across azimuth
horizontal_range = np.nanmax(image_filled, axis=1) - np.nanmin(image_filled, axis=1)

print(f"✓ Horizontal variance computed")
print(f"  High variance indicates bedding: mean={np.mean(horizontal_variance):.1f}")

# Find depths with high horizontal coherence (bedding)
# Strong bedding = low variance + high gradient

# TODO: Implement bedding plane detection
print("⚠ Bedding detection - TO BE IMPLEMENTED")
print("  Approach:")
print("  1. Horizontal correlation analysis")
print("  2. Detect low-angle features (<30°)")
print("  3. Track azimuthal continuity")
print("  4. Identify bedding thickness and spacing")

# ============================================================================
# STEP 6: FAULT DETECTION
# ============================================================================

print("\n" + "="*80)
print("STEP 6: FAULT DETECTION")
print("="*80)

print("Detecting faults (offset features)...")

# Faults show:
# - Vertical offset in bedding
# - Conductivity contrast
# - Possible drag features
# - May coincide with fracture zones

# TODO: Implement fault detection
print("⚠ Fault detection - TO BE IMPLEMENTED")
print("  Approach:")
print("  1. Detect vertical offsets in bedding")
print("  2. Look for conductivity contrasts")
print("  3. Analyze fracture clustering")
print("  4. Estimate fault throw/displacement")

# ============================================================================
# STEP 7: VISUALIZATION
# ============================================================================

print("\n" + "="*80)
print("STEP 7: CREATING VISUALIZATION")
print("="*80)

fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Original image
ax1 = axes[0, 0]
im1 = ax1.imshow(image_norm, aspect='auto', cmap='YlOrBr_r',
                 extent=[0, 360, depth.max(), depth.min()])
ax1.set_xlabel('Azimuth (degrees)')
ax1.set_ylabel('Depth (m)')
ax1.set_title('Original CMI Image')
plt.colorbar(im1, ax=ax1, label='Conductivity')

# Canny edges
ax2 = axes[0, 1]
ax2.imshow(edges_canny, aspect='auto', cmap='binary',
           extent=[0, 360, depth.max(), depth.min()])
ax2.set_xlabel('Azimuth (degrees)')
ax2.set_ylabel('Depth (m)')
ax2.set_title('Canny Edge Detection')

# Gradient magnitude
ax3 = axes[0, 2]
im3 = ax3.imshow(gradient_magnitude, aspect='auto', cmap='hot',
                 extent=[0, 360, depth.max(), depth.min()])
ax3.set_xlabel('Azimuth (degrees)')
ax3.set_ylabel('Depth (m)')
ax3.set_title('Gradient Magnitude')
plt.colorbar(im3, ax=ax3, label='Gradient')

# Sobel vertical (bedding)
ax4 = axes[1, 0]
im4 = ax4.imshow(np.abs(sobel_v), aspect='auto', cmap='Blues',
                 extent=[0, 360, depth.max(), depth.min()])
ax4.set_xlabel('Azimuth (degrees)')
ax4.set_ylabel('Depth (m)')
ax4.set_title('Vertical Gradient (Bedding)')
plt.colorbar(im4, ax=ax4, label='Gradient')

# Sobel horizontal (fractures)
ax5 = axes[1, 1]
im5 = ax5.imshow(np.abs(sobel_h), aspect='auto', cmap='Reds',
                 extent=[0, 360, depth.max(), depth.min()])
ax5.set_xlabel('Azimuth (degrees)')
ax5.set_ylabel('Depth (m)')
ax5.set_title('Horizontal Gradient (Fractures)')
plt.colorbar(im5, ax=ax5, label='Gradient')

# Gradient direction
ax6 = axes[1, 2]
im6 = ax6.imshow(gradient_direction, aspect='auto', cmap='twilight',
                 extent=[0, 360, depth.max(), depth.min()],
                 vmin=-180, vmax=180)
ax6.set_xlabel('Azimuth (degrees)')
ax6.set_ylabel('Depth (m)')
ax6.set_title('Gradient Direction')
plt.colorbar(im6, ax=ax6, label='Angle (degrees)')

plt.tight_layout()

output_png = 'Feature_Detection_Initial.png'
output_pdf = 'Feature_Detection_Initial.pdf'
plt.savefig(output_png, dpi=300, bbox_inches='tight')
plt.savefig(output_pdf, bbox_inches='tight')

print(f"✓ Visualization saved: {output_png}")
print(f"✓ Visualization saved: {output_pdf}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("FEATURE DETECTION - INITIAL ANALYSIS COMPLETE")
print("="*80)

print("\nCompleted:")
print("  ✓ Edge detection (Canny)")
print("  ✓ Gradient analysis (Sobel vertical/horizontal)")
print("  ✓ Initial visualization")

print("\nNext Steps (TO BE IMPLEMENTED):")
print("  ⚠ Fracture detection:")
print("    - Hough line transform for high-angle features")
print("    - Sinusoid fitting for dipping fractures")
print("    - Natural vs induced fracture classification")
print("  ⚠ Bedding detection:")
print("    - Horizontal correlation tracking")
print("    - Bedding plane extraction")
print("    - Thickness and spacing analysis")
print("  ⚠ Fault detection:")
print("    - Vertical offset detection")
print("    - Fault throw estimation")
print("    - Structural interpretation")

print("\n" + "="*80 + "\n")
