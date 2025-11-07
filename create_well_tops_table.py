"""
Final script to create a clean well tops table from the PDF extraction.
"""

import pandas as pd

# Well tops data extracted from Page 2 of the completion report
well_tops_data = {
    'Formation': [
        'Westbourne Formation',
        'Springbok Sandstone',
        'Upper Juandah Coal Measures',
        'Lower Juandah Coal Measures',
        'Tangalooma Sandstone',
        'Taroom Coal Measures',
        'Eurombah Formation'
    ],
    'Depth_MDRT_m': [
        4.50,
        127.60,
        233.30,
        298.20,
        374.80,
        407.10,
        547.00
    ],
    'Depth_TVDRT_m': [
        4.50,
        127.60,
        233.30,
        298.20,
        374.80,
        407.10,
        547.00
    ],
    'Depth_TVDGL_m': [
        0.00,
        123.10,
        228.80,
        293.70,
        370.30,
        402.60,
        542.50
    ]
}

# Create DataFrame
df = pd.DataFrame(well_tops_data)

# Calculate thickness
df['Thickness_m'] = df['Depth_MDRT_m'].shift(-1) - df['Depth_MDRT_m']
df.loc[df.index[-1], 'Thickness_m'] = None  # Last formation thickness unknown (TD not reached)

# Add well information
well_info = {
    'Well Name': 'Anya 105',
    'Operator': 'QGC',
    'Basin': 'Surat Basin',
    'Total Depth': '580.00 m MDRT',
    'Spud Date': '11-11-2017',
    'TD Date': '12-11-2017',
    'Ground Level': '353.00 m AHD',
    'RT Elevation': '357.50 m AHD'
}

# Display results
print("="*80)
print("WELL TOPS TABLE - ANYA 105")
print("="*80)
print("\nWell Information:")
for key, value in well_info.items():
    print(f"  {key}: {value}")

print("\n" + "="*80)
print("FORMATION TOPS")
print("="*80)
print(df.to_string(index=False))

# Save to CSV
output_csv = "Anya_105_Well_Tops.csv"
df.to_csv(output_csv, index=False)
print(f"\n✓ Well tops table saved to: {output_csv}")

# Also save to Excel with formatting
output_excel = "Anya_105_Well_Tops.xlsx"
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    # Write well info
    pd.DataFrame([well_info]).T.to_excel(writer, sheet_name='Well Info', header=False)
    
    # Write well tops
    df.to_excel(writer, sheet_name='Formation Tops', index=False)

print(f"✓ Well tops table saved to: {output_excel}")

print("\n" + "="*80)
print("NOTES:")
print("="*80)
print("- MDRT: Measured Depth from Rotary Table")
print("- TVDRT: True Vertical Depth from Rotary Table")
print("- TVDGL: True Vertical Depth from Ground Level")
print("- All depths are in meters")
print("- Depths are logger depths from wireline logs")
