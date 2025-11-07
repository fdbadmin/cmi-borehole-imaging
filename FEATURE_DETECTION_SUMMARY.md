# CMI Feature Detection Summary

## Overview
Automated detection of geological features from CMI borehole imaging data for Anya 105 well, Walloon Coal Measures.

**Analysis Date:** 2024  
**Reservoir Interval:** 233.3 - 547.0 m (313.7 m gross)  
**Vertical Resolution:** 2 mm  
**Total Samples:** 156,851 depths × 360° azimuth

---

## Detection Results

### Fractures
- **Total Detected:** 954 fractures
- **Average Length:** 0.122 m
- **Length Range:** 0.050 - 2.348 m (minimum threshold: 5 cm)
- **Azimuth Distribution:** 10° - 351° (full azimuthal coverage)
- **Average Conductivity:** Varies by fracture (extracted from CMI)

**Interpretation:**
- High fracture density indicates naturally fractured reservoir
- Azimuthal distribution suggests multiple fracture sets
- Longer fractures (>1m) may represent through-going features
- Fracture-associated zones likely have enhanced permeability

### Bedding Planes
- **Total Detected:** 914 bedding planes
- **Average Spacing:** 0.343 m (34.3 cm)
- **Spacing Range:** 0.098 - 5.522 m
- **Azimuthal Coverage:** 100% (continuous horizontal features)
- **Average Conductivity:** Varies by bedding plane

**Interpretation:**
- Well-defined bedding with ~34 cm average spacing
- Consistent horizontal features across full azimuth
- May represent coal/shale interbedding
- Bedding boundaries = potential flow barriers/baffles

### Faults
- **Total Detected:** 0 faults

**Interpretation:**
- No major faults detected with current criteria (95th percentile contrast)
- May indicate unfaulted reservoir section
- Alternatively, fault detection threshold may need adjustment
- Smaller-scale offsets may exist below detection threshold

---

## Methodology

### Fracture Detection
**Approach:** Vertical feature detection using horizontal Sobel gradient
1. Calculate horizontal gradient (∂/∂azimuth)
2. Threshold: 75th percentile of |gradient|
3. Morphological cleanup (binary opening → closing)
4. Connected component labeling
5. Filter by minimum length (5 cm) and pixel count (≥10 pixels)
6. Extract: depth extent, length, azimuth, conductivity

**Why horizontal gradient?** High horizontal gradient indicates vertical features (fractures).

### Bedding Detection
**Approach:** Horizontal feature detection using vertical Sobel gradient
1. Calculate vertical gradient (∂/∂depth)
2. Threshold: 80th percentile of |gradient|
3. Analyze azimuthal continuity (must cover >90° of borehole)
4. Smooth gradient profile (Gaussian σ=5)
5. Peak finding: scipy.signal.find_peaks
   - Height threshold: 70th percentile of gradient
   - Minimum spacing: 10 cm
6. Extract: depth, gradient strength, conductivity, azimuthal coverage

**Why vertical gradient?** High vertical gradient indicates horizontal features (bedding).

### Fault Detection
**Approach:** Lateral conductivity contrast analysis
1. Calculate azimuthal gradient for each depth (circular with wrap-around)
2. Threshold: 95th percentile of |lateral gradient|
3. Find vertical continuity (minimum 0.5 m extent)
4. Calculate conductivity contrast across feature (±5° window)
5. Check for nearby fractures (fault association)
6. Filter by contrast: >75th percentile

**Why lateral contrast?** Faults show abrupt conductivity changes across fault plane.

---

## Key Parameters

### Image Preprocessing
- **Gap Filling:** Linear interpolation for missing data
- **Normalization:** 0-255 uint8 for image processing
- **Edge Detection:** Canny (sigma=2.0, thresholds 30-100)

### Fracture Criteria
- Minimum length: 5 cm
- Minimum pixel count: 10 pixels
- Orientation: High-angle (>60° from horizontal)
- Gradient threshold: P75

### Bedding Criteria
- Minimum azimuthal coverage: 90° (25% of borehole)
- Minimum spacing: 10 cm
- Orientation: Low-angle (<30° from horizontal)
- Gradient threshold: P80

