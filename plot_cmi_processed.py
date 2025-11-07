#!/usr/bin/env python3
"""
Display Weatherford CMI Processed Images
Uses vendor-processed CMI_DYN and CMI_STAT channels
"""

from dlisio import dlis
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

print("\n" + "="*80)
print("WEATHERFORD CMI PROCESSED IMAGES")
print("="*80)

# Zone of interest
TOP_DEPTH = 233.3
BASE_DEPTH = 547.0

print(f"\nZone of Interest: {TOP_DEPTH}m to {BASE_DEPTH}m")

# Load DLIS file
dlis_file = 'Raw dataset/qgc_anya-105_mcg-cmi.dlis'

with dlis.load(dlis_file) as files:
    for f in files:
        frame = f.frames[0]
        print(f"\nLoading frame: {frame.name}")
        
        # Load all curves
        print("Loading data...")
        curves_data = frame.curves()
        depth = curves_data['DEPTH']
        
        # Load processed images
        cmi_dyn = curves_data['CMI_DYN']
        cmi_stat = curves_data['CMI_STAT']
        
        print(f"CMI_DYN shape: {cmi_dyn.shape}")
        print(f"CMI_STAT shape: {cmi_stat.shape}")
        
        # Filter to zone of interest
        zone_mask = (depth >= TOP_DEPTH) & (depth <= BASE_DEPTH)
        zone_depth = depth[zone_mask]
        zone_dyn = cmi_dyn[zone_mask]
        zone_stat = cmi_stat[zone_mask]
        
        print(f"\n✓ Depth samples in zone: {len(zone_depth)}")
        print(f"  Depth range: {zone_depth.min():.2f} to {zone_depth.max():.2f}m")
        print(f"  Sampling: {np.median(np.diff(zone_depth)):.4f}m")
        print(f"  Image dimensions: {zone_dyn.shape[0]} samples × {zone_dyn.shape[1]} azimuth bins")
        
        # Replace null values (-9999) with NaN
        zone_dyn[zone_dyn == -9999] = np.nan
        zone_stat[zone_stat == -9999] = np.nan
        
        # Statistics
        print(f"\nCMI_DYN (Dynamic Image) statistics:")
        print(f"  Range: [{np.nanmin(zone_dyn):.1f}, {np.nanmax(zone_dyn):.1f}]")
        print(f"  Mean: {np.nanmean(zone_dyn):.1f}")
        print(f"  Median: {np.nanmedian(zone_dyn):.1f}")
        print(f"  Valid data: {100*np.sum(~np.isnan(zone_dyn))/zone_dyn.size:.1f}%")
        
        print(f"\nCMI_STAT (Static Image) statistics:")
        print(f"  Range: [{np.nanmin(zone_stat):.1f}, {np.nanmax(zone_stat):.1f}]")
        print(f"  Mean: {np.nanmean(zone_stat):.1f}")
        print(f"  Median: {np.nanmedian(zone_stat):.1f}")
        print(f"  Valid data: {100*np.sum(~np.isnan(zone_stat))/zone_stat.size:.1f}%")
        
        # Create brown-to-yellow colormap for resistivity imaging
        # Low values (conductive/shale) = yellow
        # High values (resistive/coal) = brown
        colors = ['#8B4513', '#A0522D', '#CD853F', '#DEB887', '#F5DEB3', '#FFFFE0']
        coal_cmap = LinearSegmentedColormap.from_list('coal', colors[::-1])  # Reverse for conductivity
        
        print("\n" + "="*80)
        print("CREATING IMAGE PLOTS")
        print("="*80)
        
        # Create figure with 3 panels: Dynamic, Static, and Zoomed comparison
        fig = plt.figure(figsize=(24, 20))
        
        # Panel 1: CMI_DYN (Dynamic Image)
        ax1 = plt.subplot(1, 3, 1)
        
        extent = [0, 360, zone_depth.max(), zone_depth.min()]
        im1 = ax1.imshow(zone_dyn, aspect='auto', extent=extent,
                        cmap=coal_cmap, interpolation='bilinear',
                        vmin=0, vmax=255)
        
        ax1.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=10)
        ax1.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax1.set_title(f'CMI Dynamic Image\nAnya 105: {TOP_DEPTH}-{BASE_DEPTH}m',
                     fontweight='bold', fontsize=11, pad=10)
        ax1.set_xticks([0, 90, 180, 270, 360])
        ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='white')
        
        cbar1 = plt.colorbar(im1, ax=ax1, pad=0.02)
        cbar1.set_label('Image Intensity [0-255]', fontweight='bold', fontsize=9)
        
        # Panel 2: CMI_STAT (Static Image)
        ax2 = plt.subplot(1, 3, 2)
        
        im2 = ax2.imshow(zone_stat, aspect='auto', extent=extent,
                        cmap=coal_cmap, interpolation='bilinear',
                        vmin=0, vmax=255)
        
        ax2.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=10)
        ax2.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax2.set_title(f'CMI Static Image\nAnya 105: {TOP_DEPTH}-{BASE_DEPTH}m',
                     fontweight='bold', fontsize=11, pad=10)
        ax2.set_xticks([0, 90, 180, 270, 360])
        ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='white')
        
        cbar2 = plt.colorbar(im2, ax=ax2, pad=0.02)
        cbar2.set_label('Image Intensity [0-255]', fontweight='bold', fontsize=9)
        
        # Panel 3: Zoomed detail comparison
        ax3 = plt.subplot(1, 3, 3)
        
        zoom_center = 478.5
        zoom_range = 20.0
        zoom_mask = (zone_depth >= zoom_center - zoom_range/2) & (zone_depth <= zoom_center + zoom_range/2)
        
        zoom_depth = zone_depth[zoom_mask]
        zoom_stat = zone_stat[zoom_mask]
        
        extent_zoom = [0, 360, zoom_depth.max(), zoom_depth.min()]
        im3 = ax3.imshow(zoom_stat, aspect='auto', extent=extent_zoom,
                        cmap=coal_cmap, interpolation='bilinear',
                        vmin=0, vmax=255)
        
        ax3.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=10)
        ax3.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax3.set_title(f'Detail: {zoom_center-zoom_range/2:.1f}-{zoom_center+zoom_range/2:.1f}m\n({len(zoom_depth)} samples, 2mm resolution)',
                     fontweight='bold', fontsize=11, pad=10)
        ax3.set_xticks([0, 90, 180, 270, 360])
        ax3.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='white')
        
        cbar3 = plt.colorbar(im3, ax=ax3, pad=0.02)
        cbar3.set_label('Image Intensity [0-255]', fontweight='bold', fontsize=9)
        
        plt.suptitle('Weatherford CMI Processed Borehole Images\n(Brown=Resistive/Coal, Yellow=Conductive/Shale)',
                    fontsize=13, fontweight='bold', y=0.998)
        
        plt.tight_layout()
        
        # Save figure
        output_png = 'CMI_Processed_Images.png'
        plt.savefig(output_png, dpi=300, bbox_inches='tight')
        print(f"✓ Saved image to: {output_png}")
        
        output_pdf = 'CMI_Processed_Images.pdf'
        plt.savefig(output_pdf, bbox_inches='tight')
        print(f"✓ Saved image to: {output_pdf}")

        print("\n" + "="*80)
        print("✓ CMI PROCESSED IMAGES COMPLETE!")
        print("="*80)
        print("\nDeliverables:")
        print("  - CMI_Processed_Images.png/pdf")
        print("    * Panel 1: CMI_DYN (Dynamic Image)")
        print("    * Panel 2: CMI_STAT (Static Image)")
        print("    * Panel 3: Detail zoom (468.5-488.5m)")
        print("\nNotes:")
        print("  - These are VENDOR-PROCESSED images from Weatherford")
        print("  - Already normalized and calibrated (0-255 scale)")
        print("  - 360° azimuthal coverage (1° bins)")
        print("  - Full 2mm vertical resolution preserved")
        print("  - Dynamic = time-varying response")
        print("  - Static = steady-state response")
        print("="*80 + "\n")
