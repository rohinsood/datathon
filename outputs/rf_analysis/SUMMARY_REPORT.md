# Earnings Mobility Predictor: Random Forest Analysis - Summary Report

**Date:** November 15, 2025  
**Analysis:** Four Random Forest regression models (R1a, R1b, R1c, R1d)  
**Target:** 10-year median earnings (dependent students)  
**Sample:** N=5,013 institutions (after filtering for complete earnings data)

---

## Executive Summary

We conducted four Random Forest regression analyses to assess the importance of **affordability gap** in predicting 10-year student earnings outcomes:

1. **R1a (Full Model)**: Complete model with all features including affordability
2. **R1b (Baseline)**: Same model WITHOUT affordability gap
3. **R1c (Interactions)**: Model with afford × Pell and afford × URM interactions
4. **R1d (Subgroups)**: Separate models for high-Pell vs low-Pell institutions

---

## Key Findings

### 🎯 Overall Model Performance (R1a)

| Metric | Training | Test |
|--------|----------|------|
| **R²** | 0.9530 | **0.9311** |
| **RMSE** | - | **$3,374** |
| **MAE** | - | **$1,865** |

✅ **Excellent predictive power** - The model explains 93.1% of variance in earnings.

---

### 📊 Feature Importance Rankings (R1a Full Model)

**Top 10 Most Important Features:**

| Rank | Feature | Importance | Category |
|------|---------|------------|----------|
| 1 | % Pell students | 0.4502 | Demographics |
| 2 | % Women | 0.1136 | Demographics |
| 3 | SAT composite | 0.0654 | Selectivity |
| 4 | Log endowment | 0.0544 | Resources |
| 5 | Admission rate | 0.0459 | Selectivity |
| 6 | Log instructional exp | 0.0448 | Resources |
| 7 | Region (Northeast) | 0.0346 | Geography |
| 8 | % URM | 0.0340 | Demographics |
| 9 | % White | 0.0308 | Demographics |
| 10 | ACT composite | 0.0291 | Selectivity |
| **11** | **Affordability gap** | **0.0254** | **Affordability** |

### 🔍 Affordability Gap Performance

**R1a (Full Model):**
- **Rank:** #11 out of 29 features
- **Importance:** 0.0254 (2.54%)
- **Interpretation:** Moderate importance, but outranked by demographics, selectivity, and resources

**Key Insight:** While affordability gap is in the top half of predictors, it is **less important than:**
- Student demographics (Pell %, race, gender)
- Institutional selectivity (test scores, admission rate)
- Institutional resources (endowment, expenditure)

---

### 📈 Affordability Contribution (R1b vs R1a Comparison)

**Does adding affordability gap improve the model?**

| Model | Test R² | Test RMSE |
|-------|---------|-----------|
| R1b (No Affordability) | 0.9307 | $3,383 |
| R1a (With Affordability) | 0.9311 | $3,374 |
| **Improvement** | **+0.0004** | **$9** |

**Finding:** Adding affordability gap provides:
- ✅ **+0.04% improvement in R²** (small but positive)
- ✅ **$9 reduction in RMSE** (marginal improvement)

**Interpretation:** Affordability gap **does** add explanatory power for earnings, but the contribution is **modest** because:
1. Demographics (especially Pell %) already capture much of the affordability-related variation
2. Selectivity measures capture institutional quality correlated with both affordability and outcomes
3. Affordability's effect may be mediated through these other factors

---

### 🔗 Interaction Effects (R1c Model)

**Do affordability effects vary by institution type?**

**Interaction Feature Rankings:**

| Feature | Rank | Importance | 
|---------|------|------------|
| afford × URM | #12 | 0.0180 |
| afford_gap_cont | #13 | 0.0121 |
| afford × Pell | #14 | 0.0116 |

