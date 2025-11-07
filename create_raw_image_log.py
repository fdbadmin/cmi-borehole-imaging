#!/usr/bin/env python3
"""
Create CMI Borehole Image - No Interpolation
Display raw button measurements without azimuthal interpolation
"""

from dlisio import dlis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm

print("\n" + "="*80)
print("CREATING CMI BOREHOLE IMAGE - RAW DATA (NO INTERPOLATION)")
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
        azimuth = curves_data['AZIM']
        p1az = curves_data['P1AZ']
        
        # Filter to zone of interest
        zone_mask = (depth >= TOP_DEPTH) & (depth <= BASE_DEPTH)
        zone_depth = depth[zone_mask]
        zone_azimuth = azimuth[zone_mask]
        zone_p1az = p1az[zone_mask]
        
        print(f"✓ Depth samples in zone: {len(zone_depth)}")
        print(f"  Depth range: {zone_depth.min():.2f} to {zone_depth.max():.2f}m")
        print(f"  Sampling: {np.median(np.diff(zone_depth)):.4f}m")
        print(f"  Azimuth range: {np.nanmin(zone_azimuth):.1f}° to {np.nanmax(zone_azimuth):.1f}°")
        print(f"  P1 reference azimuth range: {np.nanmin(zone_p1az):.1f}° to {np.nanmax(zone_p1az):.1f}°")
        
        # Button pad names (8 pads × 2 rows = 16 channels)
        button_channels = [
            'BT1L', 'BT1U',  # Pad 1
            'BT2L', 'BT2U',  # Pad 2
            'BT3L', 'BT3U',  # Pad 3
            'BT4L', 'BT4U',  # Pad 4
            'BT5L', 'BT5U',  # Pad 5
            'BT6L', 'BT6U',  # Pad 6
            'BT7L', 'BT7U',  # Pad 7
            'BT8L', 'BT8U',  # Pad 8
        ]
        
        print(f"\n{'='*80}")
        print("EXTRACTING BUTTON ARRAYS")
        print(f"{'='*80}")
        
        # Storage for all button data
        all_buttons = []
        button_names = []
        
        for i, channel_name in enumerate(button_channels):
            # Get channel data
            channel_data = curves_data[channel_name]
            zone_data = channel_data[zone_mask]
            
            # Reshape from (N, 1, X) to (N, X)
            zone_data_2d = zone_data.squeeze()
            
            # Replace null values
            zone_data_2d[zone_data_2d == -9999] = np.nan
            zone_data_2d[zone_data_2d < 0] = np.nan
            
            # Append to collection
            all_buttons.append(zone_data_2d)
            
            # Track statistics
            valid_pct = 100 * np.sum(~np.isnan(zone_data_2d)) / zone_data_2d.size
            print(f"  {i+1:2d}. {channel_name:6s}: shape {zone_data_2d.shape}, "
                  f"range [{np.nanmin(zone_data_2d):7.1f}, {np.nanmax(zone_data_2d):7.1f}] MMHO, "
                  f"valid {valid_pct:5.1f}%")
        
        # Combine all buttons into single array - NO INTERPOLATION
        print(f"\n{'='*80}")
        print("ASSEMBLING RAW IMAGE")
        print(f"{'='*80}")
        
        raw_image = np.hstack(all_buttons)  # Just concatenate - no azimuth correction
        print(f"Raw image shape: {raw_image.shape}")
        print(f"  Depth samples: {raw_image.shape[0]}")
        print(f"  Total buttons: {raw_image.shape[1]}")
        print(f"  Vertical resolution: {np.median(np.diff(zone_depth))*1000:.1f} mm")
        
        # Statistics
        print(f"\nImage statistics:")
        print(f"  Min: {np.nanmin(raw_image):.2f} MMHO")
        print(f"  Max: {np.nanmax(raw_image):.2f} MMHO")
        print(f"  Mean: {np.nanmean(raw_image):.2f} MMHO")
        print(f"  Median: {np.nanmedian(raw_image):.2f} MMHO")
        
        # Create visualizations
        print(f"\n{'='*80}")
        print("CREATING RAW BOREHOLE IMAGE")
        print(f"{'='*80}")
        
        # Create brown-to-yellow colormap
        colors_list = [
            (0.2, 0.1, 0.0),   # Dark brown (coal/resistive)
            (0.4, 0.2, 0.1),   # Brown
            (0.6, 0.4, 0.2),   # Light brown
            (0.8, 0.6, 0.3),   # Tan
            (1.0, 0.9, 0.4),   # Yellow (shale/conductive)
        ]
        coal_cmap = LinearSegmentedColormap.from_list('coal_image', colors_list, N=256)
        
        # Industry standard processing: normalize and enhance contrast
        # 1. Remove zeros and nulls
        valid_data = raw_image[(raw_image > 0) & ~np.isnan(raw_image)]
        
        # 2. Calculate statistics on valid data
        p01 = np.nanpercentile(valid_data, 1)   # 1st percentile
        p05 = np.nanpercentile(valid_data, 5)   # 5th percentile
        p50 = np.nanpercentile(valid_data, 50)  # Median
        p95 = np.nanpercentile(valid_data, 95)  # 95th percentile
        p99 = np.nanpercentile(valid_data, 99)  # 99th percentile
        median = np.nanmedian(valid_data)
        mean = np.nanmean(valid_data)
        
        print(f"\nData statistics (valid data only):")
        print(f"  P01: {p01:.2f} MMHO")
        print(f"  P05: {p05:.2f} MMHO")
        print(f"  Median: {median:.2f} MMHO")
        print(f"  Mean: {mean:.2f} MMHO")
        print(f"  P95: {p95:.2f} MMHO")
        print(f"  P99: {p99:.2f} MMHO")
        
        # 3. Industry standard: use P05-P95 for better contrast (remove extreme outliers)
        vmin = max(p05, 0.1)  # Don't go below 0.1 for log scale
        vmax = p95
        
        print(f"\nColor scale (using P05-P95 for optimal contrast):")
        print(f"  Min: {vmin:.2f} MMHO")
        print(f"  Max: {vmax:.2f} MMHO")
        print(f"  Ratio: {vmax/vmin:.1f}x")
        
        # Simpler approach - just clip and use log scale
        # No histogram equalization (it was causing artifacts)
        clipped_image = np.clip(raw_image, vmin, vmax)
        clipped_image[raw_image <= 0] = np.nan  # Preserve invalid data as NaN
        
        # Create figure - 2 panels comparing raw and clipped
        fig = plt.figure(figsize=(20, 20))
        
        # Panel 1: Log scale with P05-P95 clipping
        ax1 = plt.subplot(1, 2, 1)
        
        extent = [0, raw_image.shape[1], zone_depth.max(), zone_depth.min()]
        im1 = ax1.imshow(clipped_image, aspect='auto', extent=extent,
                        cmap=coal_cmap, interpolation='nearest',
                        norm=LogNorm(vmin=vmin, vmax=vmax))
        
        ax1.set_xlabel('Button Number', fontweight='bold', fontsize=10)
        ax1.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax1.set_title(f'CMI Image Log (Log Scale P05-P95)\nAnya 105: {TOP_DEPTH}-{BASE_DEPTH}m',
                     fontweight='bold', fontsize=11, pad=10)
        
        # Add pad markers
        btn_idx = 0
        pad_positions = []
        pad_labels = []
        for i, channel_name in enumerate(button_channels):
            num_btns = all_buttons[i].shape[1]
            pad_positions.append(btn_idx + num_btns/2)
            pad_labels.append(channel_name)
            if i > 0:
                ax1.axvline(btn_idx, color='white', linestyle='-', linewidth=0.5, alpha=0.5)
            btn_idx += num_btns
        
        ax1.set_xticks(pad_positions)
        ax1.set_xticklabels(pad_labels, fontsize=7, rotation=45, ha='right')
        cbar1 = plt.colorbar(im1, ax=ax1, pad=0.02)
        cbar1.set_label('Conductivity [MMHO]', fontweight='bold', fontsize=9)
        ax1.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='white')
        
        # Panel 2: Zoomed detail
        ax2 = plt.subplot(1, 2, 2)
        
        zoom_center = 478.5
        zoom_range = 20.0
        zoom_mask = (zone_depth >= zoom_center - zoom_range/2) & (zone_depth <= zoom_center + zoom_range/2)
        
        zoom_depth = zone_depth[zoom_mask]
        zoom_image = clipped_image[zoom_mask, :]
        
        extent_zoom = [0, raw_image.shape[1], zoom_depth.max(), zoom_depth.min()]
        im2 = ax2.imshow(zoom_image, aspect='auto', extent=extent_zoom,
                        cmap=coal_cmap, interpolation='nearest',
                        norm=LogNorm(vmin=vmin, vmax=vmax))
        
        ax2.set_xlabel('Button Number', fontweight='bold', fontsize=10)
        ax2.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax2.set_title(f'Detail: {zoom_center-zoom_range/2:.1f}-{zoom_center+zoom_range/2:.1f}m\n({len(zoom_depth)} samples, 2mm resolution)',
                     fontweight='bold', fontsize=11, pad=10)
        
        btn_idx = 0
        for i, channel_name in enumerate(button_channels):
            num_btns = all_buttons[i].shape[1]
            if i > 0:
                ax2.axvline(btn_idx, color='white', linestyle='-', linewidth=0.5, alpha=0.5)
            btn_idx += num_btns
        
        ax2.set_xticks(pad_positions)
        ax2.set_xticklabels(pad_labels, fontsize=7, rotation=45, ha='right')
        cbar2 = plt.colorbar(im2, ax=ax2, pad=0.02)
        cbar2.set_label('Conductivity [MMHO]', fontweight='bold', fontsize=9)
        ax2.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='white')
        
        plt.suptitle('CMI Borehole Image Log\n(Brown=Low Conductivity/Coal, Yellow=High Conductivity/Shale)',
                    fontsize=13, fontweight='bold', y=0.995)
        
        plt.tight_layout()
        
        output_file = 'CMI_Raw_Image_Log.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved raw image to: {output_file}")
        
        output_pdf = 'CMI_Raw_Image_Log.pdf'
        plt.savefig(output_pdf, bbox_inches='tight')
        print(f"✓ Saved raw image to: {output_pdf}")

        print("\n" + "="*80)
        print("✓ CMI RAW IMAGE LOG COMPLETE!")
        print("="*80)
        print("\nDeliverables:")
        print("  - CMI_Raw_Image_Log.png/pdf - 2-panel display")
        print("    * Panel 1: Full interval with P05-P95 clipping and log scale")
        print("    * Panel 2: Detail zoom (468.5-488.5m) at 2mm resolution")
        print("  - 176 buttons displayed sequentially by pad")
        print("  - Full 2mm vertical resolution preserved")
        print("  - No azimuthal interpolation")
        print("\nProcessing applied:")
        print("  - Percentile clipping (P05-P95) to optimize contrast")
        print("  - Logarithmic normalization")
        print("  - Simple approach without histogram equalization")
        print("="*80 + "\n")