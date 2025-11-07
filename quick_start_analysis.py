"""
CSG Quick Start Interpretation - Anya 105
Focus: Upper Juandah Coal Measures to Top of Eurombah Formation

This script performs:
1. Load LAS file and formation tops
2. Extract zone of interest (Upper Juandah to Eurombah top)
3. Coal identification using CSG criteria
4. Net coal calculation
5. Ash content estimation
6. Basic petrophysical summary
7. Industry-standard log plot
"""

import lasio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')

print("="*80)
print("CSG QUICK START INTERPRETATION - ANYA 105")
print("Zone: Upper Juandah Coal Measures to Top of Eurombah Formation")
print("="*80)

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================
print("\n[1/7] Loading LAS file and formation tops...")

# Load LAS file
las_file = "Raw dataset/qgc_anya_105_mai_mfe_mss_mpd_mdn_hires.las"
las = lasio.read(las_file)

# Convert to DataFrame
df = las.df().reset_index()
print(f"  ✓ Loaded {len(df)} data points")
print(f"  ✓ Available curves: {list(df.columns)}")

# Load formation tops
tops = pd.read_csv("Anya_105_Well_Tops.csv")
print(f"\n  Formation Tops:")
print(tops[['Formation', 'Depth_MDRT_m']].to_string(index=False))

# ============================================================================
# STEP 2: DEFINE ZONE OF INTEREST
# ============================================================================
print("\n[2/7] Defining zone of interest...")

# Get depths for zone boundaries
top_depth = tops[tops['Formation'] == 'Upper Juandah Coal Measures']['Depth_MDRT_m'].values[0]
base_depth = tops[tops['Formation'] == 'Eurombah Formation']['Depth_MDRT_m'].values[0]

print(f"  Top: Upper Juandah Coal Measures @ {top_depth:.2f} m")
print(f"  Base: Eurombah Formation @ {base_depth:.2f} m")
print(f"  Interval: {base_depth - top_depth:.2f} m")

# Filter data to zone of interest
df_zone = df[(df['DEPT'] >= top_depth) & (df['DEPT'] <= base_depth)].copy()
print(f"  ✓ Extracted {len(df_zone)} data points in zone")

# ============================================================================
# STEP 3: IDENTIFY REQUIRED CURVES
# ============================================================================
print("\n[3/7] Identifying and mapping log curves...")

# Common curve naming conventions
curve_map = {}

# Direct mapping for this specific LAS file
curve_map = {
    'DEPTH': 'DEPT',
    'GR': 'GRGC',          # MCG Gamma Ray
    'RHOB': 'HDEN',        # Vectar Processed Density (better quality)
    'RHOB_ALT': 'DEN',     # Compensated Density (backup)
    'NPHI': 'NPOR',        # Base Neutron Porosity (in %)
    'PE': 'PDPE',          # Photoelectric Factor
    'RT': 'RTAO',          # Array Resistivity
    'DT': 'DT35',          # Compensated Sonic
    'CALI': 'CLDC',        # Density Caliper
    'DCOR': 'DCOR',        # Density Correction
}

# Check which curves exist
for log_type, curve_name in list(curve_map.items()):
    if curve_name not in df_zone.columns:
        print(f"  ⚠ {curve_name} not found for {log_type}")

print(f"  Mapped curves:")
for log_type, curve_name in curve_map.items():
    print(f"    {log_type:8s} -> {curve_name}")

# Rename curves for easier access
for log_type, curve_name in curve_map.items():
    if curve_name in df_zone.columns and log_type != curve_name:
        df_zone[log_type] = df_zone[curve_name]

# Convert NPHI from % to fraction if needed
if 'NPHI' in df_zone.columns:
    # Check if values are in percentage (>1)
    if df_zone['NPHI'].max() > 1.0:
        df_zone['NPHI'] = df_zone['NPHI'] / 100.0
        print(f"  ℹ Converted NPHI from % to fraction")

# ============================================================================
# STEP 4: COAL IDENTIFICATION
# ============================================================================
print("\n[4/7] Identifying coal seams using CSG criteria...")

# CSG Coal Detection Criteria
# 1. Density < 1.8 g/cc (coal is less dense than clastics)
# 2. Neutron > 0.30 (high hydrogen content)
# 3. Gamma Ray < 60 API (low radioactivity)
# 4. PE < 0.5 (if available - low atomic number)

coal_flag = np.zeros(len(df_zone), dtype=bool)

# Check which criteria we can apply
criteria_met = []

