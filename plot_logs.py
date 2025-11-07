"""
Create industry-standard log display for CSG interpretation
Focus: Upper Juandah Coal Measures to Eurombah Formation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("CREATING LOG DISPLAY")
print("="*80)

# Load processed data
df = pd.read_csv("Anya_105_Upper_Juandah_to_Eurombah_Analysis.csv")
tops = pd.read_csv("Anya_105_Well_Tops.csv")

# Get zone boundaries
top_depth = tops[tops['Formation'] == 'Upper Juandah Coal Measures']['Depth_MDRT_m'].values[0]
base_depth = tops[tops['Formation'] == 'Eurombah Formation']['Depth_MDRT_m'].values[0]

# Filter tops within zone
zone_tops = tops[(tops['Depth_MDRT_m'] >= top_depth) & (tops['Depth_MDRT_m'] <= base_depth)]

print(f"Creating log plot from {top_depth:.1f}m to {base_depth:.1f}m...")

# Create figure with 7 tracks
fig = plt.figure(figsize=(16, 12))
gs = GridSpec(1, 7, width_ratios=[0.5, 1, 1, 1.2, 1, 1, 0.8], wspace=0.3)

# Set overall title
fig.suptitle('Anya 105 - CSG Petrophysical Analysis\nUpper Juandah Coal Measures to Eurombah Formation', 
             fontsize=14, fontweight='bold', y=0.98)

# ============================================================================
# TRACK 1: DEPTH & FORMATIONS
# ============================================================================
ax1 = fig.add_subplot(gs[0])
ax1.set_ylim(base_depth, top_depth)
ax1.set_xlim(0, 1)
ax1.set_ylabel('Depth (m MDRT)', fontweight='bold')
ax1.yaxis.set_label_position('left')
ax1.yaxis.tick_left()
ax1.grid(True, alpha=0.3)

# Add formation labels
for idx, row in zone_tops.iterrows():
    depth = row['Depth_MDRT_m']
    formation = row['Formation'].replace(' Coal Measures', '\nCoal\nMeas.')
    formation = formation.replace(' Formation', '\nFm.')
    formation = formation.replace(' Sandstone', '\nSst.')
    
    ax1.axhline(depth, color='black', linewidth=2, linestyle='-')
    ax1.text(0.5, depth - 5, formation, ha='center', va='top', 
             fontsize=7, fontweight='bold', rotation=0)

ax1.set_xticks([])
ax1.set_title('Formation', fontsize=9, fontweight='bold')

# ============================================================================
# TRACK 2: GAMMA RAY & CALIPER (Industry Standard)
# ============================================================================
ax2 = fig.add_subplot(gs[1])
ax2.set_ylim(base_depth, top_depth)
ax2.set_xlim(0, 150)  # Standard GR range 0-150 API
ax2.set_xlabel('GR (API)', fontsize=8, fontweight='bold')
ax2.grid(True, alpha=0.2, which='both', linestyle='-', linewidth=0.5)
ax2.xaxis.set_label_position('top')
ax2.xaxis.tick_top()

# Plot GR with standard black color
if 'GR' in df.columns:
    ax2.plot(df['GR'], df['DEPTH'], 'black', linewidth=0.7, label='GR')
    # Shade clean zones (low GR - coal/sandstone)
    ax2.fill_betweenx(df['DEPTH'], 0, df['GR'], 
                      where=df['GR']<60, alpha=0.2, color='yellow')
    # Shade shale zones (high GR)
    ax2.fill_betweenx(df['DEPTH'], df['GR'], 150,
                      where=df['GR']>60, alpha=0.15, color='brown')

# Add caliper on secondary axis
ax2_cal = ax2.twiny()
ax2_cal.set_xlim(6, 16)  # Standard caliper range
ax2_cal.set_xlabel('Cal (in)', fontsize=8, fontweight='bold', color='black')
ax2_cal.tick_params(axis='x', labelcolor='black', labelsize=7)
ax2_cal.spines['top'].set_position(('outward', 25))

if 'CALI' in df.columns:
    ax2_cal.plot(df['CALI'], df['DEPTH'], color='#FF1493', linewidth=1.0, label='Cal')
    # Show bit size reference
    bit_size = 8.5  # 8.5" hole
    ax2_cal.axvline(bit_size, color='red', linestyle='--', linewidth=1.5, alpha=0.4)

ax2.set_title('Gamma Ray / Caliper', fontsize=9, fontweight='bold', pad=35)
ax2.set_yticklabels([])
ax2.tick_params(labelsize=7)

# ============================================================================
# TRACK 3: RESISTIVITY (Industry Standard)
# ============================================================================
ax3 = fig.add_subplot(gs[2])
ax3.set_ylim(base_depth, top_depth)
ax3.set_xlim(0.2, 2000)  # Standard log resistivity scale
ax3.set_xscale('log')
ax3.set_xlabel('Resistivity (ohmm)', fontsize=8, fontweight='bold')
ax3.grid(True, alpha=0.2, which='both', linestyle='-', linewidth=0.5)
ax3.xaxis.set_label_position('top')
ax3.xaxis.tick_top()

if 'RT' in df.columns:
    # Clip to reasonable range and plot with standard red color
    rt_plot = df['RT'].clip(0.2, 2000)
    ax3.plot(rt_plot, df['DEPTH'], color='red', linewidth=0.8, label='RT')

ax3.set_title('Resistivity', fontsize=9, fontweight='bold')
ax3.set_yticklabels([])
ax3.tick_params(labelsize=7)

# ============================================================================
# TRACK 4: DENSITY - NEUTRON (Industry Standard - Classic Crossover)
# ============================================================================
ax4 = fig.add_subplot(gs[3])
ax4.set_ylim(base_depth, top_depth)
ax4.set_xlim(1.5, 2.5)  # Extended range to include coal (1.3-1.8 g/cc)
ax4.set_xlabel('Density (g/cc)', fontsize=8, fontweight='bold', color='red')
ax4.tick_params(axis='x', labelcolor='red', labelsize=7)
ax4.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
ax4.xaxis.set_label_position('top')
ax4.xaxis.tick_top()

if 'RHOB' in df.columns:
    # Plot density with standard red color and red fill to left
    ax4.plot(df['RHOB'], df['DEPTH'], color='red', linewidth=0.8, label='RHOB')
    # Highlight coal density range (< 1.8 g/cc) - fill to left edge
    ax4.fill_betweenx(df['DEPTH'], 1.5, df['RHOB'],
                      where=df['RHOB']<1.8, alpha=0.25, color='red', 
                      interpolate=True, label='Coal ρb<1.8')

# Neutron on secondary axis (reversed for crossover display)
ax4_n = ax4.twiny()
ax4_n.set_xlim(0.45, -0.15)  # Reversed! Standard neutron range
ax4_n.set_xlabel('Neutron (v/v)', fontsize=8, fontweight='bold', color='blue')
ax4_n.tick_params(axis='x', labelcolor='blue', labelsize=7)
ax4_n.spines['top'].set_position(('outward', 25))

if 'NPHI' in df.columns:
    # Plot neutron with standard blue color and dashed line
    ax4_n.plot(df['NPHI'], df['DEPTH'], color='blue', linewidth=0.8, 
               linestyle='--', label='NPHI')
    # Show crossover zones (gas indicator - density < neutron when reversed)
    # In gas zones, the blue neutron line crosses over to the RIGHT of red density
    crossover = (df['RHOB'] < 2.3) & (df['NPHI'] < 0.40)
    
# Add reference lines for matrix points
ax4.axvline(2.65, color='gray', linestyle=':', linewidth=1, alpha=0.5)  # Quartz
ax4.axvline(2.71, color='gray', linestyle=':', linewidth=1, alpha=0.5)  # Calcite
ax4.axvline(1.8, color='darkred', linestyle='--', linewidth=1.5, alpha=0.7)  # Coal cutoff

ax4.set_title('Density-Neutron', fontsize=9, fontweight='bold', pad=35)
ax4.set_yticklabels([])
ax4.tick_params(labelsize=7)

# ============================================================================
# TRACK 5: PHOTOELECTRIC FACTOR (Industry Standard)
# ============================================================================
ax5 = fig.add_subplot(gs[4])
ax5.set_ylim(base_depth, top_depth)
ax5.set_xlim(0, 10)  # Standard PE range 0-10 b/e
ax5.set_xlabel('PE (b/e)', fontsize=8, fontweight='bold')
ax5.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
ax5.xaxis.set_label_position('top')
ax5.xaxis.tick_top()

if 'PE' in df.columns:
    # Plot PE with standard green/brown color
    ax5.plot(df['PE'], df['DEPTH'], color='green', linewidth=0.8, label='PE')
    # Highlight coal PE range (low PE)
    ax5.fill_betweenx(df['DEPTH'], 0, df['PE'],
                      where=df['PE']<2.0, alpha=0.25, color='green')
    
    # Add reference lines for common minerals
    ax5.axvline(1.81, color='gray', linestyle=':', linewidth=1, alpha=0.5)  # Quartz
    ax5.axvline(5.08, color='gray', linestyle=':', linewidth=1, alpha=0.5)  # Calcite
    ax5.axvline(0.35, color='darkgreen', linestyle='--', linewidth=1.5, alpha=0.7)  # Pure coal

ax5.set_title('Photoelectric', fontsize=9, fontweight='bold')
ax5.set_yticklabels([])
ax5.tick_params(labelsize=7)

# ============================================================================
# TRACK 6: ASH CONTENT (CSG-Specific)
# ============================================================================
ax6 = fig.add_subplot(gs[5])
ax6.set_ylim(base_depth, top_depth)
ax6.set_xlim(0, 100)
ax6.set_xlabel('Ash (%)', fontsize=8, fontweight='bold')
ax6.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
ax6.xaxis.set_label_position('top')
ax6.xaxis.tick_top()

if 'ASH_PCT' in df.columns:
    # Plot ash content with brown color
    ax6.plot(df['ASH_PCT'], df['DEPTH'], color='saddlebrown', linewidth=0.8, label='Ash')
    # Show quality zones with proper colors
    # Bright coal zone (low ash)
    ax6.fill_betweenx(df['DEPTH'], 0, df['ASH_PCT'],
                      where=(df['ASH_PCT']<20) & (df['COAL_FLAG']), 
                      alpha=0.3, color='gold', label='Bright')
    # Dull coal zone (medium ash)
    ax6.fill_betweenx(df['DEPTH'], df['ASH_PCT'], 100,
                      where=(df['ASH_PCT']>=20) & (df['ASH_PCT']<40) & (df['COAL_FLAG']), 
                      alpha=0.2, color='chocolate')
    
    # Add reference lines
    ax6.axvline(20, color='gold', linestyle='--', linewidth=1.5, alpha=0.7)
    ax6.axvline(40, color='chocolate', linestyle='--', linewidth=1.5, alpha=0.7)

ax6.set_title('Ash Content', fontsize=9, fontweight='bold')
ax6.set_yticklabels([])
ax6.tick_params(labelsize=7)

# ============================================================================
# TRACK 7: COAL FLAGS (Industry Standard)
# ============================================================================
ax7 = fig.add_subplot(gs[6])
ax7.set_ylim(base_depth, top_depth)
ax7.set_xlim(0, 3)
ax7.set_xticks([0.5, 1.5, 2.5])
ax7.set_xticklabels(['Coal', 'Net', 'Qual'], fontsize=7, rotation=0)
ax7.grid(True, alpha=0.2, axis='y', linestyle='-', linewidth=0.5)
ax7.xaxis.set_label_position('top')
ax7.xaxis.tick_top()

# Coal flag (black)
if 'COAL_FLAG' in df.columns:
    coal_x = df['COAL_FLAG'].astype(int) * 0.5 + 0.25
    ax7.fill_betweenx(df['DEPTH'], 0.25, coal_x, 
                      where=df['COAL_FLAG'], color='black', alpha=0.8)

# Net coal flag (dark green)
if 'NET_COAL' in df.columns:
    net_x = df['NET_COAL'].astype(int) * 0.5 + 1.25
    ax7.fill_betweenx(df['DEPTH'], 1.25, net_x,
                      where=df['NET_COAL'], color='darkgreen', alpha=0.8)

# Coal quality (color-coded)
if 'COAL_QUALITY' in df.columns:
    # Bright coal (gold)
    bright = (df['COAL_QUALITY'] == 'Bright Coal').astype(int) * 0.5 + 2.25
    ax7.fill_betweenx(df['DEPTH'], 2.25, bright,
                      where=df['COAL_QUALITY']=='Bright Coal', color='gold', alpha=0.8)
    
    # Dull coal (chocolate)
    dull = (df['COAL_QUALITY'] == 'Dull Coal').astype(int) * 0.5 + 2.25
    ax7.fill_betweenx(df['DEPTH'], 2.25, dull,
                      where=df['COAL_QUALITY']=='Dull Coal', color='chocolate', alpha=0.8)
    
    # Carbonaceous (brown)
    carb = (df['COAL_QUALITY'] == 'Carbonaceous').astype(int) * 0.5 + 2.25
    ax7.fill_betweenx(df['DEPTH'], 2.25, carb,
                      where=df['COAL_QUALITY']=='Carbonaceous', color='brown', alpha=0.8)

ax7.set_title('Flags', fontsize=9, fontweight='bold')
ax7.set_yticklabels([])
ax7.tick_params(labelsize=7)

# ============================================================================
# Add formation tops lines to all tracks
# ============================================================================
for ax in [ax2, ax3, ax4, ax5, ax6, ax7]:
    for idx, row in zone_tops.iterrows():
        ax.axhline(row['Depth_MDRT_m'], color='black', linewidth=1.5, linestyle='-', alpha=0.7)

# ============================================================================
# Add summary text box
# ============================================================================
summary_text = f"""
ANALYSIS SUMMARY
Zone: Upper Juandah to Eurombah
Gross: {base_depth - top_depth:.1f} m
Net Coal: {df['NET_COAL'].sum() * 0.025:.2f} m
NTG: {df['NET_COAL'].sum() / len(df):.1%}
Coal Seams: {len(pd.read_csv('Anya_105_Coal_Seam_Inventory.csv')) if pd.read_csv('Anya_105_Coal_Seam_Inventory.csv').shape[0] > 0 else 0}
"""

fig.text(0.02, 0.02, summary_text, fontsize=8, family='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Adjust layout
plt.tight_layout(rect=[0, 0.05, 1, 0.96])

# Save figure
output_file = "Anya_105_Log_Display.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✓ Log display saved to: {output_file}")

# Also save as PDF
output_pdf = "Anya_105_Log_Display.pdf"
plt.savefig(output_pdf, dpi=150, bbox_inches='tight')
print(f"✓ Log display saved to: {output_pdf}")

plt.show()

print("\n" + "="*80)
print("✓ LOG DISPLAY COMPLETE!")
print("="*80)
