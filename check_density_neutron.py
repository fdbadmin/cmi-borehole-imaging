"""
Quick check of density-neutron crossover display
"""
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("Anya_105_Upper_Juandah_to_Eurombah_Analysis.csv")

# Sample a portion to check
sample = df[(df['DEPTH'] > 470) & (df['DEPTH'] < 485)].copy()

print("DENSITY-NEUTRON CHECK")
print("="*60)
print("\nSample data around coal zone (478-479m):")
print(sample[['DEPTH', 'RHOB', 'NPHI', 'GR', 'PE', 'COAL_FLAG']].to_string(index=False))

print("\n" + "="*60)
print("SCALE CHECK:")
print("="*60)
print(f"Density (RHOB) range in zone: {df['RHOB'].min():.3f} to {df['RHOB'].max():.3f} g/cc")
print(f"Neutron (NPHI) range in zone: {df['NPHI'].min():.3f} to {df['NPHI'].max():.3f} v/v")

print("\n" + "="*60)
print("CROSSOVER INTERPRETATION:")
print("="*60)
print("For coal zones, we expect:")
print("  - Low density (< 1.8 g/cc)")
print("  - High neutron (> 0.30 or 30%)")
print("  - On reversed neutron scale: curves SEPARATE (gas indication)")
print("\nCurrent display:")
print("  - Density: 1.95 → 2.95 g/cc (left to right)")
print("  - Neutron: 0.45 → -0.15 v/v (right to left, REVERSED)")
print("\n⚠️  ISSUE: Density scale starts at 1.95 g/cc")
print("   Coal at 1.3-1.8 g/cc will be OFF THE LEFT EDGE!")
print("\nRECOMMENDATION:")
print("  - Density: 1.5 → 2.5 g/cc (better for coal)")
print("  - OR: 1.0 → 3.0 g/cc (full range including coal)")