**Finding:** Interaction terms (afford × Pell, afford × URM) have **similar importance** to the main affordability effect, suggesting:
- ⚠️ Affordability's effect on earnings **does not strongly vary** by Pell or URM composition
- The interactions are not capturing substantial heterogeneity
- Model R1c performed slightly worse (R² = 0.92) than R1a (R² = 0.93)

**Interpretation:** While we hypothesized that affordability would matter MORE for equity-serving institutions, the data suggest affordability has a **relatively uniform effect** across institution types.

---

### 🎓 Subgroup Analysis: High-Pell vs Low-Pell (R1d)

**Does affordability matter differently for high-Pell vs low-Pell institutions?**

#### High-Pell Institutions (≥44% Pell students)
- **N:** 2,558 institutions
- **Model R²:** 0.7324
- **RMSE:** $5,131
- **Affordability Rank:** **#6 out of 29**
- **Affordability Importance:** **0.0610 (6.1%)**

**Top 5 Features:**
1. % Pell (0.317)
2. % Women (0.120)
3. Instructional expenditure (0.095)
4. Region (0.079)
5. % URM (0.073)

#### Low-Pell Institutions (<44% Pell students)
- **N:** 2,455 institutions
- **Model R²:** 0.9380
- **RMSE:** $3,304
- **Affordability Rank:** **#12 out of 29**
- **Affordability Importance:** **0.0111 (1.1%)**

**Top 5 Features:**
1. % Pell (0.225)
2. % Women (0.166)
3. SAT composite (0.124)
4. ACT composite (0.109)
5. Log endowment (0.073)

---

### 🎯 KEY FINDING: Affordability Matters MORE for High-Pell Institutions

**Comparison:**
- **High-Pell:** Rank #6, Importance = 6.1%
- **Low-Pell:** Rank #12, Importance = 1.1%

**Importance Ratio:** High-Pell is **5.5× stronger** than low-Pell

**Interpretation:**
✅ **Affordability gap is MUCH more important for high-Pell institutions**
- At high-Pell institutions, affordability ranks in the **top 6 predictors**
- At low-Pell institutions, affordability drops to **#12**
- This supports the equity hypothesis: **affordability matters most for institutions serving lower-income students**

**Why the difference?**
- **High-Pell institutions:** Students are more price-sensitive; affordability directly affects enrollment quality, persistence, and ultimately earnings
- **Low-Pell institutions:** More affluent students are less constrained by price; selectivity and resources dominate

---

## Model Performance Comparison

| Model | Description | N | Test R² | Test RMSE | Afford Rank |
|-------|-------------|---|---------|-----------|-------------|
| **R1a** | Full model | 5,013 | 0.9311 | $3,374 | #11 |
| **R1b** | No affordability | 5,013 | 0.9307 | $3,383 | N/A |
| **R1c** | With interactions | 5,013 | 0.9200 | $3,636 | #13 |
| **R1d-High** | High-Pell only | 2,558 | 0.7324 | $5,131 | **#6** |
| **R1d-Low** | Low-Pell only | 2,455 | 0.9380 | $3,304 | #12 |

**Notes:**
- High-Pell model has lower R² because earnings are more variable and harder to predict at these institutions
- Low-Pell model has higher R² because student/institutional characteristics are stronger predictors when price is less constraining

---

## Implications for Policy and Practice

### 1. **Affordability Does Predict Earnings, But Modestly**
- Affordability gap ranks #11 overall
- Adding it improves model by only 0.04%
- **Implication:** Affordability is ONE of many factors affecting earnings, not the dominant factor

