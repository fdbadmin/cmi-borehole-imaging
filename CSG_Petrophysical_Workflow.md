# CSG Petrophysical Analysis Workflow - Anya 105
## Industry Standard Workflow for Coal Seam Gas Reservoirs

---

## 📋 EXECUTIVE SUMMARY
**Well**: Anya 105  
**Basin**: Surat Basin, Queensland  
**Target Formations**: Juandah Coal Measures, Taroom Coal Measures  
**Analysis Type**: Coal Seam Gas (CSG) Petrophysical Evaluation  
**Available Data**:
- Wireline logs (GR, Density, Neutron, Resistivity, Sonic, PE)
- Formation tops
- Well completion report

---

## 🎯 WORKFLOW PHASES

### **PHASE 1: DATA LOADING & QC** ✓
#### 1.1 Load LAS Files
- Load wireline log data (MAI-MFE-MSS-MPD-MDN suite)
- Load formation tops from extracted CSV
- Verify depth matching and data integrity

#### 1.2 Data Quality Control
- Identify missing data intervals
- Check for environmental corrections (borehole conditions)
- Validate depth registration between logs
- Check caliper log for washouts/tight holes
- Review logging conditions (mud type, density, temperature)

#### 1.3 Depth Alignment
- Match log depths to formation tops
- Verify MD vs TVD consistency
- Check for depth shifts between logging runs

---

### **PHASE 2: LOG CONDITIONING** ✓
#### 2.1 Environmental Corrections
- Borehole correction (caliper effects on density/neutron)
- Temperature corrections for resistivity
- Mud filtrate invasion corrections

#### 2.2 Normalization
- Gamma Ray normalization (shale baseline)
- Density-Neutron crossplot calibration
- Resistivity baseline establishment

#### 2.3 Smoothing & Despiking
- Remove spurious spikes
- Apply median filtering where appropriate
- Preserve true formation boundaries

---

### **PHASE 3: COAL IDENTIFICATION & ZONATION** ⭐ (CRITICAL FOR CSG)
#### 3.1 Coal Detection Algorithm
**Primary Indicators**:
- **Density**: ρb < 2.0 g/cc (typically 1.3-1.8 g/cc for coal)
- **Neutron Porosity**: φN > 30% (high hydrogen index)
- **Gamma Ray**: GR < 60 API (low radioactivity)
- **Resistivity**: Variable (depends on water saturation)
- **PE (Photoelectric Factor)**: PE < 0.5 (low atomic number)

**Combined Coal Flag**:
```
COAL_FLAG = (RHOB < 2.0) AND (NPHI > 0.30) AND (GR < 60) AND (PE < 0.5)
```

#### 3.2 Coal Quality Classification
- **Bright Coal**: High vitrinite, low ash (ρb < 1.5)
- **Dull Coal**: Lower vitrinite, higher ash (ρb 1.5-1.8)
- **Carbonaceous Shale**: Transitional (ρb 1.8-2.0)

#### 3.3 Coal Seam Delineation
- Identify individual coal seams
- Calculate Net Coal thickness
- Determine coal seam continuity
- Flag interburden (non-coal) intervals

---

### **PHASE 4: COAL PETROPHYSICAL PROPERTIES** ⭐
#### 4.1 Ash Content Calculation
**Method 1: Density-based (Primary)**
```
ASH (%) = (ρb - ρcoal) / (ρash - ρcoal) × 100
Where:
  ρcoal = 1.30-1.35 g/cc (pure coal density)
  ρash = 2.65 g/cc (mineral matter density)
  ρb = bulk density (measured)
```

**Method 2: PE-based (Secondary)**
```
ASH (%) = f(PE, ρb) - requires calibration with core data
```

#### 4.2 Gas Content Estimation
**Langmuir Isotherm Approach**:
```
Gc = VL × P / (PL + P)
Where:
  Gc = Gas content (scf/ton or m³/tonne)
  VL = Langmuir volume (maximum gas capacity)
  P = Reservoir pressure
  PL = Langmuir pressure
```

**Parameters needed**:
- Reservoir pressure profile
- Langmuir parameters (VL, PL) - typically from desorption tests
- Coal rank correlation

#### 4.3 Total Organic Carbon (TOC)
**Passey Method (ΔlogR)**:
```
TOC = (ΔlogR) × 10^(2.297 - 0.1688×LOM)
Where:
  ΔlogR = log10(Rt/Rbaseline) + 0.02×(ΔtF - ΔtFbaseline)
  LOM = Level of Maturity
```

