# Visualizing Small Risk Values - Quick Reference

## Problem
Your expected deaths values are very small (e.g., 2.47e-04), which makes visualization challenging with standard approaches.

## Solution: Three Optimized Scripts

### 1. **visualize_building_risk.py** - Updated with Smart Scaling
**Best for:** Standard interactive visualization with automatic log scaling

**Key Improvements:**
- ✅ Automatic detection of small values and log scaling
- ✅ Scientific notation in popups and tooltips (e.g., 2.47e-04)
- ✅ Enhanced legend with value range in scientific notation
- ✅ Shows coefficient of variation in popups
- ✅ Displays top 5 highest risk buildings

**Output:** `building_risk_map.html`

**Usage:**
```bash
python visualize_building_risk.py
```

---

### 2. **visualize_risk_percentile.py** - NEW! Percentile-Based (Recommended)
**Best for:** When absolute values are too small to discriminate visually

**Key Features:**
- ✅ **Percentile-based coloring** - Buildings ranked 0-100%
- ✅ **6 Risk Categories:**
  - Very High (Top 5%) - Dark Red
  - High (90-95%) - Crimson
  - Elevated (75-90%) - Orange
  - Moderate (50-75%) - Gold
  - Low-Moderate (25-50%) - Yellow-Green
  - Low (Bottom 25%) - Green
- ✅ Enhanced popups showing both absolute values AND percentile rank
- ✅ Category-wise statistics (buildings, deaths, occupants per category)
- ✅ Better visual discrimination for small values

**Output:** `building_risk_percentile_map.html`

**Usage:**
```bash
python visualize_risk_percentile.py
```

---

### 3. **visualize_risk_static.py** - Updated for Reports
**Best for:** Publication-quality static images

**Key Improvements:**
- ✅ Scientific notation on color bars
- ✅ Value range annotations on plots
- ✅ Formatted statistics output
- ✅ Four analysis views + uncertainty scatter plot

**Outputs:** 
- `building_risk_static_maps.png` (4-panel overview)
- `risk_uncertainty_scatter.png` (mean vs std analysis)

**Usage:**
```bash
python visualize_risk_static.py
```

---

## Comparison: Which Script to Use?

| Scenario | Recommended Script | Why? |
|----------|-------------------|------|
| Values vary by 10x or more | `visualize_building_risk.py` | Auto log-scale handles range |
| Values all very small (<0.001) | `visualize_risk_percentile.py` | Percentiles show relative differences |
| Need publication figures | `visualize_risk_static.py` | High-res PNG with proper formatting |
| Interactive exploration | `visualize_risk_percentile.py` | Best UX with clear categories |
| Quick overview | `visualize_building_risk.py` | Fast, automatic scaling |

---

## Understanding Your Small Values

For values like `expected_deaths_mean = 2.47e-04`:

**What it means:**
- 2.47e-04 = 0.000247 = 0.0247%
- Approximately 2.47 deaths per 10,000 exposures
- Very low absolute risk, but relative comparisons still matter

**Why percentile-based visualization helps:**
- Even if all values are small, some buildings are still riskier than others
- Percentiles show: "This building is in the top 10% of risk"
- Easier to identify priorities for intervention

---

## Example Outputs

### Scientific Notation Display
```
Expected Deaths (Mean): 2.47e-04
Expected Deaths (Std):  5.05e-05
Coefficient of Variation: 0.204
```

### Percentile Display
```
Risk Percentile: 87.3%
Category: Elevated (Top 25%)
```

### Statistics Summary
```
RISK STATISTICS SUMMARY
==============================================================
Total buildings analyzed: 156

Expected Deaths (Mean):
  Min:    1.23e-05
  Max:    4.56e-04
  Mean:   2.34e-04
  Median: 2.15e-04
  Total:  3.65e-02

High-risk buildings (top 10%):
  Count: 16
  Threshold: 3.89e-04
  Total expected deaths: 6.78e-03
```

---

## Interpretation Guide

### For Small Absolute Values

**Focus on relative risk:**
- Don't worry about absolute magnitude
- Compare buildings to each other
- Use percentiles for prioritization

**Key questions to answer:**
1. Which buildings are in the top 10% of risk?
2. How does uncertainty vary across buildings?
3. Are high-risk buildings also high-occupancy?
4. What building characteristics correlate with risk?

### Coefficient of Variation (CV)

CV = Std / Mean measures relative uncertainty:
- **CV < 0.3**: Reliable estimates
- **CV 0.3-0.7**: Moderate uncertainty
- **CV > 0.7**: High uncertainty, need more data

For your example: CV = 5.05e-05 / 2.47e-04 = 0.204 (reliable)

---

## Tips for Analysis

### Prioritization Strategy

1. **Immediate attention (Very High Risk):**
   - Top 5% by expected deaths
   - High occupancy (>50 people)
   - Low uncertainty (CV < 0.5)

2. **Further investigation (High/Elevated):**
   - 75th-95th percentile risk
   - High uncertainty (CV > 0.5)
   - Medium-high occupancy

3. **Monitor (Moderate and below):**
   - Below 75th percentile
   - Lower occupancy
   - Any building characteristics

### Combining Metrics

Best practice: Look at multiple factors
```python
# High priority buildings (example criteria)
priority = (
    (risk_percentile > 90) &  # Top 10% risk
    (num_occupants > 30) &     # More than 30 people
    (cv < 0.5)                 # Reliable estimate
)
```

---

## Troubleshooting

**Problem:** All buildings look the same color
**Solution:** Use `visualize_risk_percentile.py` for better discrimination

**Problem:** Values too small to read
**Solution:** All scripts now use scientific notation (e.g., 2.47e-04)

**Problem:** Can't see relative differences
**Solution:** Percentile-based coloring shows rankings clearly

**Problem:** Need to explain results to non-technical audience
**Solution:** Use percentile categories ("Top 10% risk") instead of absolute values

---

## Next Steps

1. Start with **percentile-based visualization** for best discrimination
2. Generate **static plots** for your report/presentation
3. Use **statistics** to support findings
4. Export high-risk building list for further analysis

## Example Workflow

```bash
# 1. Create percentile-based interactive map
python visualize_risk_percentile.py

# 2. Open the HTML file and explore
firefox building_risk_percentile_map.html

# 3. Generate publication figures
python visualize_risk_static.py

# 4. Review statistics and identify priorities
# Check console output for category distributions
```

---

**Remember:** Even with small absolute values, relative risk matters for prioritization!
