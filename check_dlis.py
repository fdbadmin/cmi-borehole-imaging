#!/usr/bin/env python3
"""
Check DLIS File Contents
Examine what curves and data are available in the BHI DLIS file
"""

try:
    from dlisio import dlis
    import pandas as pd
    
    print("\n" + "="*80)
    print("DLIS FILE INSPECTION")
    print("="*80)
    
    # Load DLIS file
    dlis_file = 'Raw dataset/qgc_anya-105_mcg-cmi.dlis'
    
    with dlis.load(dlis_file) as files:
        for f in files:
            print(f"\n{'='*80}")
            print(f"File: {f.describe()}")
            print(f"{'='*80}")
            
            # List all frames (log datasets)
            print(f"\nFrames (Log Datasets): {len(f.frames)}")
            for i, frame in enumerate(f.frames):
                print(f"\n--- Frame {i+1}: {frame.name} ---")
                print(f"Description: {frame.description}")
                print(f"Index Type: {frame.index_type}")
                try:
                    print(f"Depth Interval: {frame.index_min} to {frame.index_max}")
                except:
                    pass
                print(f"Number of Channels: {len(frame.channels)}")
                
                print(f"\nChannels (Curves):")
                for j, channel in enumerate(frame.channels):
                    try:
                        units = channel.units if hasattr(channel, 'units') else ''
                        long_name = channel.long_name if hasattr(channel, 'long_name') else ''
                        print(f"  {j+1:2d}. {channel.name:20s} | {str(long_name):40s} | {units}")
                    except:
                        print(f"  {j+1:2d}. {channel.name}")
                    
                # Show depth range
                try:
                    curves = frame.curves()
                    print(f"\nData Points: {len(curves)} samples")
                    if len(curves) > 0:
                        depth_col = curves.columns[0]
                        print(f"Depth Range: {curves[depth_col].min():.2f} to {curves[depth_col].max():.2f}")
                except Exception as e:
                    print(f"Could not load curve data: {e}")
            
            # List all channels globally
            print(f"\n{'='*80}")
            print(f"All Channels in File: {len(f.channels)}")
            print(f"{'='*80}")
            for i, channel in enumerate(f.channels[:30]):  # First 30
                print(f"{i+1:3d}. {channel.name:20s} | {channel.long_name:50s} | {channel.units}")
            
            if len(f.channels) > 30:
                print(f"\n... and {len(f.channels) - 30} more channels")
                
    print("\n" + "="*80)
    print("✓ DLIS inspection complete!")
    print("="*80 + "\n")
    
except ImportError:
    print("\n" + "="*80)
    print("⚠ dlisio package not installed")
    print("="*80)
    print("\nTo read DLIS files, install dlisio:")
    print("  pip install dlisio")
    print("\nAlternatively, the DLIS could be converted to LAS format.")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n⚠ Error reading DLIS file: {e}")
    print("\nThe file may need to be converted to LAS format first.")
