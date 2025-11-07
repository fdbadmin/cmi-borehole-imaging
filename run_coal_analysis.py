#!/usr/bin/env python3
"""
SIMPLIFIED END-TO-END COAL ANALYSIS PIPELINE
Runs existing optimized scripts in sequence for coal seam analysis

This wrapper executes:
1. CMI image processing (cmi_no_interpolation.py) 
2. Coal seam detection (detect_coal_seams.py)
3. Generates summary report

Much faster than re-implementing - uses pre-tested, optimized code.
"""

import os
import sys
import subprocess
import pandas as pd
from datetime import datetime

print("\n" + "="*80)
print("COAL SEAM ANALYSIS PIPELINE - SIMPLIFIED WRAPPER")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Configuration
OUTPUT_DIR = 'Coal_Analysis_Results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read well tops for reservoir definition
print("Loading well tops...")
tops = pd.read_csv('Anya_105_Well_Tops.csv')
print(f"✓ Loaded {len(tops)} formations\n")

print("Reservoir definition (Walloon Coal Measures):")
walloon_formations = ['Upper Juandah Coal Measures', 'Lower Juandah Coal Measures', 
                      'Tangalooma Sandstone', 'Taroom Coal Measures']
for fm in walloon_formations:
    row = tops[tops['Formation'] == fm]
    if not row.empty:
        print(f"  {fm:<35s}: {row['Depth_MDRT_m'].values[0]:.1f} m")

reservoir_top = tops[tops['Formation'] == 'Upper Juandah Coal Measures']['Depth_MDRT_m'].values[0]
reservoir_base = tops[tops['Formation'] == 'Eurombah Formation']['Depth_MDRT_m'].values[0]
print(f"\n  Total reservoir zone: {reservoir_top:.1f} - {reservoir_base:.1f} m")

# ============================================================================
# STEP 1: Process CMI Image (if not already done)
# ============================================================================

print("\n" + "="*80)
print("STEP 1: CMI IMAGE PROCESSING")
print("="*80)

cmi_image_file = 'CMI_NoInterpolation_Image.csv'

if os.path.exists(cmi_image_file):
    print(f"✓ CMI image already exists: {cmi_image_file}")
    print("  Skipping CMI processing (delete file to regenerate)")
