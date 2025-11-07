#!/usr/bin/env python3
"""
Create Full CMI Borehole Image Log
Extract all button arrays and generate unwrapped borehole image
Zone: Upper Juandah Coal Measures to Eurombah Formation (233.3-547.0m)
"""

from dlisio import dlis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches

print("\n" + "="*80)
print("CREATING CMI BOREHOLE IMAGE LOG")
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
        azimuth = curves_data['AZIM']  # Borehole azimuth
        p1az = curves_data['P1AZ']     # Reference pad azimuth
        
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
            try:
                # Get channel data
                channel_data = curves_data[channel_name]
                zone_data = channel_data[zone_mask]
                
                # Reshape from (N, 1, 10) to (N, 10)
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
                
                # Store individual button names for CSV
                for btn in range(10):
                    button_names.append(f'{channel_name}_BTN{btn+1}')
                    
            except KeyError:
                print(f"  {i+1:2d}. {channel_name:6s}: NOT FOUND")
            except Exception as e:
                print(f"  {i+1:2d}. {channel_name:6s}: ERROR - {e}")
        
        # Combine all buttons into single array
        # Each pad has variable buttons (10 or 12), 16 pads total
        print(f"\n{'='*80}")
        print("ASSEMBLING IMAGE WITH AZIMUTH ORIENTATION")
        print(f"{'='*80}")
        
        image_array = np.hstack(all_buttons)  # Concatenate horizontally
        print(f"Image array shape: {image_array.shape}")
        print(f"  Depth samples: {image_array.shape[0]}")
        print(f"  Total buttons: {image_array.shape[1]}")
        
        # Calculate button azimuth positions
        # CMI has 8 pads arranged circumferentially (45° apart)
        # Each pad has 10 or 12 buttons arranged vertically in 2 rows (upper/lower)
        # Pad 1 is at P1AZ reference azimuth
        
        pad_spacing = 45.0  # degrees between pads
        buttons_per_pad = []
        for i in range(0, len(all_buttons), 2):
            buttons_per_pad.append(all_buttons[i].shape[1])  # Lower row
            
        print(f"\nPad configuration:")
        print(f"  Number of pads: 8")
        print(f"  Pad spacing: {pad_spacing}°")
        print(f"  Buttons per pad: {buttons_per_pad}")
        
        # Create azimuth array for each button
        # This varies with depth as tool rotates
        button_azimuths = np.zeros((len(zone_depth), image_array.shape[1]))
        
        button_idx = 0
        for pad_num in range(8):
            # Pad offset from reference (Pad 1 at P1AZ)
            pad_offset = pad_num * pad_spacing
            
            # Get buttons for this pad (lower and upper rows)
            num_buttons = buttons_per_pad[pad_num]
            
            # Lower row
            for btn in range(num_buttons):
                # Angular position within pad
                btn_angle = (btn / num_buttons) * pad_spacing
                # Absolute azimuth (varies with depth due to tool rotation)
                button_azimuths[:, button_idx] = (zone_p1az + pad_offset + btn_angle) % 360
                button_idx += 1
            
            # Upper row
            for btn in range(num_buttons):
                btn_angle = (btn / num_buttons) * pad_spacing
                button_azimuths[:, button_idx] = (zone_p1az + pad_offset + btn_angle) % 360
                button_idx += 1
        
        print(f"\n✓ Created azimuth-oriented button positions")
        print(f"  Azimuth array shape: {button_azimuths.shape}")
        print(f"  Azimuth range: {button_azimuths.min():.1f}° to {button_azimuths.max():.1f}°")
        
        # Statistics
        print(f"\nImage statistics:")
        print(f"  Min: {np.nanmin(image_array):.2f} MMHO")
        print(f"  Max: {np.nanmax(image_array):.2f} MMHO")
        print(f"  Mean: {np.nanmean(image_array):.2f} MMHO")
        print(f"  Median: {np.nanmedian(image_array):.2f} MMHO")
        print(f"  P95: {np.nanpercentile(image_array, 95):.2f} MMHO")
        
        # Save to CSV
        print(f"\n{'='*80}")
        print("SAVING DATA")
        print(f"{'='*80}")
        
        # Create DataFrame
        df_dict = {'DEPTH': zone_depth}
        for i, btn_name in enumerate(button_names):
            df_dict[btn_name] = image_array[:, i]
        
        df = pd.DataFrame(df_dict)
        
        csv_file = 'CMI_Image_Log_Full.csv'
        df.to_csv(csv_file, index=False, float_format='%.4f')
        print(f"✓ Saved full button data to: {csv_file}")
        print(f"  Columns: {len(df.columns)} (1 depth + {len(button_names)} buttons)")
        print(f"  Rows: {len(df)}")
        print(f"  File size: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        # Create visualizations
        print(f"\n{'='*80}")
        print("CREATING BOREHOLE IMAGE")
        print(f"{'='*80}")
        
        # Create brown-to-yellow colormap (coal resistivity imaging)
        # Brown (low conductivity/high resistivity = coal)
        # Yellow (high conductivity/low resistivity = shale)
        from matplotlib.colors import LinearSegmentedColormap, LogNorm
        
        colors_list = [
            (0.2, 0.1, 0.0),   # Dark brown (coal/resistive)
            (0.4, 0.2, 0.1),   # Brown
            (0.6, 0.4, 0.2),   # Light brown
            (0.8, 0.6, 0.3),   # Tan
            (1.0, 0.9, 0.4),   # Yellow (shale/conductive)
        ]
        coal_cmap = LinearSegmentedColormap.from_list('coal_image', colors_list, N=256)
        
        # Create unwrapped image using azimuth orientation
        # Need to interpolate irregular azimuth data onto regular grid
        print("Creating azimuth-corrected unwrapped image...")
        
        # Define regular azimuth grid (0-360 degrees)
        n_azimuth_bins = 360  # 1 degree bins
        azimuth_grid = np.linspace(0, 360, n_azimuth_bins)
        
        # Interpolate onto regular grid - KEEP ALL DEPTH SAMPLES (156,851 rows!)
        unwrapped_image = np.zeros((len(zone_depth), n_azimuth_bins))
        
        print(f"Interpolating {len(zone_depth)} depth samples onto regular azimuth grid...")
        
        for i in range(len(zone_depth)):
            # Sort buttons by azimuth for this depth
            sorted_idx = np.argsort(button_azimuths[i, :])
            sorted_az = button_azimuths[i, sorted_idx]
            sorted_values = image_array[i, sorted_idx]
            
            # Handle wraparound (360° = 0°) - extend data on both sides
            sorted_az = np.concatenate([sorted_az - 360, sorted_az, sorted_az + 360])
            sorted_values = np.concatenate([sorted_values, sorted_values, sorted_values])
            
            # Interpolate onto regular azimuth grid
            unwrapped_image[i, :] = np.interp(azimuth_grid, sorted_az, sorted_values)
        
        print(f"✓ Unwrapped image shape: {unwrapped_image.shape}")
        print(f"  Vertical resolution: {np.median(np.diff(zone_depth))*1000:.1f} mm ({len(zone_depth)} samples)")
        print(f"  Azimuthal resolution: {360/n_azimuth_bins:.1f}° ({n_azimuth_bins} bins)")
        
        # Fixed color scale - brown at 7.94 MMHO, yellow at 0.33 MMHO
        vmin = 0.33  # Yellow (high conductivity)
        vmax = 7.94  # Brown (low conductivity)
        
        print(f"\nColor scale (logarithmic):")
        print(f"  Brown (min): {vmax} MMHO (coal/resistive)")
        print(f"  Yellow (max): {vmin} MMHO (shale/conductive)")
        
        # Create figure with multiple panels
        fig = plt.figure(figsize=(18, 20))  # Taller for high vertical resolution
        
        # Main image - azimuth corrected with log scale - FULL RESOLUTION
        ax1 = plt.subplot(1, 2, 1)
        
        extent = [0, 360, zone_depth.max(), zone_depth.min()]
        im = ax1.imshow(unwrapped_image, aspect='auto', extent=extent,
                       cmap=coal_cmap, interpolation='nearest',  # Use 'nearest' to preserve sharp edges
                       norm=LogNorm(vmin=vmin, vmax=vmax))
        
        ax1.set_xlabel('Azimuth (degrees True North)', fontweight='bold', fontsize=11)
        ax1.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax1.set_title('CMI Borehole Image - Full Resolution (2mm vertical)\n' + 
                     f'Anya 105: {TOP_DEPTH}m - {BASE_DEPTH}m (Brown=Coal, Yellow=Shale)',
                     fontweight='bold', fontsize=12, pad=10)
        
        # Add azimuth markers
        azimuth_ticks = [0, 45, 90, 135, 180, 225, 270, 315, 360]
        azimuth_labels = ['N\n0°', 'NE\n45°', 'E\n90°', 'SE\n135°', 'S\n180°', 
                         'SW\n225°', 'W\n270°', 'NW\n315°', 'N\n360°']
        ax1.set_xticks(azimuth_ticks)
        ax1.set_xticklabels(azimuth_labels, fontsize=9)
        
        # Add colorbar with log scale
        cbar = plt.colorbar(im, ax=ax1, pad=0.02)
        cbar.set_label('Conductivity [MMHO] (log scale)', fontweight='bold', fontsize=10)
        
        # Add grid
        ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='black')
        ax1.set_xlim(0, 360)
        
        # Panel 2: Zoomed section to show vertical detail
        ax2 = plt.subplot(1, 2, 2)
        
        # Show a detailed 20m section around coal zone (~478-479m from previous analysis)
        zoom_center = 478.5
        zoom_range = 20.0  # ±10m
        zoom_mask = (zone_depth >= zoom_center - zoom_range/2) & (zone_depth <= zoom_center + zoom_range/2)
        
        zoom_depth = zone_depth[zoom_mask]
        zoom_image = unwrapped_image[zoom_mask, :]
        
        extent_zoom = [0, 360, zoom_depth.max(), zoom_depth.min()]
        im2 = ax2.imshow(zoom_image, aspect='auto', extent=extent_zoom,
                        cmap=coal_cmap, interpolation='nearest',  # Preserve pixel detail
                        norm=LogNorm(vmin=vmin, vmax=vmax))
        
        ax2.set_xlabel('Azimuth (degrees True North)', fontweight='bold', fontsize=11)
        ax2.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax2.set_title(f'CMI Detail View: {zoom_center-zoom_range/2:.1f}-{zoom_center+zoom_range/2:.1f}m\n' + 
                     f'({len(zoom_depth)} samples at 2mm spacing)',
                     fontweight='bold', fontsize=12, pad=10)
        
        # Azimuth markers
        ax2.set_xticks(azimuth_ticks)
        ax2.set_xticklabels(azimuth_labels, fontsize=9)
        
        cbar2 = plt.colorbar(im2, ax=ax2, pad=0.02)
        cbar2.set_label('Conductivity [MMHO] (log scale)', fontweight='bold', fontsize=10)
        
        ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='black')
        ax2.set_xlim(0, 360)
        
        plt.tight_layout()
        
        output_file = 'CMI_Borehole_Image_Log.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved image to: {output_file}")
        
        # Also save as PDF
        output_pdf = 'CMI_Borehole_Image_Log.pdf'
        plt.savefig(output_pdf, bbox_inches='tight')
        print(f"✓ Saved image to: {output_pdf}")
        
        plt.close()
        
        # Create a more detailed plot focusing on coal zones
        print(f"\n{'='*80}")
        print("CREATING COAL-FOCUSED IMAGE")
        print(f"{'='*80}")
        
        # Identify potential coal zones (low conductivity)
        avg_conductivity = np.nanmean(unwrapped_image, axis=1)
        coal_threshold = np.nanpercentile(avg_conductivity, 25)  # Bottom 25%
        coal_flag = avg_conductivity < coal_threshold
        
        fig2, (ax_img, ax_avg) = plt.subplots(1, 2, figsize=(18, 20))  # Taller for full resolution
        
        # Main image with coal zones highlighted - FULL RESOLUTION
        im3 = ax_img.imshow(unwrapped_image, aspect='auto', extent=extent,
                           cmap=coal_cmap, interpolation='nearest',  # Preserve detail
                           norm=LogNorm(vmin=vmin, vmax=vmax))
        
        ax_img.set_xlabel('Azimuth (degrees True North)', fontweight='bold', fontsize=11)
        ax_img.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax_img.set_title('CMI Image with Coal Zone Highlighting\n(Brown=Low Conductivity=Potential Coal)',
                        fontweight='bold', fontsize=12, pad=10)
        
        ax_img.set_xticks(azimuth_ticks)
        ax_img.set_xticklabels(azimuth_labels, fontsize=9)
        
        cbar3 = plt.colorbar(im3, ax=ax_img, pad=0.02)
        cbar3.set_label('Conductivity [MMHO] (log scale)', fontweight='bold', fontsize=10)
        
        # Highlight coal zones with overlay
        for i in range(len(zone_depth)-1):
            if coal_flag[i]:
                ax_img.axhspan(zone_depth[i+1], zone_depth[i], 
                             facecolor='cyan', alpha=0.15, zorder=10)
        
        ax_img.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='black')
        ax_img.set_xlim(0, 360)
        
        # Average conductivity track
        ax_avg.plot(avg_conductivity, zone_depth, 'b-', linewidth=1, label='Avg Conductivity')
        ax_avg.axvline(coal_threshold, color='red', linestyle='--', linewidth=2, 
                      label=f'Coal Threshold ({coal_threshold:.1f} MMHO)')
        ax_avg.fill_betweenx(zone_depth, 0, avg_conductivity, 
                            where=coal_flag, color='yellow', alpha=0.3, 
                            label='Potential Coal')
        
        ax_avg.set_xlabel('Average Conductivity (MMHO)', fontweight='bold', fontsize=11)
        ax_avg.set_ylabel('Depth (m)', fontweight='bold', fontsize=11)
        ax_avg.set_title('Average Circumferential Conductivity',
                        fontweight='bold', fontsize=12, pad=10)
        ax_avg.invert_yaxis()
        ax_avg.grid(True, alpha=0.3)
        ax_avg.legend(loc='best', fontsize=10)
        
        plt.tight_layout()
        
        output_coal = 'CMI_Coal_Focused_Image.png'
        plt.savefig(output_coal, dpi=300, bbox_inches='tight')
        print(f"✓ Saved coal-focused image to: {output_coal}")
        
        output_coal_pdf = 'CMI_Coal_Focused_Image.pdf'
        plt.savefig(output_coal_pdf, bbox_inches='tight')
        print(f"✓ Saved coal-focused image to: {output_coal_pdf}")
        
        print(f"\nCoal detection from image:")
        print(f"  Threshold: {coal_threshold:.2f} MMHO")
        print(f"  Coal intervals: {np.sum(coal_flag)} samples = {np.sum(coal_flag) * 0.002:.2f}m")

print("\n" + "="*80)
print("✓ CMI BOREHOLE IMAGE LOG COMPLETE!")
print("="*80)
print("\nDeliverables:")
print("  1. CMI_Image_Log_Full.csv - All 160 button values")
print("  2. CMI_Borehole_Image_Log.png/pdf - Full & binned images")
print("  3. CMI_Coal_Focused_Image.png/pdf - Coal zone highlighting")
print("="*80 + "\n")