### Fault Criteria
- Minimum vertical extent: 0.5 m
- Conductivity contrast threshold: P75
- Lateral gradient threshold: P95

---

## Output Files

### CSV Files
1. **Fractures_Detected.csv** (954 records)
   - Columns: Top_m, Base_m, Length_m, Azimuth_deg, Azimuth_span_deg, Orientation_deg, AvgConductivity, PixelCount
   
2. **Bedding_Detected.csv** (914 records)
   - Columns: Depth_m, GradientStrength, AvgConductivity, AzimuthalCoverage_pct, ApparentDip_deg

3. **Faults_Detected.csv** (if any detected)
   - Columns: Top_m, Base_m, Height_m, Azimuth_deg, ConductivityContrast, FractureAssociation

### Visualizations
- **Feature_Detection_Results.png/pdf** - 6-panel comprehensive analysis
  - Panel 1: CMI image with feature overlays (cyan=bedding, red=fractures, yellow=faults)
  - Panel 2: Canny edge detection
  - Panel 3: Gradient magnitude
  - Panel 4: Vertical gradient (bedding) with overlays
  - Panel 5: Horizontal gradient (fractures) with overlays
  - Panel 6: Statistics summary

---

## Reservoir Implications

### Fracture Network
- **954 detected fractures** indicate extensive natural fracturing
- **Average spacing:** ~33 cm between fractures (313.7m / 954)
- **Full azimuthal coverage** suggests isotropic fracture network
- **CSG Production Impact:**
  - Enhanced permeability pathways
  - Potential sweet spots for well targeting
  - Gas migration routes

### Bedding/Stratigraphy
- **914 bedding planes** with 34 cm average spacing
- Likely represents coal/shale interbedding typical of Walloon Coal Measures
- **Flow Implications:**
  - Horizontal bedding = flow barriers (low vertical permeability)
  - Compartmentalization potential
  - Pressure communication limited between beds

### Structural Complexity
- **No major faults detected** suggests relatively simple structure
- Unfaulted reservoir = better lateral continuity
- May enhance predictability of gas distribution

---

## Recommendations

### Next Steps
1. **Validate fracture orientations** against core data (if available)
2. **Correlate fractures with production data** - identify high-productivity zones
3. **Integrate with coal seam analysis** - fracture-coal intersection = sweet spots
4. **Refine fault detection** - lower threshold to detect subtle features
5. **Dip analysis** - implement sinusoid fitting for apparent dip calculation

### Advanced Analysis
1. **Fracture density maps** - spatial distribution of fractures
2. **Fracture aperture estimation** - conductivity contrast analysis
3. **Natural vs induced fracture classification** - orientation/conductivity patterns
4. **3D structural model** - if multiple wells available

### Quality Control
1. Compare bedding spacing with core measurements
2. Verify fracture azimuths with image log QC
3. Cross-check with drilling parameters (mud losses, kicks)
4. Validate conductivity anomalies against other logs

---

## Technical Notes

### Dependencies
- Python 3.9.6
- Libraries: numpy, pandas, matplotlib, scipy, scikit-image
- Input: CMI_NoInterpolation_Image.csv (from cmi_no_interpolation.py)

### Processing Time
- ~10-15 seconds for full analysis (156,851 samples)
- Edge detection: ~2-3 seconds
- Feature extraction: ~5-8 seconds
- Visualization: ~2-3 seconds

### Limitations
1. **Resolution:** Limited by 2mm CMI sampling (smaller features not detected)
2. **Azimuthal bias:** Single well = no true dip, only apparent dip
3. **Conductivity range:** Only detects conductive features (resistive features missed)
4. **Threshold sensitivity:** Results depend on percentile thresholds chosen
5. **No ground truth:** Validation requires core/other data

---

## Related Analyses
- **Coal Seam Detection:** detect_coal_seams.py (72 seams, 34.28m net coal)
- **CMI Processing:** cmi_no_interpolation.py (within-pad interpolation)
- **Cutoff Optimization:** optimize_conductivity_cutoff.py (conductivity=178)

---

## Contact
For questions about this analysis, refer to the GitHub repository:
https://github.com/fdbadmin/cmi-borehole-imaging

Branch: `feature/image-analysis`  
Script: `detect_features.py`