if 'RHOB' in df_zone.columns:
    rhob_flag = df_zone['RHOB'] < 1.8  # Changed from 2.0 to 1.8
    coal_flag = coal_flag | rhob_flag
    criteria_met.append('RHOB < 1.8')
    print(f"  ✓ Density criterion: {rhob_flag.sum()} points")

if 'NPHI' in df_zone.columns:
    nphi_flag = df_zone['NPHI'] > 0.30
    if len(criteria_met) > 0:
        coal_flag = coal_flag & nphi_flag
    else:
        coal_flag = nphi_flag
    criteria_met.append('NPHI > 0.30')
    print(f"  ✓ Neutron criterion: {nphi_flag.sum()} points")

if 'GR' in df_zone.columns:
    gr_flag = df_zone['GR'] < 60
    if len(criteria_met) > 0:
        coal_flag = coal_flag & gr_flag
    else:
        coal_flag = gr_flag
    criteria_met.append('GR < 60')
    print(f"  ✓ Gamma Ray criterion: {gr_flag.sum()} points")

if 'PE' in df_zone.columns:
    pe_flag = df_zone['PE'] < 0.5
    coal_flag = coal_flag & pe_flag
    criteria_met.append('PE < 0.5')
    print(f"  ✓ PE criterion: {pe_flag.sum()} points")

df_zone['COAL_FLAG'] = coal_flag
print(f"\n  Combined coal detection: {coal_flag.sum()} points ({100*coal_flag.sum()/len(df_zone):.1f}%)")
print(f"  Criteria used: {' AND '.join(criteria_met)}")

# ============================================================================
# STEP 5: CALCULATE ASH CONTENT
# ============================================================================
print("\n[5/7] Calculating ash content...")

if 'RHOB' in df_zone.columns:
    # Ash content from density
    # ASH% = (RHOB - RHO_coal) / (RHO_ash - RHO_coal) * 100
    
    RHO_COAL = 1.35  # Pure coal density (g/cc)
    RHO_ASH = 2.65   # Mineral matter density (g/cc)
    
    df_zone['ASH_PCT'] = ((df_zone['RHOB'] - RHO_COAL) / (RHO_ASH - RHO_COAL)) * 100
    
    # Limit to reasonable range (0-100%)
    df_zone['ASH_PCT'] = df_zone['ASH_PCT'].clip(0, 100)
    
    # Calculate for coal intervals only
    coal_ash = df_zone.loc[df_zone['COAL_FLAG'], 'ASH_PCT']
    print(f"  ✓ Ash content calculated")
    print(f"    Average ash in coal intervals: {coal_ash.mean():.1f}%")
    print(f"    Min ash: {coal_ash.min():.1f}%")
    print(f"    Max ash: {coal_ash.max():.1f}%")
else:
    print("  ⚠ RHOB not available - cannot calculate ash content")
    df_zone['ASH_PCT'] = np.nan

# ============================================================================
# STEP 6: COAL QUALITY CLASSIFICATION
# ============================================================================
print("\n[6/7] Classifying coal quality...")

df_zone['COAL_QUALITY'] = 'Non-coal'

if 'RHOB' in df_zone.columns:
    # High quality (Bright coal): RHOB < 1.5, ASH < 20%
    bright_coal = df_zone['COAL_FLAG'] & (df_zone['RHOB'] < 1.5)
    df_zone.loc[bright_coal, 'COAL_QUALITY'] = 'Bright Coal'
    
    # Medium quality (Dull coal): RHOB 1.5-1.8, ASH 20-40%
    dull_coal = df_zone['COAL_FLAG'] & (df_zone['RHOB'] >= 1.5) & (df_zone['RHOB'] < 1.8)
    df_zone.loc[dull_coal, 'COAL_QUALITY'] = 'Dull Coal'
    
    # Low quality (Carbonaceous): RHOB 1.8-2.0, ASH 40-60%
    carb_shale = df_zone['COAL_FLAG'] & (df_zone['RHOB'] >= 1.8)
    df_zone.loc[carb_shale, 'COAL_QUALITY'] = 'Carbonaceous'
    
    print(f"  Bright Coal:  {bright_coal.sum()} points ({100*bright_coal.sum()/len(df_zone):.1f}%)")
    print(f"  Dull Coal:    {dull_coal.sum()} points ({100*dull_coal.sum()/len(df_zone):.1f}%)")
    print(f"  Carbonaceous: {carb_shale.sum()} points ({100*carb_shale.sum()/len(df_zone):.1f}%)")

# ============================================================================
# STEP 7: NET COAL CALCULATION
# ============================================================================
print("\n[7/7] Calculating net coal thickness...")

