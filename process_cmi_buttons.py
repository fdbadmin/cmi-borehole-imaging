#!/usr/bin/env python3
"""
Process CMI Button Data to Create Borehole Image
Replicates vendor processing workflow from raw button measurements
"""

from dlisio import dlis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.interpolate import griddata
from scipy.ndimage import median_filter

print("\n" + "="*80)
print("PROCESSING CMI BUTTON DATA TO BOREHOLE IMAGE")
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
        mspd = curves_data['MSPD']  # Logging speed
        
        # Filter to zone of interest
        zone_mask = (depth >= TOP_DEPTH) & (depth <= BASE_DEPTH)
        zone_depth = depth[zone_mask]
        zone_azimuth = azimuth[zone_mask]
        zone_p1az = p1az[zone_mask]
        zone_mspd = mspd[zone_mask]
        
        print(f"✓ Depth samples in zone: {len(zone_depth)}")
        print(f"  Depth range: {zone_depth.min():.2f} to {zone_depth.max():.2f}m")
        print(f"  Sampling: {np.median(np.diff(zone_depth)):.4f}m")
        
        # Button pad names (8 pads × 2 rows = 16 channels)
        button_channels = [
            'BT1L', 'BT1U', 'BT2L', 'BT2U', 'BT3L', 'BT3U', 'BT4L', 'BT4U',
            'BT5L', 'BT5U', 'BT6L', 'BT6U', 'BT7L', 'BT7U', 'BT8L', 'BT8U'
        ]
        
        # Pad geometry: azimuthal offset from Pad 1 reference
        # CMI tool typically has 8 pads at 45° spacing
        pad_offsets = {
            1: 0,      # Pad 1 is reference (P1AZ)
            2: 45,     # Pad 2 at +45°
            3: 90,     # Pad 3 at +90°
            4: 135,    # Pad 4 at +135°
            5: 180,    # Pad 5 at +180°
            6: 225,    # Pad 6 at +225°
            7: 270,    # Pad 7 at +270°
            8: 315     # Pad 8 at +315°
        }
        
        print("\n" + "="*80)
        print("STEP 1: EXTRACT AND ORGANIZE BUTTON DATA")
        print("="*80)
        
        # Extract all button arrays
        all_buttons = []
        button_info = []
        
        for i, channel_name in enumerate(button_channels):
            channel_data = curves_data[channel_name][zone_mask]
            
            # Remove extra dimension if present
            if channel_data.ndim == 3:
                channel_data = channel_data.squeeze(axis=1)
            
            num_buttons = channel_data.shape[1]
            valid_pct = 100 * np.sum(~np.isnan(channel_data)) / channel_data.size
            
            all_buttons.append(channel_data)
            button_info.append({
                'channel': channel_name,
                'pad': int(channel_name[2]),  # Extract pad number
                'row': channel_name[3],        # L or U
                'num_buttons': num_buttons,
                'valid_pct': valid_pct
            })
            
            print(f"  {i+1:2d}. {channel_name:6s}: {num_buttons} buttons, {valid_pct:.1f}% valid")
        
        print("\n" + "="*80)
        print("STEP 2: SPEED CORRECTION")
        print("="*80)
        
        # Normalize for logging speed variations
        # Conductivity measurements are affected by tool speed
        median_speed = np.nanmedian(zone_mspd)
        speed_factor = zone_mspd / median_speed
        
        print(f"Logging speed range: {np.nanmin(zone_mspd):.1f} to {np.nanmax(zone_mspd):.1f} m/hr")
        print(f"Median speed: {median_speed:.1f} m/hr")
        print(f"Applying speed normalization...")
        
        corrected_buttons = []
        for btn_data in all_buttons:
            # Apply speed correction (inverse relationship)
            corrected = btn_data / speed_factor[:, np.newaxis]
            corrected_buttons.append(corrected)
        
        print("✓ Speed correction applied")
        
        print("\n" + "="*80)
        print("STEP 3: PAD NORMALIZATION")
        print("="*80)
        
        # Normalize each pad to have similar response
        # Calculate median for each pad and equalize
        print("Equalizing pad responses...")
        
        normalized_buttons = []
        pad_stats = []
        
        for i, (btn_data, info) in enumerate(zip(corrected_buttons, button_info)):
            pad_median = np.nanmedian(btn_data)
            pad_stats.append({'channel': info['channel'], 'median': pad_median})
            normalized_buttons.append(btn_data)
        
        # Find global median across all pads
        global_median = np.nanmedian([s['median'] for s in pad_stats])
        
        # Normalize each pad to global median
        for i, (btn_data, stats) in enumerate(zip(normalized_buttons, pad_stats)):
            if stats['median'] > 0:
                scale_factor = global_median / stats['median']
                normalized_buttons[i] = btn_data * scale_factor
                print(f"  {stats['channel']}: median {stats['median']:.1f} → {global_median:.1f} MMHO (factor: {scale_factor:.3f})")
        
        print("✓ Pad normalization complete")
        
        print("\n" + "="*80)
        print("STEP 4: AZIMUTHAL UNWRAPPING")
        print("="*80)
        
        # Create 360° unwrapped image by mapping each button to its azimuthal position
        print("Mapping buttons to azimuthal positions...")
        
        # Create output image: depth × azimuth
        n_depths = len(zone_depth)
        n_azimuth_bins = 360  # 1° bins
        unwrapped_image = np.full((n_depths, n_azimuth_bins), np.nan)
        
        # For each button, calculate its azimuthal position and map to image
        for btn_idx, (btn_data, info) in enumerate(zip(normalized_buttons, button_info)):
            pad_num = info['pad']
            num_buttons = info['num_buttons']
            
            # Get pad azimuthal offset
            pad_offset = pad_offsets[pad_num]
            
            # Calculate azimuthal positions for each button on this pad
            # Buttons are arranged circumferentially on the pad
            # Assuming buttons span ~20° on each pad
            button_span = 20.0  # degrees
            
            for btn in range(num_buttons):
                # Button position relative to pad center
                # Distribute buttons evenly across the span
                if num_buttons > 1:
                    btn_offset = -button_span/2 + (btn / (num_buttons-1)) * button_span
                else:
                    btn_offset = 0
                
                # Absolute azimuth for this button at each depth
                # P1AZ gives the azimuth of Pad 1, add offsets for other pads
                button_azimuth = (zone_p1az + pad_offset + btn_offset) % 360
                
                # Map to azimuth bins
                azimuth_bins = (button_azimuth).astype(int) % 360
                
                # Place button values in the image
                for depth_idx in range(n_depths):
                    az_bin = azimuth_bins[depth_idx]
                    if not np.isnan(btn_data[depth_idx, btn]):
                        unwrapped_image[depth_idx, az_bin] = btn_data[depth_idx, btn]
        
        # Count coverage
        coverage = 100 * np.sum(~np.isnan(unwrapped_image)) / unwrapped_image.size
        print(f"✓ Azimuthal coverage: {coverage:.1f}%")
        
        print("\n" + "="*80)
        print("STEP 5: INTERPOLATION")
        print("="*80)
        
        # Interpolate to fill gaps between buttons
        print("Interpolating gaps in azimuthal coverage...")
        
        filled_image = np.copy(unwrapped_image)
        
        # For each depth level, interpolate across azimuth
        for depth_idx in range(n_depths):
            row = unwrapped_image[depth_idx, :]
            valid_mask = ~np.isnan(row)
            
            if np.sum(valid_mask) > 3:  # Need at least 3 points
                valid_azimuth = np.where(valid_mask)[0]
                valid_values = row[valid_mask]
                
                # Interpolate (linear) to fill gaps
                all_azimuth = np.arange(n_azimuth_bins)
                interpolated = np.interp(all_azimuth, valid_azimuth, valid_values, 
                                        period=360)  # Periodic boundary
                
                filled_image[depth_idx, :] = interpolated
        
        coverage_after = 100 * np.sum(~np.isnan(filled_image)) / filled_image.size
        print(f"✓ Coverage after interpolation: {coverage_after:.1f}%")
        
        print("\n" + "="*80)
        print("STEP 6: IMAGE ENHANCEMENT")
        print("="*80)
        
        # Apply median filter to reduce noise (optional - can cause smoothing)
        print("Applying median filter to reduce noise...")
        # Use smaller filter to preserve resolution
        smoothed_image = median_filter(filled_image, size=(1, 3))  # Only smooth azimuthally, not vertically
        print(f"  Filter size: 1×3 (preserves vertical resolution)")
        
        print("\n" + "="*80)
        print("STEP 7: NORMALIZATION TO 0-255")
        print("="*80)
        
        # Normalize to 0-255 range for standard image display
        # Use percentile clipping to handle outliers
        p05 = np.nanpercentile(smoothed_image, 5)
        p95 = np.nanpercentile(smoothed_image, 95)
        
        print(f"Data range: {np.nanmin(smoothed_image):.1f} to {np.nanmax(smoothed_image):.1f} MMHO")
        print(f"Using P05-P95: {p05:.1f} to {p95:.1f} MMHO")
        
        # Clip and normalize
        clipped_image = np.clip(smoothed_image, p05, p95)
        normalized_image = 255 * (clipped_image - p05) / (p95 - p05)
        
        print(f"✓ Normalized to range: {np.nanmin(normalized_image):.1f} to {np.nanmax(normalized_image):.1f}")
        
        print("\n" + "="*80)
        print("CREATING VISUALIZATION")
        print("="*80)
        
        # Create brown-to-yellow colormap
        colors = ['#8B4513', '#A0522D', '#CD853F', '#DEB887', '#F5DEB3', '#FFFFE0']
        coal_cmap = LinearSegmentedColormap.from_list('coal', colors[::-1])
        
        # Create comparison figure
        fig = plt.figure(figsize=(24, 20))
        
        # Panel 1: Our processed image
        ax1 = plt.subplot(1, 3, 1)
        
        extent = [0, 360, zone_depth.max(), zone_depth.min()]
        im1 = ax1.imshow(normalized_image, aspect='auto', extent=extent,
                        cmap=coal_cmap, interpolation='none',  # No interpolation to preserve resolution
                        vmin=0, vmax=255)
        
        ax1.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=10)
        ax1.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax1.set_title(f'Our Processed Image\nAnya 105: {TOP_DEPTH}-{BASE_DEPTH}m',
                     fontweight='bold', fontsize=11, pad=10)
        ax1.set_xticks([0, 90, 180, 270, 360])
        ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='white')
        
        cbar1 = plt.colorbar(im1, ax=ax1, pad=0.02)
        cbar1.set_label('Normalized Intensity [0-255]', fontweight='bold', fontsize=9)
        
        # Panel 2: Vendor processed image (for comparison)
        ax2 = plt.subplot(1, 3, 2)
        
        cmi_dyn = curves_data['CMI_DYN'][zone_mask]
        cmi_dyn[cmi_dyn == -9999] = np.nan
        
        im2 = ax2.imshow(cmi_dyn, aspect='auto', extent=extent,
                        cmap=coal_cmap, interpolation='none',  # No interpolation
                        vmin=0, vmax=255)
        
        ax2.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=10)
        ax2.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax2.set_title(f'Vendor Processed (CMI_DYN)\nAnya 105: {TOP_DEPTH}-{BASE_DEPTH}m',
                     fontweight='bold', fontsize=11, pad=10)
        ax2.set_xticks([0, 90, 180, 270, 360])
        ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='white')
        
        cbar2 = plt.colorbar(im2, ax=ax2, pad=0.02)
        cbar2.set_label('Vendor Intensity [0-255]', fontweight='bold', fontsize=9)
        
        # Panel 3: Difference map
        ax3 = plt.subplot(1, 3, 3)
        
        difference = normalized_image - cmi_dyn
        
        im3 = ax3.imshow(difference, aspect='auto', extent=extent,
                        cmap='seismic', interpolation='none',  # No interpolation
                        vmin=-50, vmax=50)
        
        ax3.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=10)
        ax3.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax3.set_title(f'Difference Map\n(Our Processing - Vendor)',
                     fontweight='bold', fontsize=11, pad=10)
        ax3.set_xticks([0, 90, 180, 270, 360])
        ax3.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='white')
        
        cbar3 = plt.colorbar(im3, ax=ax3, pad=0.02)
        cbar3.set_label('Difference [-50 to +50]', fontweight='bold', fontsize=9)
        
        plt.suptitle('CMI Processing Comparison: Our Algorithm vs Vendor\n(Brown=Resistive/Coal, Yellow=Conductive/Shale)',
                    fontsize=13, fontweight='bold', y=0.998)
        
        plt.tight_layout()
        
        # Save figure
        output_png = 'CMI_Custom_Processing.png'
        plt.savefig(output_png, dpi=300, bbox_inches='tight')
        print(f"✓ Saved image to: {output_png}")
        
        output_pdf = 'CMI_Custom_Processing.pdf'
        plt.savefig(output_pdf, bbox_inches='tight')
        print(f"✓ Saved image to: {output_pdf}")
        
        # Save processed data
        print("\nSaving processed image data...")
        df = pd.DataFrame(normalized_image, 
                         index=zone_depth,
                         columns=[f'AZ_{i:03d}' for i in range(n_azimuth_bins)])
        df.index.name = 'DEPTH'
        
        csv_file = 'CMI_Custom_Processed_Image.csv'
        df.to_csv(csv_file)
        print(f"✓ Saved processed data to: {csv_file}")

        print("\n" + "="*80)
        print("✓ CMI PROCESSING COMPLETE!")
        print("="*80)
        print("\nProcessing steps applied:")
        print("  1. Speed correction (normalized for logging speed)")
        print("  2. Pad normalization (equalized pad responses)")
        print("  3. Azimuthal unwrapping (mapped to 360° image)")
        print("  4. Interpolation (filled gaps between buttons)")
        print("  5. Median filtering (noise reduction)")
        print("  6. Normalization to 0-255 (standard image scale)")
        print("\nDeliverables:")
        print("  - CMI_Custom_Processing.png/pdf - 3-panel comparison")
        print("  - CMI_Custom_Processed_Image.csv - Processed image data")
        print("="*80 + "\n")
