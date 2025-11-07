"""
Check available curves in LAS file and map them properly
"""

import lasio
import pandas as pd

las = lasio.read("Raw dataset/qgc_anya_105_mai_mfe_mss_mpd_mdn_hires.las")

print("="*80)
print("AVAILABLE CURVES IN LAS FILE")
print("="*80)

for curve in las.curves:
    print(f"\nCurve: {curve.mnemonic}")
    print(f"  Description: {curve.descr}")
    print(f"  Unit: {curve.unit}")
    print(f"  Sample: {curve.data[1000:1005]}")

print("\n" + "="*80)
print("LIKELY CURVE MAPPINGS FOR CSG ANALYSIS")
print("="*80)

# Analyze curve names
df = las.df().reset_index()

mappings = {
    'DEPT': 'Depth',
    'GRGC': 'Gamma Ray (corrected)',
    'SPCG': 'Spontaneous Potential',
    'NPOR': 'Neutron Porosity (likely)',
    'DENF': 'Density Formation (likely RHOB)',
    'HDEN': 'High-res Density (likely RHOB)',
    'DCOR': 'Density Correction',
    'PDPE': 'Photoelectric Factor',
    'DPOR': 'Density Porosity',
    'DT35': 'Sonic (Delta-T)',
    'DPRD': 'Deep Resistivity',
    'DPRS': 'Shallow Resistivity',
    'RTAO': 'Resistivity (another)',
}

for curve, description in mappings.items():
    if curve in df.columns:
        data = df[curve].dropna()
        if len(data) > 0:
            print(f"\n{curve:8s} ({description})")
            print(f"  Range: {data.min():.4f} to {data.max():.4f}")
            print(f"  Mean:  {data.mean():.4f}")
            print(f"  Unit:  {las.curves[curve].unit if curve in las.curves else 'unknown'}")
