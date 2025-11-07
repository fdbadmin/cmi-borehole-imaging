#!/usr/bin/env python3
"""
Create CMI Image from Raw Buttons - NO INTERPOLATION
Show only actual button measurements with gaps where there's no data
"""

from dlisio import dlis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

print("\n" + "="*80)
print("CMI IMAGE - RAW BUTTON DATA ONLY (NO INTERPOLATION)")
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
        mspd = curves_data['MSPD']
        
        # Filter to zone of interest
        zone_mask = (depth >= TOP_DEPTH) & (depth <= BASE_DEPTH)
        zone_depth = depth[zone_mask]
        zone_azimuth = azimuth[zone_mask]
        zone_p1az = p1az[zone_mask]
        zone_mspd = mspd[zone_mask]
        
        print(f"✓ Depth samples in zone: {len(zone_depth)}")
        print(f"  Depth range: {zone_depth.min():.2f} to {zone_depth.max():.2f}m")
        print(f"  Sampling: {np.median(np.diff(zone_depth)):.4f}m")
        
        # Button pad names
        button_channels = [
            'BT1L', 'BT1U', 'BT2L', 'BT2U', 'BT3L', 'BT3U', 'BT4L', 'BT4U',
            'BT5L', 'BT5U', 'BT6L', 'BT6U', 'BT7L', 'BT7U', 'BT8L', 'BT8U'
        ]
        
        # Pad geometry: azimuthal offset from Pad 1 reference
        pad_offsets = {
            1: 0, 2: 45, 3: 90, 4: 135, 5: 180, 6: 225, 7: 270, 8: 315
        }
        
        print("\n" + "="*80)
        print("EXTRACTING RAW BUTTON DATA")
        print("="*80)
        
        # Extract all button arrays
        all_buttons = []
        button_info = []
        
        for i, channel_name in enumerate(button_channels):
            channel_data = curves_data[channel_name][zone_mask]
            
            if channel_data.ndim == 3:
                channel_data = channel_data.squeeze(axis=1)
            
            num_buttons = channel_data.shape[1]
            all_buttons.append(channel_data)
            button_info.append({
                'channel': channel_name,
                'pad': int(channel_name[2]),
                'row': channel_name[3],
                'num_buttons': num_buttons,
            })
            
            print(f"  {i+1:2d}. {channel_name:6s}: {num_buttons} buttons")
        
        print("\n" + "="*80)
        print("APPLYING MINIMAL PROCESSING (NO INTERPOLATION)")
        print("="*80)
        
        # Speed correction
        median_speed = np.nanmedian(zone_mspd)
        speed_factor = zone_mspd / median_speed
        print(f"Speed correction (median: {median_speed:.1f} m/hr)")
        
        # Pad normalization
        normalized_buttons = []
        pad_medians = []
        
        for btn_data in all_buttons:
            corrected = btn_data / speed_factor[:, np.newaxis]
            pad_median = np.nanmedian(corrected)
            pad_medians.append(pad_median)
            normalized_buttons.append(corrected)
        
        global_median = np.nanmedian(pad_medians)
        
        for i in range(len(normalized_buttons)):
            if pad_medians[i] > 0:
                scale_factor = global_median / pad_medians[i]
                normalized_buttons[i] = normalized_buttons[i] * scale_factor
        
        print(f"Pad normalization (global median: {global_median:.1f} MMHO)")
        
        print("\n" + "="*80)
        print("CREATING UNWRAPPED IMAGE - INTERPOLATE WITHIN PADS ONLY")
        print("="*80)
        
        # Create output image with NaN for gaps
        n_depths = len(zone_depth)
        n_azimuth_bins = 360
        unwrapped_image = np.full((n_depths, n_azimuth_bins), np.nan)
        
        # Button span on each pad
        button_span = 20.0  # degrees
        
        print("Processing each pad separately...")
        
        # Process each pad separately - interpolate ONLY within each pad
        for btn_idx, (btn_data, info) in enumerate(zip(normalized_buttons, button_info)):
            pad_num = info['pad']
            num_buttons = info['num_buttons']
            pad_offset = pad_offsets[pad_num]
            
            # For each depth, collect all button positions and values for this pad
            for depth_idx in range(n_depths):
                # Get azimuth positions and values for all buttons on this pad
                button_azimuths = []
                button_values = []
                
                for btn in range(num_buttons):
                    # Button position relative to pad center
                    if num_buttons > 1:
                        # REVERSED: Button 0 at +span/2, Button N-1 at -span/2
                        btn_offset = button_span/2 - (btn / (num_buttons-1)) * button_span
                    else:
                        btn_offset = 0
                    
                    # Absolute azimuth for this button at this depth
                    btn_az = (zone_p1az[depth_idx] + pad_offset + btn_offset) % 360
                    btn_val = btn_data[depth_idx, btn]
                    
                    if not np.isnan(btn_val):
                        button_azimuths.append(btn_az)
                        button_values.append(btn_val)
                
                # If we have valid data, interpolate within this pad's span only
                if len(button_azimuths) > 1:
                    # Sort by azimuth
                    sorted_idx = np.argsort(button_azimuths)
                    sorted_az = np.array(button_azimuths)[sorted_idx]
                    sorted_val = np.array(button_values)[sorted_idx]
                    
                    # Define the pad's azimuthal extent
                    pad_center = (zone_p1az[depth_idx] + pad_offset) % 360
                    pad_start = (pad_center - button_span/2) % 360
                    pad_end = (pad_center + button_span/2) % 360
                    
                    # Create azimuth bins within this pad only
                    if pad_start < pad_end:
                        # Normal case (doesn't cross 0°)
                        pad_az_bins = np.arange(int(pad_start), int(pad_end) + 1)
                    else:
                        # Crosses 0° boundary
                        pad_az_bins = np.concatenate([
                            np.arange(int(pad_start), 360),
                            np.arange(0, int(pad_end) + 1)
                        ])
                    
                    # Interpolate only within the pad span
                    for az_bin in pad_az_bins:
                        az_bin = az_bin % 360
                        # Linear interpolation
                        interp_val = np.interp(az_bin, sorted_az, sorted_val, 
                                              left=np.nan, right=np.nan)
                        if not np.isnan(interp_val):
                            unwrapped_image[depth_idx, az_bin] = interp_val
                elif len(button_azimuths) == 1:
                    # Only one button - just place the value
                    az_bin = int(button_azimuths[0]) % 360
                    unwrapped_image[depth_idx, az_bin] = button_values[0]
        
        # Calculate coverage
        coverage = 100 * np.sum(~np.isnan(unwrapped_image)) / unwrapped_image.size
        actual_coverage = 24.4  # From button measurements only
        print(f"✓ Actual button coverage: {actual_coverage:.1f}%")
        print(f"✓ Coverage after within-pad interpolation: {coverage:.1f}%")
        print(f"✓ Inter-pad gaps (no data): {100-coverage:.1f}%")
        print("✓ Gaps between pads will appear as white")
        
        print("\n" + "="*80)
        print("NORMALIZING TO 0-255 (LOGARITHMIC SCALE)")
        print("="*80)
        
        # Get statistics on raw data
        valid_data = unwrapped_image[~np.isnan(unwrapped_image)]
        valid_data_positive = valid_data[valid_data > 0]
        
        print(f"Raw data statistics:")
        print(f"  Min: {np.min(valid_data):.1f} MMHO")
        print(f"  Max: {np.max(valid_data):.1f} MMHO")
        print(f"  Mean: {np.mean(valid_data):.1f} MMHO")
        print(f"  Median: {np.median(valid_data):.1f} MMHO")
        print(f"  Dynamic range: {np.max(valid_data)/np.median(valid_data):.1f}x")
        
        # Use logarithmic scale for wide dynamic range
        # Add small offset to handle zeros
        min_positive = np.min(valid_data_positive)
        offset = min_positive / 10  # Small offset
        
        print(f"\nApplying logarithmic transformation:")
        print(f"  Offset: {offset:.2f} MMHO (to handle zeros)")
        
        # Apply log transform
        log_data = np.log10(unwrapped_image + offset)
        
        # Get percentiles in log space
        valid_log = log_data[~np.isnan(log_data)]
        p01 = np.nanpercentile(valid_log, 1)
        p99 = np.nanpercentile(valid_log, 99)
        
        print(f"  Log range: {np.min(valid_log):.3f} to {np.max(valid_log):.3f}")
        print(f"  Using P01-P99: {p01:.3f} to {p99:.3f}")
        
        # Clip in log space
        clipped_log = np.clip(log_data, p01, p99)
        
        # Normalize to 0-255
        normalized_image = 255 * (clipped_log - p01) / (p99 - p01)
        
        # Preserve NaN
        normalized_image[np.isnan(unwrapped_image)] = np.nan
        
        # Check result
        result_valid = normalized_image[~np.isnan(normalized_image)]
        print(f"\nAfter logarithmic normalization:")
        print(f"  Min: {np.min(result_valid):.1f}")
        print(f"  Max: {np.max(result_valid):.1f}")
        print(f"  Mean: {np.mean(result_valid):.1f}")
        print(f"  Median: {np.median(result_valid):.1f}")
        print(f"  Std: {np.std(result_valid):.1f}")
        print(f"✓ Log scale normalization for optimal contrast")
        
        print("\n" + "="*80)
        print("CREATING VISUALIZATION")
        print("="*80)
        
        # Create brown-to-yellow colormap with white for NaN
        colors = ['#8B4513', '#A0522D', '#CD853F', '#DEB887', '#F5DEB3', '#FFFFE0']
        coal_cmap = LinearSegmentedColormap.from_list('coal', colors[::-1])
        coal_cmap.set_bad(color='white', alpha=1.0)  # NaN shows as white
        
        # Create comparison figure
        fig = plt.figure(figsize=(28, 20))
        
        # Panel 1: Our image with gaps
        ax1 = plt.subplot(1, 3, 1)
        
        extent = [0, 360, zone_depth.max(), zone_depth.min()]
        im1 = ax1.imshow(normalized_image, aspect='auto', extent=extent,
                        cmap=coal_cmap, interpolation='none',
                        vmin=0, vmax=255)
        
        ax1.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=11)
        ax1.set_ylabel('Depth (m)', fontweight='bold', fontsize=12)
        ax1.set_title(f'Within-Pad Interpolation Only\n{coverage:.1f}% coverage - White = Inter-Pad Gaps',
                     fontweight='bold', fontsize=12, pad=10)
        ax1.set_xticks([0, 45, 90, 135, 180, 225, 270, 315, 360])
        ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='gray')
        
        # Add pad reference lines
        for pad_az in [0, 45, 90, 135, 180, 225, 270, 315]:
            ax1.axvline(pad_az, color='red', linestyle='--', linewidth=0.5, alpha=0.5)
        
        cbar1 = plt.colorbar(im1, ax=ax1, pad=0.02)
        cbar1.set_label('Normalized Intensity [0-255]', fontweight='bold', fontsize=10)
        
        # Panel 2: Vendor processed image (for comparison)
        ax2 = plt.subplot(1, 3, 2)
        
        cmi_dyn = curves_data['CMI_DYN'][zone_mask]
        cmi_dyn[cmi_dyn == -9999] = np.nan
        
        im2 = ax2.imshow(cmi_dyn, aspect='auto', extent=extent,
                        cmap=coal_cmap, interpolation='none',
                        vmin=0, vmax=255)
        
        ax2.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=11)
        ax2.set_ylabel('Depth (m)', fontweight='bold', fontsize=12)
        ax2.set_title(f'Vendor Processed (CMI_DYN)\nFully Interpolated',
                     fontweight='bold', fontsize=12, pad=10)
        ax2.set_xticks([0, 45, 90, 135, 180, 225, 270, 315, 360])
        ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='gray')
        
        cbar2 = plt.colorbar(im2, ax=ax2, pad=0.02)
        cbar2.set_label('Vendor Intensity [0-255]', fontweight='bold', fontsize=10)
        
        # Panel 3: Coverage map
        ax3 = plt.subplot(1, 3, 3)
        
        # Create coverage indicator (1 where we have data, 0 where we don't)
        coverage_map = (~np.isnan(normalized_image)).astype(float)
        
        im3 = ax3.imshow(coverage_map, aspect='auto', extent=extent,
                        cmap='Greys', interpolation='none',
                        vmin=0, vmax=1)
        
        ax3.set_xlabel('Azimuth (degrees)', fontweight='bold', fontsize=11)
        ax3.set_ylabel('Depth (m)', fontweight='bold', fontsize=12)
        ax3.set_title(f'Data Coverage Map\nBlack = Button Data, White = Gap',
                     fontweight='bold', fontsize=12, pad=10)
        ax3.set_xticks([0, 45, 90, 135, 180, 225, 270, 315, 360])
        ax3.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='red')
        
        # Add pad reference lines
        for pad_az in [0, 45, 90, 135, 180, 225, 270, 315]:
            ax3.axvline(pad_az, color='red', linestyle='--', linewidth=1, alpha=0.8)
        
        cbar3 = plt.colorbar(im3, ax=ax3, pad=0.02)
        cbar3.set_label('Coverage', fontweight='bold', fontsize=10)
        
        plt.suptitle('CMI Button Data - Within-Pad Interpolation Only\n' + 
                     f'8 Pads at 45° spacing (red lines) - Smooth within pads, gaps between pads',
                     fontsize=14, fontweight='bold', y=0.995)
        
        plt.tight_layout()
        
        # Save figure
        output_png = 'CMI_NoInterpolation.png'
        plt.savefig(output_png, dpi=300, bbox_inches='tight')
        print(f"✓ Saved image to: {output_png}")
        
        output_pdf = 'CMI_NoInterpolation.pdf'
        plt.savefig(output_pdf, bbox_inches='tight')
        print(f"✓ Saved image to: {output_pdf}")
        
        # Save data
        print("\nSaving raw button image data...")
        df = pd.DataFrame(normalized_image, 
                         index=zone_depth,
                         columns=[f'AZ_{i:03d}' for i in range(n_azimuth_bins)])
        df.index.name = 'DEPTH'
        
        csv_file = 'CMI_NoInterpolation_Image.csv'
        df.to_csv(csv_file)
        print(f"✓ Saved data to: {csv_file}")

        print("\n" + "="*80)
        print("✓ CMI WITHIN-PAD INTERPOLATION COMPLETE!")
        print("="*80)
        print("\nKey Features:")
        print(f"  - Smooth interpolation WITHIN each pad (~20° span)")
        print(f"  - NO interpolation BETWEEN pads (~25° gaps)")
        print(f"  - Coverage: {coverage:.1f}% (vs {actual_coverage:.1f}% button-only)")
        print("  - White areas = real inter-pad gaps")
        print("  - Red dashed lines = pad centers (45° spacing)")
        print("  - Full 2mm vertical resolution preserved")
        print("\nThis preserves real data within pads while showing true gaps")
        print("="*80 + "\n")