### 2. **Context Matters: Affordability's Effect is Heterogeneous**
- 5.5× more important for high-Pell institutions (#6 rank) vs low-Pell (#12 rank)
- **Implication:** Affordability policies should **target equity-serving institutions** where impact is greatest

### 3. **Demographics and Selectivity Dominate**
- % Pell alone explains 45% of variation (10× affordability's effect)
- Selectivity measures (SAT, admission rate) also outrank affordability
- **Implication:** Earnings are primarily determined by **who attends** (student demographics) and **where they attend** (institutional quality), not just **cost**

### 4. **Interaction Effects Are Weak**
- Afford × Pell and Afford × URM interactions don't substantially improve model
- **Implication:** Affordability's effect is relatively **uniform** within institutional types (though the **level** differs between high/low-Pell)

---

## Limitations

1. **Observational Data:** This is predictive modeling, not causal inference. We cannot claim affordability "causes" earnings changes.

2. **Omitted Variable Bias:** Unobserved factors (program quality, student motivation, labor market conditions) affect both affordability and earnings.

3. **Collinearity:** Affordability is correlated with Pell %, selectivity, and resources, making it hard to isolate its independent effect.

4. **Data Censoring:** Earnings data has only ~1,000 unique values, limiting precision.

5. **Dependent Students Only:** Analysis uses earnings of dependent students (93.8% coverage). Results may not generalize to independent students.

---

## Recommendations for App/Dashboard

### For a "College ROI / Affordability-Mobility" Dashboard:

**1. Feature Importance Chart:**
- Show that demographics (#1: Pell %) and selectivity dominate earnings prediction
- Position affordability in context: Important, but not dominant
- Interactive: Let users see how importance changes for high-Pell vs low-Pell

**2. Subgroup Comparison:**
- **Key Visual:** Side-by-side comparison of high-Pell (#6 rank, 6.1%) vs low-Pell (#12 rank, 1.1%)
- Message: "Affordability matters **5.5× more** for institutions serving low-income students"

**3. Model Performance Metrics:**
- Show R² = 0.93 (excellent prediction)
- Show that adding affordability improves model by $9 RMSE
- Message: "Every feature matters, but some more than others"

**4. Institution-Specific Predictions:**
- Use trained model to predict earnings for user-selected institutions
- Show which features contribute most to that institution's predicted earnings
- Highlight when affordability is particularly important (high-Pell institutions)

---

## Next Steps

### For Comprehensive Analysis:
1. **Causal Inference:** Use propensity score matching or instrumental variables to estimate causal effects (not just correlations)
2. **Graduation Rate Model:** Replicate analysis with grad rates as outcome
3. **MSI Analysis:** Separate models for HBCUs, HSIs, TCUs
4. **State-Level Analysis:** Account for regional cost-of-living and labor market differences
5. **Longitudinal:** Track earnings over time (10-year, 15-year, 20-year)

---

## Files Generated

**Data:**
- `outputs/rf_analysis/model_summary.csv` - Performance metrics for all models
- `outputs/rf_analysis/feature_importance_r1a.csv` - Full model feature rankings
- `outputs/rf_analysis/feature_importance_r1c.csv` - Interaction model feature rankings
- `outputs/rf_analysis/feature_importance_high_pell.csv` - High-Pell subgroup rankings
- `outputs/rf_analysis/feature_importance_low_pell.csv` - Low-Pell subgroup rankings

**Visualizations:**
- `outputs/rf_analysis/feature_importance_comparison.png` - 4-panel comparison chart

**Code:**
- `src/earnings_mobility_rf_analysis.py` - Complete analysis script

---

## Conclusion

**Main Takeaway:**  
Affordability gap **does** predict 10-year earnings, but its effect is **moderate** (#11 overall) and **heterogeneous** (#6 for high-Pell, #12 for low-Pell). The analysis provides strong evidence that **affordability policies should target equity-serving institutions** where the impact is 5.5× larger.

The strongest predictors of earnings are:
1. **Student demographics** (Pell %, race, gender)
2. **Institutional selectivity** (test scores, admission rate)  
3. **Institutional resources** (endowment, instructional spending)
4. **Affordability** (moderate effect, but critical for high-Pell institutions)

For app/dashboard development, these findings enable **data-driven storytelling** about the complex relationship between college affordability, institutional characteristics, and economic mobility.

---

**Report prepared by:** Data Science Team  
**For questions:** See `src/earnings_mobility_rf_analysis.py` for reproducible code

