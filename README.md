# CMI Borehole Image Processing - Anya 105 Well

Coal Seam Gas (CSG) petrophysical analysis with Weatherford CMI (Circumferential Microresistivity Imager) processing from raw button data.

## Project Overview

Analysis of Anya 105 well (QGC operator, Surat Basin, Queensland) targeting the Walloon Coal Measures for CSG evaluation. This project processes raw CMI borehole imaging data to create high-resolution resistivity images for coal and fracture identification.

**Zone of Interest:** 233.3 - 547.0m (313.7m interval)  
**Vertical Resolution:** 2mm (156,851 depth samples)  
**Tool Configuration:** 8 pads at 45° spacing, 176 total buttons

## Key Scripts

### CMI Image Processing
- **`cmi_no_interpolation.py`** - Main processing script
  - Extracts raw button data from DLIS file
  - Speed and pad normalization
  - Within-pad interpolation (preserves real gaps between pads)
  - Logarithmic normalization for optimal contrast
  - Outputs: `CMI_NoInterpolation.png/pdf`, `CMI_NoInterpolation_Image.csv`

### Comparison & Validation
- **`plot_cmi_processed.py`** - Display vendor-processed CMI_DYN and CMI_STAT images
- **`verify_resolution.py`** - Generate resolution verification plots
  - 4 × 5m zoom windows at different depths
  - 1m ultra-zoom showing individual 2mm samples
  - Side-by-side comparison with vendor processing

### Analysis Tools
- **`plot_logs.py`** - 7-track wireline log display
- **`quick_start_analysis.py`** - Coal detection from wireline logs
- **`qc_button_data.py`** - CMI data quality control

### Diagnostic Tools
- **`diagnose_interpolation.py`** - Analyze interpolation smoothing effects
- **`process_cmi_buttons.py`** - Full processing with cross-pad interpolation (experimental)

## Processing Workflow

1. **Data Extraction**
   - Load DLIS file: `qgc_anya-105_mcg-cmi.dlis`
   - Extract 16 button channels (BT1L-BT8U)
   - Filter to zone of interest (233.3-547.0m)

2. **Speed Correction**
   - Normalize for logging speed variations (4.4-4.9 m/hr)
   - Median speed: 4.7 m/hr

3. **Pad Normalization**
   - Equalize response between 8 pads
   - Correction factors: 0.94-1.11×

4. **Azimuthal Unwrapping**
   - Map buttons to 360° azimuthal image
   - Button 0 at +10°, Button N-1 at -10° (reversed from initial)
   - Each pad covers ~20° span

5. **Within-Pad Interpolation**
   - Smooth interpolation across each pad's button array
   - NO interpolation between pads (preserves real gaps)
   - Coverage: 44.3% (vs 24.4% button-only, 55.7% gaps)

6. **Logarithmic Normalization**
   - Log10 transformation for wide dynamic range
   - P01-P99 clipping in log space
   - Normalize to 0-255 intensity scale

## Key Results

### Data Quality (from QC analysis)
- ✅ 100% data availability
- ✅ Perfect pad balance (ratios 0.99-1.05)
- ✅ Minimal outliers (0.17%)
- ✅ Perfect 2mm depth sampling
- ✅ Excellent borehole condition (8.4-8.5" in 8.5" hole)
- ✅ Zero washouts

### Processing Statistics
- **Raw data range:** 0 - 19,460 MMHO
- **Dynamic range:** 133× (median-to-max)
- **Normalized mean:** 204.5 (0-255 scale)
- **Normalized median:** 216.4

### Coverage Analysis
- **Button measurements:** 24.4%
- **After within-pad interp:** 44.3%
- **Inter-pad gaps:** 55.7%

## File Structure

```
Log Analysis/
├── Raw dataset/
│   ├── qgc_anya-105_mcg-cmi.dlis          # CMI imaging data
│   ├── qgc_anya_105_mai_*.las             # Wireline logs
│   └── qgc-anya-105_cmi_logs.pdf          # Vendor plots
├── cmi_no_interpolation.py                # Main CMI processor
├── plot_cmi_processed.py                  # Vendor image display
├── verify_resolution.py                   # Resolution verification
├── plot_logs.py                           # Wireline log plotter
├── quick_start_analysis.py                # Coal detection
├── qc_button_data.py                      # CMI QC
└── diagnose_interpolation.py              # Diagnostic tool
```

