# DoWhy Causal Analysis - README

## Overview

This folder contains a complete DoWhy causal inference analysis examining the effect of institutional affordability gaps on 10-year student earnings.

## Files

### Analysis Script
- **`dowhy_causal_analysis.py`** - Main Python script that runs the full DoWhy pipeline
  - Loads and prepares data
  - Specifies causal model with 30+ confounders
  - Estimates causal effects using 3 methods (IPW, Stratification, Regression)
  - Runs 4 robustness/refutation tests
  - Creates visualizations
  - Provides detailed interpretation

### Summary Documents
- **`DOWHY_ANSWER.md`** - **START HERE** - Direct answer to the research question with policy implications
- **`DOWHY_FINDINGS_SUMMARY.md`** - Comprehensive technical report with all findings, limitations, and next steps

### Output Figures
- **`outputs/figures/dowhy_ate_comparison.png`** - Bar chart comparing ATE estimates across 3 methods
- **`outputs/figures/dowhy_raw_vs_adjusted.png`** - Visual comparison of raw vs causally-adjusted effects

## Quick Start

```bash
# Run the analysis
python dowhy_causal_analysis.py

# Read the key findings
cat DOWHY_ANSWER.md
```

## Research Question

**"What is the causal effect of being in a low affordability gap institution on 10-year earnings, after controlling for selectivity, demographics, resources, etc.?"**

## Key Finding

**Average Treatment Effect: -$2,904** (range: -$3,421 to -$2,428 across methods)

Students at LOW affordability gap institutions (more affordable) earn approximately **$3,000 LESS** after 10 years compared to HIGH gap institutions, even after controlling for selectivity, demographics, resources, and other institutional characteristics.

### ⚠️ Critical Caveat

The **failed placebo refutation test** suggests this is **NOT a true causal effect**. More likely, there are important unobserved confounders (especially field of study and career preferences) driving this association.

## What DoWhy Revealed

### ✅ Consistent Finding
- All 3 causal methods show negative effects
- Results are stable across data subsets
- Not sensitive to random noise

### ⚠️ Validity Concerns
- Placebo test failed → likely unobserved confounding
- Missing key variables: field of study, career preferences, alumni networks
- Cannot make strong causal claims with this data

### 💡 Key Insight
**DoWhy helped us avoid making false causal claims.** We learned that while there's a robust negative association, it's not causally credible, and we should NOT conclude that "affordability causes lower earnings."

## Policy Implications

### ❌ Don't Conclude:
- "Making college affordable reduces earnings"
- "We should focus on expensive institutions"

### ✅ Do Conclude:
- "Students at affordable institutions earn less on average, but this is likely due to selection and omitted variables, not affordability itself"
- "Affordability matters for OTHER important outcomes: debt, access, equity, completion"
- "We need better data (especially field of study) to credibly estimate this causal effect"

## Methods Used

### DoWhy Workflow:
1. **Define Causal Model** - Treatment, outcome, and 30 common causes (confounders)
2. **Identify Estimand** - Used backdoor criterion to determine adjustment set
3. **Estimate Effect** - Three methods:
   - Inverse Propensity Weighting (IPW): -$2,863
   - Propensity Score Stratification: -$3,421
   - Linear Regression: -$2,428
4. **Refute Estimate** - Four robustness tests:
   - ✅ Random common cause: Passed
   - ⚠️ Placebo treatment: Failed (red flag)
   - ✅ Data subset: Passed
   - ⚠️ Unobserved confounder: Moderate sensitivity

### Confounders Controlled (30 variables):
- **Selectivity**: Admit rate, SAT scores
- **Resources**: Instructional expenditure, endowment
- **Demographics**: % Pell, race/ethnicity, % women
- **MSI Status**: HBCU, HSI, TCU, AANAPISI, PBI
- **Institutional**: Sector, size, region, control type

## Data

- **Source**: `outputs/data/analysis_ready.csv`
- **Sample Size**: 5,013 institutions
  - Treatment (Low Gap): 1,178 institutions
  - Control (High Gap): 3,835 institutions
- **Treatment**: Binary indicator (1 = bottom 25% affordability gap, 0 = top 25%)
- **Outcome**: Median 10-year earnings of graduates ($)

## Interpretation

### Raw Data:
- Low-gap institutions: $40,437 average earnings
- High-gap institutions: $45,719 average earnings
- **Raw difference: -$5,282**

### After Causal Adjustment:
- **Causal effect: -$2,904**

### What Changed:
Controlling for confounders **reduced the gap by 45%**, but a ~$3K gap remains. This remaining gap is likely due to **unobserved factors** rather than affordability itself.

## Limitations & Next Steps

### Major Limitations:
1. **Missing field of study** - Likely the biggest omitted variable
2. **Missing career preferences** - Some students choose lower-paying meaningful work
3. **No geographic adjustment** - Earnings not adjusted for cost of living
4. **Failed placebo test** - Suggests invalid causal identification

### Recommended Next Steps:
1. ✅ Add field of study controls (CRITICAL)
2. ✅ Adjust for geographic cost of living
3. ✅ Examine heterogeneous effects by subgroup (Pell, URM, MSI)
4. ✅ Try alternative outcomes (debt, graduation rates)
5. ✅ Look for instrumental variables or natural experiments

## Dependencies

```python
pandas
numpy
matplotlib
seaborn
dowhy
```

Install with:
```bash
pip install pandas numpy matplotlib seaborn dowhy
```

## Contact & Citation

Analysis conducted: November 16, 2025

Based on the DoWhy framework:
- DoWhy Documentation: https://www.pywhy.org/dowhy/
- Paper: Sharma, A., & Kiciman, E. (2020). DoWhy: An End-to-End Library for Causal Inference. arXiv preprint arXiv:2011.04216.

## Additional Resources

- **DoWhy Tutorial**: https://www.pywhy.org/dowhy/v0.11.1/user_guide/intro.html
- **Causal Inference Book**: https://theeffectbook.net/
- **Pearl's Causal Hierarchy**: https://ftp.cs.ucla.edu/pub/stat_ser/r350.pdf

