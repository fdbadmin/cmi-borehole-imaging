# CMI Borehole Image Processing and Coal Seam Detection

Automated processing of Weatherford CMI (Circumferential Microresistivity Imager) borehole imaging data with coal seam detection for Coal Seam Gas (CSG) reservoir evaluation.

**Well:** Anya 105  
**Basin:** Surat Basin, Queensland, Australia  
**Reservoir:** Walloon Coal Measures (233.3-547.0m)  
**Tool:** Weatherford CMI (176 buttons, 8 pads @ 45° spacing)

## Quick Start

### Run Complete Analysis Pipeline

```bash
# Activate virtual environment
source .venv/bin/activate

# Run end-to-end pipeline (< 10 seconds if CMI already processed)
python run_coal_analysis.py
```

**Output:**
- `Coal_Analysis_Results/Coal_Seams_Final.csv` - Detected coal seams with depths/thicknesses
- `Coal_Analysis_Results/Coal_Analysis_Summary.png/pdf` - 4-track visualization
- `Coal_Analysis_Results/ANALYSIS_SUMMARY.md` - Complete summary report
- `Coal_Analysis_Results/Coal_by_Formation.csv` - Coal distribution by formation

### Results Summary

**Reservoir:** 313.7m gross thickness  
**Coal Seams:** 72 detected  
**Net Coal:** 34.28m (10.9% NTG)  
**Top Formation:** Taroom Coal Measures (15.35m, 11.0% NTG)

| Formation | Seams | Coal (m) | NTG (%) |
|-----------|-------|----------|---------|
| Upper Juandah | 18 | 8.12 | 12.5 |
| Lower Juandah | 24 | 10.81 | 14.1 |
| Taroom | 30 | 15.35 | 11.0 |

## Key Features

✅ **High-resolution detection** - 2mm vertical sampling (vs 1-foot density log)  
✅ **Data-driven cutoffs** - Optimized using Otsu + statistical methods  
✅ **Siderite filtering** - Density log removes false positives  
✅ **Within-pad interpolation** - Preserves data integrity (no cross-pad smoothing)  
✅ **Logarithmic normalization** - Handles wide dynamic range (0-19,460 MMHO)  
✅ **Automated pipeline** - Complete workflow in single command
