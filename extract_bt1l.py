#!/usr/bin/env python3
"""
Extract BT1L Channel from DLIS
Focus on button array structure and data
"""

from dlisio import dlis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

print("\n" + "="*80)
print("EXTRACTING BT1L CHANNEL")
print("="*80)

# Load DLIS file
dlis_file = 'Raw dataset/qgc_anya-105_mcg-cmi.dlis'

with dlis.load(dlis_file) as files:
    for f in files:
        # Get the frame
        frame = f.frames[0]
        print(f"\nFrame: {frame.name}")
        print(f"Depth range: {frame.index_min} to {frame.index_max} m")
        
        # Find BT1L channel
        bt1l_channel = None
        for channel in frame.channels:
            if channel.name == 'BT1L':
                bt1l_channel = channel
                break
        
        if bt1l_channel is None:
            print("❌ BT1L channel not found!")
            exit()
        
        print(f"\n{'='*80}")
        print(f"BT1L CHANNEL DETAILS")
        print(f"{'='*80}")
        print(f"Name: {bt1l_channel.name}")
        print(f"Long Name: {bt1l_channel.long_name}")
        print(f"Units: {bt1l_channel.units}")
        print(f"Dimension: {bt1l_channel.dimension}")
        print(f"Representation Code: {bt1l_channel.reprc}")
        
        # Get the data
        print(f"\n{'='*80}")
        print(f"LOADING DATA")
        print(f"{'='*80}")
        
        curves_data = frame.curves()
        
        # curves_data is a structured numpy array
        print(f"Data type: {type(curves_data)}")
        print(f"Shape: {curves_data.shape}")
        print(f"Dtype names: {curves_data.dtype.names[:10]}...")  # First 10 fields
        
        # Extract DEPTH and BT1L
        depth = curves_data['DEPTH']
        bt1l_data = curves_data['BT1L']
        
        print(f"\nDEPTH array shape: {depth.shape}")
        print(f"BT1L array shape: {bt1l_data.shape}")
        print(f"BT1L data type: {bt1l_data.dtype}")
        
        # Check if BT1L is multi-dimensional (button array)
        if len(bt1l_data.shape) > 1:
            print(f"\n✓ BT1L is a BUTTON ARRAY!")
            print(f"  Array dimensions: {bt1l_data.shape}")
            print(f"  Number of buttons: {bt1l_data.shape[1]}")
            print(f"  Number of depth samples: {bt1l_data.shape[0]}")
        else:
            print(f"\n✓ BT1L is a single curve")
            print(f"  Number of samples: {bt1l_data.shape[0]}")
        
        # Show sample data
        print(f"\n{'='*80}")
        print(f"SAMPLE DATA (First 10 depths)")
        print(f"{'='*80}")
        
        for i in range(min(10, len(depth))):
            if len(bt1l_data.shape) > 1:
                print(f"Depth {depth[i]:7.2f}m: {bt1l_data[i]} (shape: {bt1l_data[i].shape})")
            else:
                print(f"Depth {depth[i]:7.2f}m: {bt1l_data[i]:.4f}")
        
        # Statistics
        print(f"\n{'='*80}")
        print(f"STATISTICS")
        print(f"{'='*80}")
        print(f"Depth range: {depth.min():.2f} to {depth.max():.2f} m")
        print(f"Depth samples: {len(depth)}")
        print(f"Depth sampling: {np.median(np.diff(depth)):.4f} m")
        
        if len(bt1l_data.shape) > 1:
            print(f"\nButton array statistics:")
            print(f"  Min value: {bt1l_data.min():.4f} {bt1l_channel.units}")
            print(f"  Max value: {bt1l_data.max():.4f} {bt1l_channel.units}")
            print(f"  Mean value: {bt1l_data.mean():.4f} {bt1l_channel.units}")
            print(f"  Std dev: {bt1l_data.std():.4f} {bt1l_channel.units}")
            
            # Check for valid data
            valid_data = ~np.isnan(bt1l_data)
            print(f"\nData quality:")
            print(f"  Valid samples: {valid_data.sum()} / {bt1l_data.size} ({100*valid_data.sum()/bt1l_data.size:.1f}%)")
            print(f"  NaN samples: {np.isnan(bt1l_data).sum()}")
            
            # Show button layout
            print(f"\n{'='*80}")
            print(f"BUTTON TABLE STRUCTURE")
            print(f"{'='*80}")
            print(f"Number of buttons per depth level: {bt1l_data.shape[1]}")
            print(f"\nSample at depth {depth[1000]:.2f}m:")
            print(f"Button values: {bt1l_data[1000]}")
            
            # Check zone of interest (Upper Juandah to Eurombah: 233.3-547.0m)
            zone_mask = (depth >= 233.3) & (depth <= 547.0)
            zone_depth = depth[zone_mask]
            zone_data = bt1l_data[zone_mask]
            
            print(f"\n{'='*80}")
            print(f"ZONE OF INTEREST (233.3-547.0m)")
            print(f"{'='*80}")
            print(f"Samples in zone: {len(zone_depth)}")
            print(f"Depth range in zone: {zone_depth.min():.2f} to {zone_depth.max():.2f} m")
            print(f"Data range in zone: {zone_data.min():.4f} to {zone_data.max():.4f} {bt1l_channel.units}")
            
            # Save zone data to CSV
            print(f"\n{'='*80}")
            print(f"SAVING DATA")
            print(f"{'='*80}")
            
            # Reshape the data - it's (samples, 1, 10) so squeeze out middle dimension
            zone_data_2d = zone_data.squeeze()  # Convert from (N, 1, 10) to (N, 10)
            
            # Replace null values (-9999) with NaN
            zone_data_2d[zone_data_2d == -9999] = np.nan
            
            # Create DataFrame with button columns
            df_dict = {'DEPTH': zone_depth}
            
            # Handle different array shapes
            if len(zone_data_2d.shape) == 2:
                num_buttons = zone_data_2d.shape[1]
                for btn in range(num_buttons):
                    df_dict[f'BUTTON_{btn+1}'] = zone_data_2d[:, btn]
            else:
                # Single column
                df_dict['BUTTON_1'] = zone_data_2d
            
            df = pd.DataFrame(df_dict)
            
            # Save to CSV
            output_file = 'BT1L_Button_Data.csv'
            df.to_csv(output_file, index=False, float_format='%.6f')
            print(f"✓ Saved to: {output_file}")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Rows: {len(df)}")
            
            # Create a quick visualization
            print(f"\n{'='*80}")
            print(f"CREATING VISUALIZATION")
            print(f"{'='*80}")
            
            # Use the cleaned 2D data
            plot_data = zone_data_2d.copy()
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 10))
            
            # Plot 1: Button array image
            if len(plot_data.shape) == 2:
                num_buttons = plot_data.shape[1]
                extent = [0.5, num_buttons+0.5, zone_depth.max(), zone_depth.min()]
                im1 = ax1.imshow(plot_data, aspect='auto', extent=extent, 
                                cmap='jet', interpolation='nearest', vmin=0, vmax=np.nanpercentile(plot_data, 99))
                ax1.set_xlabel('Button Number', fontweight='bold')
                ax1.set_ylabel('Depth (m)', fontweight='bold')
                ax1.set_title('BT1L Button Array Image\n(Pad 1 Lower Row)', 
                             fontweight='bold', fontsize=12)
                ax1.grid(True, alpha=0.3)
                plt.colorbar(im1, ax=ax1, label=f'Conductivity ({bt1l_channel.units})')
                
                # Plot 2: Individual button traces
                for btn in range(min(num_buttons, 10)):  # Plot all buttons (max 10)
                    ax2.plot(plot_data[:, btn], zone_depth, 
                            label=f'Button {btn+1}', linewidth=0.5, alpha=0.7)
            else:
                # Single trace
                ax1.plot(plot_data, zone_depth, linewidth=0.8)
                ax1.set_xlabel(f'Conductivity ({bt1l_channel.units})', fontweight='bold')
                ax1.set_ylabel('Depth (m)', fontweight='bold')
                ax1.invert_yaxis()
                
                ax2.plot(plot_data, zone_depth, linewidth=0.8, color='blue')
            
            ax2.set_xlabel(f'Conductivity ({bt1l_channel.units})', fontweight='bold')
            ax2.set_ylabel('Depth (m)', fontweight='bold')
            ax2.set_title('BT1L Individual Button Traces', 
                         fontweight='bold', fontsize=12)
            ax2.invert_yaxis()
            ax2.grid(True, alpha=0.3)
            if len(plot_data.shape) == 2:
                ax2.legend(loc='best', fontsize=8, ncol=2)
            
            plt.tight_layout()
            output_plot = 'BT1L_Button_Display.png'
            plt.savefig(output_plot, dpi=200, bbox_inches='tight')
            print(f"✓ Plot saved to: {output_plot}")
            
        else:
            print(f"Single value per depth - not a button array")

print("\n" + "="*80)
print("✓ BT1L EXTRACTION COMPLETE!")
print("="*80 + "\n")