**Schmoker Method (Density)**:
```
TOC (%) = (ρma - ρb) / (ρma - ρTOC) × 100
```

#### 4.4 Permeability Indicators
**Cleat System Analysis**:
- Resistivity anisotropy (horizontal vs vertical)
- Density-Neutron separation (fracture indicator)
- Caliper variations (coal structure)

**Empirical Relations**:
```
k ≈ f(Vitrinite%, Ash%, Depth, Stress)
```

---

### **PHASE 5: WATER SATURATION** ⭐
#### 5.1 Coal-Specific Saturation Models

**Modified Archie Equation** (Limited use in coal):
```
Sw^n = (a × Rw) / (φ^m × Rt)
```
⚠️ **Note**: Traditional Archie often unreliable in coal due to:
- Complex pore structure
- Conductive minerals
- Cleat systems

**Dual Water Model** (Preferred for CSG):
```
Sw = Swb + Swf
Where:
  Swb = Bound water in coal matrix
  Swf = Free water in cleats
```

**Indonesia/Poupon Equation** (For shaly coals):
```
1/√Rt = Swb×Vsh/√Rsh + Swf×φe/√Rw
```

#### 5.2 Critical Water Saturation
- Determine Swcrit for gas production
- Account for irreducible water in coal matrix
- Estimate mobile gas saturation (Sg = 1 - Sw)

---

### **PHASE 6: RESERVOIR CHARACTERIZATION** ⭐
#### 6.1 Net Coal Calculation
**Cutoffs**:
- Density: ρb < 2.0 g/cc
- Ash: < 50%
- Thickness: Individual seams > 0.3 m (1 ft)
- GR: < 60-70 API

**Net-to-Gross Ratio**:
```
NTG = Net Coal Thickness / Gross Interval Thickness
```

#### 6.2 Gas-in-Place (GIP)
**Volumetric Method**:
```
GIP (scf) = A × h × ρcoal × Gc × (1 - Ash/100)
Where:
  A = Drainage area (acres or m²)
  h = Net coal thickness (ft or m)
  ρcoal = Coal density (tons/ft³ or tonnes/m³)
  Gc = Gas content (scf/ton or m³/tonne)
  Ash = Ash content (%)
```

#### 6.3 Completion Quality Analysis
**Per-Seam Evaluation**:
- Gas content potential
- Permeability indicators
- Mechanical properties (for fracturing)
- Stress profile compatibility

---

### **PHASE 7: MULTI-MINERAL ANALYSIS** (Advanced)
#### 7.1 Component Resolution
Using combined logs (GR, RHOB, NPHI, PE, DT):
- Coal (vitrinite, inertinite)
- Clay minerals (kaolinite, illite)
- Quartz/silica
- Carbonates
- Pyrite

#### 7.2 Solver Methods
- Linear inversion
- Probabilistic (Monte Carlo)
- Neural network approaches

---

### **PHASE 8: VISUALIZATION & REPORTING** ✓
#### 8.1 Log Displays
**Track 1**: Depth, Formation Tops, Coal Flags
**Track 2**: Gamma Ray, Caliper
**Track 3**: Resistivity (Deep, Medium, Shallow)
**Track 4**: Density-Neutron Crossover, PE
**Track 5**: Sonic (if available)
**Track 6**: Computed Properties (Ash, Sw, Coal Quality)
**Track 7**: Net Coal Flag, Perforations

#### 8.2 Crossplots
- Density-Neutron (lithology identification)
- Density-PE (coal vs shale)
- M-N Plot (mineralogy)
- Pickett Plot (Sw determination)
- Ash vs Density
- TOC vs Resistivity

#### 8.3 Outputs
- Formation summary table
- Coal seam inventory
- Net coal by formation
- Gas-in-place estimates
- Completion recommendations
- Petrophysical properties by zone

---

### **PHASE 9: INTEGRATION & VALIDATION**
#### 9.1 Core Calibration
- Compare log-derived ash with core measurements
- Validate gas content with desorption data
- Calibrate density-porosity transforms

#### 9.2 Production Correlation
- Gas production vs log properties
- Water production vs saturation
- Well performance indicators

#### 9.3 Geological Consistency
- Verify with stratigraphic framework
- Check lateral continuity expectations
- Validate against offset wells

---

## 📊 KEY DELIVERABLES

### Quantitative Outputs:
1. **Coal Inventory Table**
   - Formation, Top/Base Depth, Gross/Net Thickness, Ash%, Gas Content
   
2. **Petrophysical Summary**
   - Average properties per zone
   - Statistical distribution (P10/P50/P90)
   