else:
    print("Running cmi_no_interpolation.py...")
    result = subprocess.run(
        ['python', 'cmi_no_interpolation.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ CMI processing complete")
    else:
        print("✗ CMI processing failed:")
        print(result.stderr)
        sys.exit(1)

# ============================================================================
# STEP 2: Detect Coal Seams
# ============================================================================

print("\n" + "="*80)
print("STEP 2: COAL SEAM DETECTION")
print("="*80)

print("Running detect_coal_seams.py...")
result = subprocess.run(
    ['python', 'detect_coal_seams.py'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✓ Coal detection complete")
    # Print summary from output
    for line in result.stdout.split('\n'):
        if 'Total coal seams detected:' in line or 'Total coal thickness:' in line or 'Net-to-Gross' in line:
            print(f"  {line.strip()}")
else:
    print("✗ Coal detection failed:")
    print(result.stderr)
    sys.exit(1)

# ============================================================================
# STEP 3: Copy Results to Output Directory
# ============================================================================

print("\n" + "="*80)
print("STEP 3: ORGANIZING RESULTS")
print("="*80)

# Copy key outputs
import shutil

files_to_copy = [
    ('Coal_Seams_Detected.csv', 'Coal_Seams_Final.csv'),
    ('Coal_Seams_Detected.png', 'Coal_Analysis_Summary.png'),
    ('Coal_Seams_Detected.pdf', 'Coal_Analysis_Summary.pdf'),
    ('Conductivity_Cutoff_Optimization.png', 'Conductivity_Cutoff_Optimization.png'),
    ('Conductivity_Cutoff_Optimization.pdf', 'Conductivity_Cutoff_Optimization.pdf'),
    ('Coal_Cutoff_Optimization.png', 'Coal_Cutoff_Optimization.png'),
    ('Coal_Cutoff_Optimization.pdf', 'Coal_Cutoff_Optimization.pdf')
]

copied_files = []
for src, dst in files_to_copy:
    if os.path.exists(src):
        dst_path = os.path.join(OUTPUT_DIR, dst)
        shutil.copy2(src, dst_path)
        copied_files.append(dst)
        print(f"✓ Copied: {dst}")

# ============================================================================
# STEP 4: Generate Summary Report
# ============================================================================

print("\n" + "="*80)
print("STEP 4: GENERATING SUMMARY REPORT")
print("="*80)

# Load coal seams
coal_seams = pd.read_csv('Coal_Seams_Detected.csv')

# Calculate statistics
total_coal = coal_seams['Thickness_m'].sum()
n_seams = len(coal_seams)
reservoir_thickness = reservoir_base - reservoir_top
ntg = total_coal / reservoir_thickness * 100

# Break down by formation
coal_by_formation = []
for fm in walloon_formations:
    row = tops[tops['Formation'] == fm]
    if row.empty:
        continue
    
    fm_top = row['Depth_MDRT_m'].values[0]
    
    # Get next formation depth for base
    fm_idx = tops[tops['Formation'] == fm].index[0]
    if fm_idx + 1 < len(tops):
        fm_base = tops.iloc[fm_idx + 1]['Depth_MDRT_m']
    else:
        fm_base = reservoir_base
    
    # Count coal in this formation
    fm_coal = coal_seams[(coal_seams['Top_m'] >= fm_top) & (coal_seams['Top_m'] < fm_base)]
    fm_thickness = fm_coal['Thickness_m'].sum()
    fm_ntg = fm_thickness / (fm_base - fm_top) * 100 if fm_base > fm_top else 0
    
    coal_by_formation.append({
        'Formation': fm,
        'Top_m': fm_top,
        'Base_m': fm_base,
        'Gross_Thickness_m': fm_base - fm_top,
        'Num_Seams': len(fm_coal),
        'Coal_Thickness_m': fm_thickness,
        'NTG_Percent': fm_ntg
    })

fm_summary = pd.DataFrame(coal_by_formation)

# Create summary document
summary_md = f"""# Coal Seam Analysis Summary
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Well:** Anya 105  
**Basin:** Surat Basin, Queensland, Australia  
**Reservoir:** Walloon Coal Measures

## Analysis Parameters

| Parameter | Value |
|-----------|-------|
| **Conductivity Cutoff** | 178 (Otsu-Median midpoint) |
| **Density Cutoff** | 2.5 g/cc (siderite exclusion) |
| **Minimum Seam Thickness** | 10 cm |
| **CMI Vertical Resolution** | 2 mm |
| **Density Log Resolution** | ~1 foot |

## Reservoir Summary

| Metric | Value |
|--------|-------|
| **Reservoir Top** | {reservoir_top:.1f} m |
| **Reservoir Base** | {reservoir_base:.1f} m |
| **Gross Thickness** | {reservoir_thickness:.1f} m |
| **Number of Coal Seams** | {n_seams} |
| **Total Coal Thickness** | {total_coal:.2f} m |
| **Net-to-Gross** | {ntg:.1f}% |
| **Average Seam Thickness** | {coal_seams['Thickness_m'].mean():.3f} m |
| **Thickest Seam** | {coal_seams['Thickness_m'].max():.3f} m |
| **Thinnest Seam** | {coal_seams['Thickness_m'].min():.3f} m |

## Coal Distribution by Formation

| Formation | Top (m) | Base (m) | Gross (m) | Seams | Coal (m) | NTG (%) |
|-----------|---------|----------|-----------|-------|----------|---------|
"""

for _, row in fm_summary.iterrows():
    summary_md += f"| {row['Formation']:<30s} | {row['Top_m']:>7.1f} | {row['Base_m']:>8.1f} | {row['Gross_Thickness_m']:>9.1f} | {row['Num_Seams']:>5d} | {row['Coal_Thickness_m']:>8.2f} | {row['NTG_Percent']:>7.1f} |\n"

summary_md += f"""
## Top 10 Thickest Seams

| Rank | Top (m) | Base (m) | Thickness (m) | Avg Conductivity |
|------|---------|----------|---------------|------------------|
"""

top_seams = coal_seams.nlargest(10, 'Thickness_m')
for i, (_, seam) in enumerate(top_seams.iterrows(), 1):
    summary_md += f"| {i:>4d} | {seam['Top_m']:>7.2f} | {seam['Base_m']:>8.2f} | {seam['Thickness_m']:>13.3f} | {seam['AvgConductivity']:>16.1f} |\n"

summary_md += f"""
## Files Generated

"""

for f in copied_files:
    summary_md += f"- `{f}`\n"

summary_md += """
## Methodology

### CMI Processing
1. Extract raw button data from DLIS file (176 buttons, 8 pads)
2. Apply speed correction (median 4.7 m/hr)
3. Normalize pads to global median
4. Azimuthal unwrapping with within-pad interpolation only
5. Logarithmic normalization (handles 0-19,460 MMHO range)

### Coal Detection
1. Calculate azimuthal average conductivity (44.3% coverage)
2. Apply 5cm Gaussian smoothing
3. Detect low conductivity zones (< 178)
4. Exclude siderite bands using density log (RHOB > 2.5 g/cc)
5. Filter connected regions > 10cm thick

### Cutoff Optimization
Conductivity cutoff (178) determined as midpoint between:
- **Otsu method**: 164.2 (minimizes within-class variance)
- **Median of methods**: 191.2 (consensus of 5 statistical methods)

This provides balanced detection: conservative enough to ensure high confidence,
aggressive enough to capture thin seams visible only in high-resolution CMI data.
"""

# Save summary
summary_file = os.path.join(OUTPUT_DIR, 'ANALYSIS_SUMMARY.md')
with open(summary_file, 'w') as f:
    f.write(summary_md)

print(f"✓ Summary report: {summary_file}")

# Save formation summary CSV
fm_csv = os.path.join(OUTPUT_DIR, 'Coal_by_Formation.csv')
fm_summary.to_csv(fm_csv, index=False)
print(f"✓ Formation summary: {fm_csv}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*80)
print("PIPELINE COMPLETE")
print("="*80)

print(f"\nReservoir: {reservoir_top:.1f} - {reservoir_base:.1f} m ({reservoir_thickness:.1f}m)")
print(f"\nCoal Summary:")
print(f"  • Seams detected:    {n_seams}")
print(f"  • Total coal:        {total_coal:.2f} m")
print(f"  • Net-to-Gross:      {ntg:.1f}%")

print(f"\nTop 3 Formations by Coal Content:")
top_formations = fm_summary.nlargest(3, 'Coal_Thickness_m')
for _, row in top_formations.iterrows():
    print(f"  • {row['Formation']:<30s}: {row['Coal_Thickness_m']:>6.2f}m ({row['NTG_Percent']:>4.1f}% NTG)")

print(f"\nOutput Directory: {OUTPUT_DIR}/")
print(f"  Files: {len(copied_files) + 2}")

print("\n" + "="*80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")