# Net coal cutoffs
NET_COAL_CUTOFF = {
    'RHOB_MAX': 1.8,       # Density < 1.8 (changed from 2.0)
    'ASH_MAX': 50,         # Ash < 50%
    'GR_MAX': 60,          # GR < 60 API
}

df_zone['NET_COAL'] = df_zone['COAL_FLAG'].copy()

# Apply additional cutoffs if ash is available
if 'ASH_PCT' in df_zone.columns:
    df_zone['NET_COAL'] = df_zone['NET_COAL'] & (df_zone['ASH_PCT'] < NET_COAL_CUTOFF['ASH_MAX'])

# Calculate thickness (assuming 0.1524 m sampling - typical for wireline)
depth_diff = df_zone['DEPTH'].diff().median()
print(f"  Average sampling interval: {depth_diff:.4f} m")

net_coal_thickness = df_zone['NET_COAL'].sum() * depth_diff
gross_thickness = base_depth - top_depth
ntg_ratio = net_coal_thickness / gross_thickness

print(f"\n  RESULTS:")
print(f"  {'='*60}")
print(f"  Gross Interval:      {gross_thickness:.2f} m")
print(f"  Net Coal Thickness:  {net_coal_thickness:.2f} m")
print(f"  Net-to-Gross:        {ntg_ratio:.1%}")
print(f"  {'='*60}")

# Identify individual coal seams
seams = []
in_seam = False
seam_start = None

for idx, row in df_zone.iterrows():
    if row['NET_COAL'] and not in_seam:
        # Start of new seam
        in_seam = True
        seam_start = row['DEPTH']
    elif not row['NET_COAL'] and in_seam:
        # End of seam
        in_seam = False
        seam_end = row['DEPTH']
        thickness = seam_end - seam_start
        if thickness > 0.3:  # Minimum 0.3m thick
            seams.append({
                'top': seam_start,
                'base': seam_end,
                'thickness': thickness
            })

print(f"\n  Individual Coal Seams (>0.3m thick): {len(seams)}")
for i, seam in enumerate(seams, 1):
    print(f"    Seam {i}: {seam['top']:.2f} - {seam['base']:.2f} m ({seam['thickness']:.2f} m)")

# ============================================================================
# STEP 8: CREATE SUMMARY TABLE
# ============================================================================
print("\n" + "="*80)
print("PETROPHYSICAL SUMMARY")
print("="*80)

summary_data = {
    'Parameter': [
        'Top Depth (MDRT)',
        'Base Depth (MDRT)',
        'Gross Interval',
        'Net Coal',
        'Net-to-Gross',
        'Number of Seams',
        'Avg Coal Density',
        'Avg Ash Content',
        'Coal Quality Ratio'
    ],
    'Value': [
        f"{top_depth:.2f} m",
        f"{base_depth:.2f} m",
        f"{gross_thickness:.2f} m",
        f"{net_coal_thickness:.2f} m",
        f"{ntg_ratio:.1%}",
        f"{len(seams)}",
        f"{df_zone.loc[df_zone['NET_COAL'], 'RHOB'].mean():.3f} g/cc" if 'RHOB' in df_zone.columns else 'N/A',
        f"{df_zone.loc[df_zone['NET_COAL'], 'ASH_PCT'].mean():.1f}%" if 'ASH_PCT' in df_zone.columns else 'N/A',
        f"{bright_coal.sum() / (bright_coal.sum() + dull_coal.sum()):.1%}" if 'RHOB' in df_zone.columns else 'N/A'
    ]
}

summary_df = pd.DataFrame(summary_data)
print(summary_df.to_string(index=False))

# ============================================================================
# STEP 9: SAVE RESULTS
# ============================================================================
print("\n" + "="*80)
print("SAVING RESULTS")
print("="*80)

# Save processed data
output_csv = "Anya_105_Upper_Juandah_to_Eurombah_Analysis.csv"
df_zone.to_csv(output_csv, index=False)
print(f"  ✓ Processed data saved to: {output_csv}")

# Save coal seam inventory
seams_df = pd.DataFrame(seams)
if len(seams) > 0:
    seams_df['seam_number'] = range(1, len(seams) + 1)
    seams_output = "Anya_105_Coal_Seam_Inventory.csv"
    seams_df.to_csv(seams_output, index=False)
    print(f"  ✓ Coal seam inventory saved to: {seams_output}")

# Save summary
summary_df.to_csv("Anya_105_Petrophysical_Summary.csv", index=False)
print(f"  ✓ Summary saved to: Anya_105_Petrophysical_Summary.csv")

print("\n" + "="*80)
print("✓ QUICK START ANALYSIS COMPLETE!")
print("="*80)
print("\nNext step: Run 'plot_logs.py' to create log display")