3. **Gas-in-Place Estimate**
   - Deterministic and probabilistic
   
4. **Completion Recommendations**
   - Target intervals
   - Perforation strategy
   
5. **Quality Indicators**
   - Coal rank proxies
   - Producibility indices

### Graphical Outputs:
1. **Composite Log Display** (1:200 or 1:500 scale)
2. **Crossplot Suite** (5-7 key plots)
3. **Formation Summary Chart**
4. **3D Property Distribution** (if multiple wells)

---

## 🛠️ PYTHON IMPLEMENTATION TOOLS

### Required Libraries:
```python
- lasio          # LAS file I/O
- pandas         # Data manipulation
- numpy          # Numerical computation
- matplotlib     # Plotting
- plotly         # Interactive visualization
- scipy          # Scientific computing
- scikit-learn   # Machine learning (clustering)
- welly          # Well log analysis
```

### Custom Modules to Build:
1. `coal_detector.py` - Coal identification algorithms
2. `ash_calculator.py` - Ash content from logs
3. `saturation_models.py` - Water saturation for coal
4. `gas_content.py` - Gas content estimation
5. `net_coal.py` - Net pay calculation
6. `log_plotter.py` - Industry-standard log plots
7. `crossplot_suite.py` - Automated crossplot generation

---

## ⚠️ CSG-SPECIFIC CONSIDERATIONS

### Critical Differences from Conventional Reservoirs:
1. **Matrix vs Cleat System**: Dual porosity behavior
2. **Gas Storage**: Adsorbed on coal surface (not free gas)
3. **Production Mechanism**: Desorption + dewatering required
4. **Permeability**: Dominated by cleat system, stress-sensitive
5. **Water Saturation**: Often >50%, water production essential
6. **Heterogeneity**: High variability in coal properties

### Quality Control Flags:
- Washouts (caliper > bit size + 2")
- Low ash coal (ρb < 1.5 g/cc) - high quality
- Thick continuous seams (> 2m) - prime targets
- Low clay content (GR < 40 API) - better permeability

---

## 📈 SUCCESS METRICS

### Analysis Quality Indicators:
- ✓ Coal identification accuracy > 95% (vs core/cuttings)
- ✓ Ash content within ±5% of core data
- ✓ Net coal thickness within ±10% of core
- ✓ Consistent with geological model
- ✓ Reproducible methodology

### Business Value:
- Accurate reserves estimation
- Optimized completion design
- Reduced uncertainty in production forecasts
- Better field development planning

---

## 🔄 RECOMMENDED IMPLEMENTATION SEQUENCE

### **Quick Start (2-3 hours)**:
1. Load LAS files ✓
2. QC & visualization ✓
3. Basic coal detection ✓
4. Net coal calculation ✓
5. Simple log plot ✓

### **Standard Analysis (1 day)**:
1-5 above, plus:
6. Ash content calculation ✓
7. Formation-based summaries ✓
8. Crossplot suite ✓
9. Detailed log display ✓

### **Advanced Analysis (2-3 days)**:
1-9 above, plus:
10. Water saturation modeling ✓
11. Gas content estimation ✓
12. Multi-mineral analysis ✓
13. Completion optimization ✓
14. Full report generation ✓

---

## 🎓 INDUSTRY STANDARDS & REFERENCES

### Standards:
- SPE Petroleum Resources Management System (PRMS)
- API RP 40 - Core Analysis Procedures
- SPWLA Best Practices in Shaly Sand Analysis

### Key CSG References:
- Scott, A.R. (2002) - "Hydrogeologic factors affecting gas content distribution"
- Laubach, S.E. (1998) - "Fracture networks in coal"
- Bustin, R.M. (2008) - "CBM reservoir characteristics"

### Regional (Surat Basin):
- Queensland Government Coal Seam Gas standards
- APLNG Technical Standards
- Local calibration data for Walloons/Juandah formations

---

## ✅ NEXT STEPS - YOUR DECISION

**Option A: Quick Start Implementation**
- Get basic results in 2-3 hours
- Coal identification, net coal, basic plots
- Good for initial screening

**Option B: Standard Full Analysis**
- Comprehensive results in 1 day
- All key petrophysical properties
- Publication-quality outputs

**Option C: Advanced + Machine Learning**
- Sophisticated analysis
- Predictive models
- Multi-well integration

**Which approach would you like to implement first?**

---

*Generated: November 2025*  
*Well: Anya 105, Surat Basin, Queensland*  
*Analysis Type: Coal Seam Gas Petrophysical Evaluation*
