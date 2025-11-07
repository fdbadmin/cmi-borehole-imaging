#!/usr/bin/env python3
"""
CMI Button Data Quality Control
Comprehensive QC checks before image generation
"""

from dlisio import dlis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

print("\n" + "="*80)
print("CMI BUTTON DATA QUALITY CONTROL")
print("="*80)

# Zone of interest
TOP_DEPTH = 233.3
BASE_DEPTH = 547.0

# Load DLIS file
dlis_file = 'Raw dataset/qgc_anya-105_mcg-cmi.dlis'

with dlis.load(dlis_file) as files:
    for f in files:
        frame = f.frames[0]
        
        # Load data
        curves_data = frame.curves()
        depth = curves_data['DEPTH']
        azimuth = curves_data['AZIM']
        p1az = curves_data['P1AZ']
        
        # Get caliper data if available
        try:
            caliper_x = curves_data['CALX']
            caliper_y = curves_data['CALY']
        except:
            caliper_x = None
            caliper_y = None
        
        # Filter to zone
        zone_mask = (depth >= TOP_DEPTH) & (depth <= BASE_DEPTH)
        zone_depth = depth[zone_mask]
        
        # Button channels
        button_channels = [
            'BT1L', 'BT1U', 'BT2L', 'BT2U', 'BT3L', 'BT3U', 
            'BT4L', 'BT4U', 'BT5L', 'BT5U', 'BT6L', 'BT6U',
            'BT7L', 'BT7U', 'BT8L', 'BT8U',
        ]
        
        print(f"\n{'='*80}")
        print("1. DATA AVAILABILITY CHECK")
        print(f"{'='*80}")
        
        all_buttons = []
        qc_stats = []
        
        for channel_name in button_channels:
            channel_data = curves_data[channel_name]
            zone_data = channel_data[zone_mask].squeeze()
            
            # Replace nulls
            zone_data[zone_data == -9999] = np.nan
            zone_data[zone_data < 0] = np.nan
            
            all_buttons.append(zone_data)
            
            # QC statistics
            total_points = zone_data.size
            valid_points = np.sum(~np.isnan(zone_data))
            null_points = np.sum(np.isnan(zone_data))
            zero_points = np.sum(zone_data == 0)
            
            qc_stats.append({
                'Channel': channel_name,
                'Total': total_points,
                'Valid': valid_points,
                'Null': null_points,
                'Zero': zero_points,
                'Valid%': 100 * valid_points / total_points,
                'Min': np.nanmin(zone_data),
                'Max': np.nanmax(zone_data),
                'Mean': np.nanmean(zone_data),
                'Std': np.nanstd(zone_data)
            })
            
            print(f"{channel_name}: {valid_points:7d}/{total_points:7d} valid ({100*valid_points/total_points:5.1f}%), "
                  f"range [{np.nanmin(zone_data):7.1f}, {np.nanmax(zone_data):7.1f}] MMHO")
        
        qc_df = pd.DataFrame(qc_stats)
        
        print(f"\n{'='*80}")
        print("2. PAD BALANCE CHECK")
        print(f"{'='*80}")
        print("(All pads should have similar mean values - large differences indicate pad contact issues)")
        
        # Compare pads (average of upper and lower rows)
        for pad_num in range(1, 9):
            lower_name = f'BT{pad_num}L'
            upper_name = f'BT{pad_num}U'
            
            lower_stats = qc_df[qc_df['Channel'] == lower_name].iloc[0]
            upper_stats = qc_df[qc_df['Channel'] == upper_name].iloc[0]
            
            pad_mean = (lower_stats['Mean'] + upper_stats['Mean']) / 2
            pad_ratio = upper_stats['Mean'] / lower_stats['Mean'] if lower_stats['Mean'] > 0 else 0
            
            status = "✓ OK" if 0.5 < pad_ratio < 2.0 else "⚠ CHECK"
            
            print(f"Pad {pad_num}: Lower={lower_stats['Mean']:6.1f}, Upper={upper_stats['Mean']:6.1f}, "
                  f"Ratio={pad_ratio:.2f} {status}")
        
        print(f"\n{'='*80}")
        print("3. OUTLIER DETECTION")
        print(f"{'='*80}")
        
        image_array = np.hstack(all_buttons)
        
        # Global statistics
        global_mean = np.nanmean(image_array)
        global_std = np.nanstd(image_array)
        global_p99 = np.nanpercentile(image_array, 99)
        
        # Detect extreme outliers (>5 sigma or >10x P99)
        outlier_threshold = min(global_mean + 5*global_std, 10*global_p99)
        outliers = image_array > outlier_threshold
        
        print(f"Global statistics:")
        print(f"  Mean: {global_mean:.2f} MMHO")
        print(f"  Std Dev: {global_std:.2f} MMHO")
        print(f"  P99: {global_p99:.2f} MMHO")
        print(f"  Outlier threshold (5σ or 10×P99): {outlier_threshold:.2f} MMHO")
        print(f"  Outliers found: {np.sum(outliers)} / {outliers.size} ({100*np.sum(outliers)/outliers.size:.3f}%)")
        
        if np.sum(outliers) > 0:
            print(f"  ⚠ Recommendation: Consider clipping outliers to {outlier_threshold:.0f} MMHO")
        
        print(f"\n{'='*80}")
        print("4. DEPTH CONTINUITY CHECK")
        print(f"{'='*80}")
        
        depth_diff = np.diff(zone_depth)
        median_spacing = np.median(depth_diff)
        
        # Find gaps (>2x median spacing)
        gaps = depth_diff > 2 * median_spacing
        
        print(f"Depth sampling:")
        print(f"  Median spacing: {median_spacing*1000:.2f} mm")
        print(f"  Min spacing: {np.min(depth_diff)*1000:.2f} mm")
        print(f"  Max spacing: {np.max(depth_diff)*1000:.2f} mm")
        print(f"  Gaps (>2× median): {np.sum(gaps)}")
        
        if np.sum(gaps) > 0:
            gap_depths = zone_depth[:-1][gaps]
            print(f"  ⚠ Gaps found at depths: {gap_depths[:5]} {'...' if len(gap_depths) > 5 else ''}")
        else:
            print(f"  ✓ No significant gaps detected")
        
        print(f"\n{'='*80}")
        print("5. TOOL ORIENTATION CHECK")
        print(f"{'='*80}")
        
        zone_azimuth = azimuth[zone_mask]
        zone_p1az = p1az[zone_mask]
        
        azim_range = np.nanmax(zone_azimuth) - np.nanmin(zone_azimuth)
        p1az_range = np.nanmax(zone_p1az) - np.nanmin(zone_p1az)
        
        print(f"Borehole azimuth range: {np.nanmin(zone_azimuth):.1f}° to {np.nanmax(zone_azimuth):.1f}° "
              f"(Δ={azim_range:.1f}°)")
        print(f"Pad 1 reference azimuth range: {np.nanmin(zone_p1az):.1f}° to {np.nanmax(zone_p1az):.1f}° "
              f"(Δ={p1az_range:.1f}°)")
        
        if p1az_range > 180:
            print(f"  ⚠ Large P1AZ variation - tool rotated significantly")
        else:
            print(f"  ✓ Reasonable tool orientation variation")
        
        if caliper_x is not None and caliper_y is not None:
            print(f"\n{'='*80}")
            print("6. BOREHOLE CONDITION CHECK (Caliper)")
            print(f"{'='*80}")
            
            zone_calx = caliper_x[zone_mask]
            zone_caly = caliper_y[zone_mask]
            
            # Calculate average caliper
            avg_caliper = (zone_calx + zone_caly) / 2
            
            # Bit size from DLIS
            bit_size = curves_data['BIT'][zone_mask]
            median_bit = np.nanmedian(bit_size)
            
            print(f"Bit size: {median_bit:.2f} inches")
            print(f"Caliper X: {np.nanmin(zone_calx):.2f} to {np.nanmax(zone_calx):.2f} inches "
                  f"(mean {np.nanmean(zone_calx):.2f})")
            print(f"Caliper Y: {np.nanmin(zone_caly):.2f} to {np.nanmax(zone_caly):.2f} inches "
                  f"(mean {np.nanmean(zone_caly):.2f})")
            
            # Check for washouts (caliper >> bit size)
            washout_threshold = median_bit * 1.5  # 50% larger than bit
            washouts = avg_caliper > washout_threshold
            washout_pct = 100 * np.sum(washouts) / len(avg_caliper)
            
            print(f"Washout zones (caliper > {washout_threshold:.1f}\"): {np.sum(washouts)} samples ({washout_pct:.1f}%)")
            
            if washout_pct > 10:
                print(f"  ⚠ Significant washouts - may affect button contact quality")
            else:
                print(f"  ✓ Minimal washouts")
        
        # Create QC visualization
        print(f"\n{'='*80}")
        print("CREATING QC PLOTS")
        print(f"{'='*80}")
        
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
        
        # Plot 1: Data availability by channel
        ax1 = fig.add_subplot(gs[0, :])
        channels = qc_df['Channel'].values
        valid_pct = qc_df['Valid%'].values
        colors = ['green' if v > 95 else 'orange' if v > 90 else 'red' for v in valid_pct]
        ax1.bar(channels, valid_pct, color=colors, alpha=0.7, edgecolor='black')
        ax1.axhline(95, color='red', linestyle='--', linewidth=2, label='95% threshold')
        ax1.set_ylabel('Valid Data %', fontweight='bold')
        ax1.set_title('Data Availability by Channel', fontweight='bold')
        ax1.set_ylim(0, 105)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot 2: Mean conductivity by pad
        ax2 = fig.add_subplot(gs[1, 0])
        pad_means = [qc_df[qc_df['Channel'] == f'BT{i}L']['Mean'].values[0] for i in range(1, 9)]
        pad_means += [qc_df[qc_df['Channel'] == f'BT{i}U']['Mean'].values[0] for i in range(1, 9)]
        x_labels = [f'P{i}L' for i in range(1, 9)] + [f'P{i}U' for i in range(1, 9)]
        ax2.bar(range(len(pad_means)), pad_means, alpha=0.7, edgecolor='black')
        ax2.set_xticks(range(len(x_labels)))
        ax2.set_xticklabels(x_labels, rotation=45, fontsize=8)
        ax2.set_ylabel('Mean Conductivity (MMHO)', fontweight='bold')
        ax2.set_title('Pad Response Balance', fontweight='bold')
        ax2.axhline(global_mean, color='red', linestyle='--', linewidth=2, label='Global mean')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Plot 3: Histogram of conductivity values
        ax3 = fig.add_subplot(gs[1, 1])
        valid_data = image_array[~np.isnan(image_array) & (image_array > 0)]
        ax3.hist(np.log10(valid_data), bins=100, alpha=0.7, edgecolor='black')
        ax3.axvline(np.log10(global_mean), color='red', linestyle='--', linewidth=2, label='Mean')
        ax3.axvline(np.log10(global_p99), color='orange', linestyle='--', linewidth=2, label='P99')
        ax3.set_xlabel('log₁₀(Conductivity) [MMHO]', fontweight='bold')
        ax3.set_ylabel('Frequency', fontweight='bold')
        ax3.set_title('Conductivity Distribution', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # Plot 4: Outliers by depth
        ax4 = fig.add_subplot(gs[1, 2])
        outliers_per_depth = np.sum(outliers, axis=1)
        ax4.plot(outliers_per_depth, zone_depth, linewidth=0.5)
        ax4.set_xlabel('Outlier Buttons', fontweight='bold')
        ax4.set_ylabel('Depth (m)', fontweight='bold')
        ax4.set_title('Outliers vs Depth', fontweight='bold')
        ax4.invert_yaxis()
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Depth sampling
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.hist(depth_diff * 1000, bins=50, alpha=0.7, edgecolor='black')
        ax5.axvline(median_spacing * 1000, color='red', linestyle='--', linewidth=2, 
                   label=f'Median: {median_spacing*1000:.2f}mm')
        ax5.set_xlabel('Depth Spacing (mm)', fontweight='bold')
        ax5.set_ylabel('Frequency', fontweight='bold')
        ax5.set_title('Depth Sampling Distribution', fontweight='bold')
        ax5.grid(True, alpha=0.3)
        ax5.legend()
        
        # Plot 6: Tool orientation
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.plot(zone_p1az, zone_depth, linewidth=0.5, label='P1 Azimuth')
        ax6.set_xlabel('Azimuth (degrees)', fontweight='bold')
        ax6.set_ylabel('Depth (m)', fontweight='bold')
        ax6.set_title('Tool Rotation vs Depth', fontweight='bold')
        ax6.invert_yaxis()
        ax6.grid(True, alpha=0.3)
        ax6.legend()
        
        # Plot 7: Caliper (if available)
        if caliper_x is not None:
            ax7 = fig.add_subplot(gs[2, 2])
            ax7.plot(zone_calx, zone_depth, linewidth=0.5, label='Cal X', alpha=0.7)
            ax7.plot(zone_caly, zone_depth, linewidth=0.5, label='Cal Y', alpha=0.7)
            ax7.axvline(median_bit, color='red', linestyle='--', linewidth=2, 
                       label=f'Bit: {median_bit:.1f}"')
            ax7.set_xlabel('Caliper (inches)', fontweight='bold')
            ax7.set_ylabel('Depth (m)', fontweight='bold')
            ax7.set_title('Borehole Caliper', fontweight='bold')
            ax7.invert_yaxis()
            ax7.grid(True, alpha=0.3)
            ax7.legend()
        
        plt.suptitle('CMI Button Data Quality Control Report', 
                    fontsize=14, fontweight='bold', y=0.995)
        
        output_file = 'CMI_QC_Report.png'
        plt.savefig(output_file, dpi=200, bbox_inches='tight')
        print(f"✓ QC plots saved to: {output_file}")
        
        output_pdf = 'CMI_QC_Report.pdf'
        plt.savefig(output_pdf, bbox_inches='tight')
        print(f"✓ QC plots saved to: {output_pdf}")
        
        # Save QC statistics
        qc_csv = 'CMI_QC_Statistics.csv'
        qc_df.to_csv(qc_csv, index=False, float_format='%.2f')
        print(f"✓ QC statistics saved to: {qc_csv}")
        
        print(f"\n{'='*80}")
        print("QC SUMMARY & RECOMMENDATIONS")
        print(f"{'='*80}")
        
        # Overall QC assessment
        issues = []
        
        if qc_df['Valid%'].min() < 95:
            issues.append(f"⚠ Low data quality on some channels (min {qc_df['Valid%'].min():.1f}%)")
        
        if np.sum(outliers) / outliers.size > 0.01:
            issues.append(f"⚠ Significant outliers detected ({100*np.sum(outliers)/outliers.size:.2f}%)")
        
        if washout_pct > 10:
            issues.append(f"⚠ Washout zones affect {washout_pct:.1f}% of interval")
        
        if len(issues) == 0:
            print("✓ DATA QUALITY: EXCELLENT - No major issues detected")
            print("\nRecommendations:")
            print("  - Data ready for image generation")
            print("  - No preprocessing required")
        else:
            print("⚠ DATA QUALITY ISSUES DETECTED:")
            for issue in issues:
                print(f"  {issue}")
            print("\nRecommendations:")
            if np.sum(outliers) / outliers.size > 0.01:
                print(f"  1. Clip outliers to {outlier_threshold:.0f} MMHO before imaging")
            if washout_pct > 10:
                print(f"  2. Flag washout zones - button contact may be poor")
                print(f"  3. Consider filtering data where caliper > {washout_threshold:.1f}\"")
            print(f"  4. Review image quality in problem zones")

print("\n" + "="*80)
print("✓ CMI QC COMPLETE!")
print("="*80 + "\n")