## Dependencies

```python
dlisio          # DLIS file reading
lasio           # LAS file reading
numpy           # Numerical processing
pandas          # Data handling
matplotlib      # Plotting
scipy           # Interpolation & filtering
```

Install with:
```bash
pip install dlisio lasio numpy pandas matplotlib scipy
```

## Usage

### Process CMI Image
```bash
python cmi_no_interpolation.py
```
Outputs:
- `CMI_NoInterpolation.png` - Image with within-pad interpolation
- `CMI_NoInterpolation_Image.csv` - Full processed data (156,851 × 360)

### Verify Resolution
```bash
python verify_resolution.py
```
Outputs:
- `CMI_Resolution_Verify_*.png` - 4 zoom windows (5m each)
- `CMI_Resolution_UltraZoom_1m.png` - 1m ultra-zoom

### Display Vendor Processing
```bash
python plot_cmi_processed.py
```
Outputs:
- `CMI_Processed_Images.png` - CMI_DYN, CMI_STAT, and detail zoom

## Key Design Decisions

### Why Within-Pad Interpolation Only?
- **Honest representation** - Shows real tool coverage limitations
- **Preserves data integrity** - No artificial features in gaps
- **Clear gaps** - White stripes show where we have NO measurements
- **Smooth where valid** - Interpolation within each pad's 10-12 buttons

### Why Logarithmic Normalization?
- **Wide dynamic range** - 0 to 19,460 MMHO (133× median-to-max)
- **Physical basis** - Conductivity response is inherently logarithmic
- **Better contrast** - Enhances subtle features in coal (low conductivity)
- **Industry standard** - Common for resistivity/conductivity imaging

### Why Reversed Button Numbering?
- **Vendor convention match** - Button 0 at +10°, not -10°
- **Empirical verification** - Compared to CMI_DYN at multiple depths
- **Pattern consistency** - Features align between our processing and vendor

## Comparison with Vendor Processing

| Feature | Our Processing | Vendor (CMI_DYN) |
|---------|---------------|------------------|
| Coverage | 44.3% (honest gaps) | 100% (fully interpolated) |
| Normalization | Independent log scale | Proprietary |
| Mean intensity | 204.5 | 132.2 |
| Vertical resolution | Full 2mm | Full 2mm |
| Azimuth bins | 360 (1° each) | 360 (1° each) |
| Processing | Transparent | Proprietary |

## Technical Notes

### Button Geometry
- **Pad spacing:** 45° (8 pads around borehole)
- **Button span per pad:** ~20°
- **Inter-pad gap:** ~25° (NO data)
- **Buttons per pad:** 10-12 (varies by pad)

### Coordinate System
- **P1AZ:** Azimuth of Pad 1 reference
- **Pad offsets:** 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°
- **Button offset:** +span/2 to -span/2 (reversed from initial)

### Known Limitations
- **55.7% gaps** - Real limitation of 8-pad tool geometry
- **Interpolation smoothing** - Within each pad's 20° span
- **Outlier handling** - P01-P99 clipping may miss extreme events

## Future Enhancements

- [ ] CLAHE (Contrast Limited Adaptive Histogram Equalization)
- [ ] Pad-by-pad adaptive normalization
- [ ] Fracture detection algorithms
- [ ] Coal thickness estimation from images
- [ ] Integration with wireline log analysis
- [ ] Automated bedding dip calculation

## References

- **Well:** Anya 105, QGC Operator
- **Basin:** Surat Basin, Queensland, Australia
- **Target:** Walloon Coal Measures (CSG)
- **Tool:** Weatherford CMI (Circumferential Microresistivity Imager)
- **Zone:** 233.3-547.0m MD

## License

Analysis for internal petrophysical evaluation.

## Author

Petrophysical analysis and CMI processing workflow development.
