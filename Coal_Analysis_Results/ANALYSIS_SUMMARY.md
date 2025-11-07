# Coal Seam Analysis Summary
**Date:** 2025-11-07 11:12:45  
**Well:** Anya 105  
**Basin:** Surat Basin, Queensland, Australia  
**Reservoir:** Walloon Coal Measures

## Analysis Parameters

| Parameter | Value |
|-----------|-------|
| **Conductivity Cutoff** | 178 (Otsu-Median midpoint) |
| **Density Cutoff** | 2.5 g/cc (siderite exclusion) |
| **Minimum Seam Thickness** | 10 cm |
| **CMI Vertical Resolution** | 2 mm |
| **Density Log Resolution** | ~1 foot |

## Reservoir Summary

| Metric | Value |
|--------|-------|
| **Reservoir Top** | 233.3 m |
| **Reservoir Base** | 547.0 m |
| **Gross Thickness** | 313.7 m |
| **Number of Coal Seams** | 72 |
| **Total Coal Thickness** | 34.28 m |
| **Net-to-Gross** | 10.9% |
| **Average Seam Thickness** | 0.476 m |
| **Thickest Seam** | 2.454 m |
| **Thinnest Seam** | 0.102 m |

## Coal Distribution by Formation

| Formation | Top (m) | Base (m) | Gross (m) | Seams | Coal (m) | NTG (%) |
|-----------|---------|----------|-----------|-------|----------|---------|
| Upper Juandah Coal Measures    |   233.3 |    298.2 |      64.9 |    18 |     8.12 |    12.5 |
| Lower Juandah Coal Measures    |   298.2 |    374.8 |      76.6 |    24 |    10.81 |    14.1 |
| Tangalooma Sandstone           |   374.8 |    407.1 |      32.3 |     0 |     0.00 |     0.0 |
| Taroom Coal Measures           |   407.1 |    547.0 |     139.9 |    30 |    15.35 |    11.0 |

## Top 10 Thickest Seams

| Rank | Top (m) | Base (m) | Thickness (m) | Avg Conductivity |
|------|---------|----------|---------------|------------------|
|    1 |  249.50 |   251.95 |         2.454 |             76.8 |
|    2 |  528.66 |   530.86 |         2.200 |            109.1 |
|    3 |  447.75 |   449.26 |         1.506 |            132.4 |
|    4 |  309.25 |   310.72 |         1.472 |            106.7 |
|    5 |  530.98 |   532.20 |         1.222 |            105.7 |
|    6 |  339.64 |   340.74 |         1.094 |            137.8 |
|    7 |  409.00 |   410.06 |         1.060 |            127.5 |
|    8 |  348.42 |   349.27 |         0.844 |            149.3 |
|    9 |  359.77 |   360.61 |         0.838 |            141.0 |
|   10 |  415.39 |   416.23 |         0.834 |             90.9 |

## Files Generated

- `Coal_Seams_Final.csv`
- `Coal_Analysis_Summary.png`
- `Coal_Analysis_Summary.pdf`
- `Conductivity_Cutoff_Optimization.png`
- `Conductivity_Cutoff_Optimization.pdf`
- `Coal_Cutoff_Optimization.png`
- `Coal_Cutoff_Optimization.pdf`

## Methodology

### CMI Processing
1. Extract raw button data from DLIS file (176 buttons, 8 pads)
2. Apply speed correction (median 4.7 m/hr)
3. Normalize pads to global median
4. Azimuthal unwrapping with within-pad interpolation only
5. Logarithmic normalization (handles 0-19,460 MMHO range)

### Coal Detection
1. Calculate azimuthal average conductivity (44.3% coverage)
2. Apply 5cm Gaussian smoothing
3. Detect low conductivity zones (< 178)
4. Exclude siderite bands using density log (RHOB > 2.5 g/cc)
5. Filter connected regions > 10cm thick

### Cutoff Optimization
Conductivity cutoff (178) determined as midpoint between:
- **Otsu method**: 164.2 (minimizes within-class variance)
- **Median of methods**: 191.2 (consensus of 5 statistical methods)

This provides balanced detection: conservative enough to ensure high confidence,
aggressive enough to capture thin seams visible only in high-resolution CMI data.
