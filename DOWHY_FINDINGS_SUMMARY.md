# DoWhy Causal Analysis: Key Findings
## Research Question: Does Affordability Gap Causally Affect 10-Year Earnings?

**Analysis Date:** November 16, 2025  
**Script:** `dowhy_causal_analysis.py`

---

## 🎯 Main Finding

### The causal effect of being in a LOW affordability gap institution (vs HIGH gap) on 10-year median earnings is:

**ATE = -$2,863** (averaged across methods)

This means that students at **more affordable institutions earn LESS** on average, even after controlling for selectivity, demographics, institutional resources, and other confounding factors.

---

## 📊 Results Across Multiple Methods

All three causal estimation methods showed **consistent negative effects**:

| Method                            | ATE Estimate | 
|-----------------------------------|--------------|
| Propensity Score Weighting (IPW)  | **-$2,863**  |
| Propensity Score Stratification   | **-$3,421**  |
| Linear Regression (Backdoor)      | **-$2,428**  |
| **Mean across methods**           | **-$2,904**  |
| **Standard deviation**            | **$407**     |
| **Range**                         | **-$3,421 to -$2,428** |

✅ **All methods show CONSISTENT direction → Robust finding**

---

## 🔬 Robustness Checks (Refutation Tests)

DoWhy's refutation tests assess whether the causal estimate is reliable:

### ✅ Test 1: Random Common Cause
- **Result:** PASSED
- **Interpretation:** Adding a random variable as a confounder did NOT change the estimate (change: $0.00)
- **Implication:** The model is not overly sensitive to noise

### ⚠️ Test 2: Placebo Treatment
- **Result:** WARNING
- **Interpretation:** When treatment is randomly assigned (placebo), we still see a large effect ($2,420)
- **Implication:** This suggests potential unobserved confounding or model misspecification
- **ACTION NEEDED:** This is a concern and warrants further investigation

### ✅ Test 3: Data Subset Validation
- **Result:** PASSED
- **Interpretation:** Effect is stable across random subsets of data (only 1.9% difference)
- **Implication:** Result is not driven by specific subsamples

### 📊 Test 4: Unobserved Confounder Sensitivity
- **Result:** Moderate sensitivity
- **Interpretation:** Adding a simulated unobserved confounder changed estimate from -$2,863 to -$2,430 (change: $433)
- **Implication:** Results are somewhat sensitive to unobserved confounding

---

## 🤔 What Does This Mean?

### This counterintuitive finding has several possible explanations:

1. **Unobserved Confounding** (most likely given placebo test warning)
   - Student motivation, ambition, career goals not captured in data
   - Pre-college academic preparation beyond SAT/ACT
   - Family networks and social capital
   - Geographic preferences (students choosing affordable schools may prefer lower-cost areas with lower wages)

2. **Institutional Network Effects**
   - Higher-priced institutions may have stronger alumni networks
   - Better career services, employer connections
   - More prestigious "brand name" that helps in job market

3. **Selection on Unobservables**
   - Students who choose affordable institutions may systematically differ in ways we can't measure
   - Career preferences: Some students optimize for job satisfaction, work-life balance, or public service rather than earnings

4. **Field of Study Effects**
   - If we're not controlling for major/field of study, this could be a major confounder
   - More affordable institutions might have different distributions of majors
   - High-earning fields (e.g., engineering, CS, finance) might cluster at more expensive institutions

5. **Geographic Labor Market Sorting**
   - Students at affordable institutions may be more likely to work in lower-cost-of-living areas
   - Earnings data might not be adjusted for geographic cost differences

---

## ⚠️ Critical Limitations

### 1. **Unobserved Confounding**
The failed placebo test is a RED FLAG. It suggests that even after controlling for 30+ confounders, there are still important variables we're missing that affect both affordability gap and earnings.

### 2. **What We Don't Control For:**
- **Field of study / major** - This is likely a huge omitted variable
- **Geographic location of graduates** (cost-of-living adjustments)
- **Student career preferences and motivations**
- **Quality of career services**
- **Alumni network strength**
- **Internship opportunities**
- **Pre-college preparation beyond test scores**

### 3. **Causal Assumptions**
This interpretation assumes:
- ✅ No unobserved confounding (VIOLATED per placebo test)
- ✅ Linear effects (may not be true)
- ✅ Common support (propensity score overlap)
- ✅ SUTVA (no spillovers between institutions)

---

## 📈 What DoWhy Told Us (vs What It Didn't)

### ✅ What DoWhy CAN Tell Us:
- **Given the observed confounders we controlled for**, the association between low affordability gap and earnings is negative and consistent across methods
- The magnitude is roughly -$2,500 to -$3,500
- This effect is not explained by selectivity, demographics, resources, sector, or MSI status (the things we measured)

### ❌ What DoWhy CANNOT Tell Us:
- Whether this is truly a **causal effect** (placebo test suggests NO)
- Why this relationship exists (mechanism unclear)
- Whether affordability "doesn't matter" for policy (could matter for other outcomes)
- What would happen if we intervened to make expensive schools more affordable

---

## 🎯 Key Takeaway for Your Research Question

### Your original question was:
> "What is the causal effect of being in a low affordability gap institution on 10-year earnings, after controlling for selectivity, demographics, resources, etc.?"

### DoWhy's Answer:
**"Based on this data and the confounders we controlled for, low-gap institutions are associated with ~$3,000 LOWER earnings on average. However, the failed placebo refutation test suggests this may NOT be a true causal effect. There are likely important unobserved confounders (especially field of study, career preferences, and network effects) that we're missing."**

### In Plain English:
**"We cannot confidently claim that making institutions more affordable CAUSES lower earnings. The negative association we observe is likely explained by factors we haven't measured. Students who attend affordable institutions may systematically differ in ways that affect their earnings (career choices, geographic preferences, etc.)."**

---

## 🔍 Recommended Next Steps

### To strengthen this analysis:

1. **Add Field of Study Controls**
   - This is likely the biggest missing confounder
   - If available in your data, re-run DoWhy controlling for major/field
   - Expected: This could flip the sign or reduce magnitude substantially

2. **Geographic Adjustments**
   - Adjust earnings for cost of living by graduate location
   - Control for region of employment

3. **Subgroup Analyses**
   - Does this hold for Pell-eligible students specifically?
   - Does it differ for MSIs vs non-MSIs?
   - Are there differential effects by sector (public vs private)?

4. **Alternative Outcomes**
   - Try outcomes less subject to individual choice: graduation rates, time to degree
   - Look at debt burden (affordability likely matters MORE here)
   - Examine equity outcomes (affordability might reduce racial/SES gaps)

5. **Sensitivity Analyses**
   - Use formal sensitivity analysis methods (e.g., Rosenbaum bounds)
   - Quantify how strong unobserved confounding would need to be to explain away effect

6. **Consider Instrumental Variables**
   - Look for quasi-experimental variation in affordability (policy changes, merit aid rules)
   - This could help address unobserved confounding

---

## 💡 What This Means for Policy

### Don't Conclude: "Affordability doesn't matter"

Even though we found a negative/null effect on earnings, this does NOT mean affordability is unimportant:

1. **Affordability likely matters MORE for:**
   - Debt burden (clear mechanism)
   - College access and completion (especially for low-SES students)
   - Reducing financial stress and improving wellbeing
   - Equity: Reducing gaps by race and income

2. **Earnings may be a poor outcome for measuring affordability's benefit:**
   - Too influenced by field of study choices
   - Too influenced by career preferences (some choose teaching, non-profit work, etc.)
   - Doesn't capture the "option value" of not having debt

3. **The counterfactual matters:**
   - A student choosing an affordable institution may have different opportunities than if that affordable institution didn't exist
   - We're comparing students at low-gap vs high-gap institutions, NOT comparing "making an institution more affordable" vs not

---

## 📁 Output Files

- **Script:** `dowhy_causal_analysis.py`
- **Figures:**
  - `outputs/figures/dowhy_ate_comparison.png` - Comparison of ATE estimates across methods
  - `outputs/figures/dowhy_raw_vs_adjusted.png` - Raw vs causally-adjusted comparison

---

## 🔑 Bottom Line

**DoWhy helped us formalize the causal question and rigorously test assumptions. The result is NOT what we'd naively expect, and the failed placebo test tells us to be skeptical. Rather than concluding "affordability doesn't causally affect earnings," we should conclude "our ability to estimate this causal effect is limited by unobserved confounding, especially field of study and career preferences."**

**This is actually a GOOD outcome from DoWhy - it revealed that a simple observational analysis would be misleading, and we need better data (or quasi-experimental designs) to answer this question definitively.**

---

## 📚 Technical Details

**Sample Size:** 5,013 institutions
- Treatment (Low Gap): 1,178 institutions  
- Control (High Gap): 3,835 institutions

**Confounders Controlled (30 variables):**
- Selectivity: admit rate, SAT scores
- Resources: instructional expenditure, endowment
- Demographics: % Pell, race/ethnicity composition, % women
- MSI Status: HBCU, HSI, TCU, AANAPISI, PBI
- Institutional: sector, size, region, control (public/private)

**DoWhy Methods Used:**
- Backdoor identification (successfully identified 30 confounders to control)
- Propensity score weighting (IPW)
- Propensity score stratification  
- Linear regression adjustment

**Refutation Tests:**
- ✅ Random common cause: Passed
- ⚠️ Placebo treatment: Failed (WARNING)
- ✅ Data subset: Passed
- 📊 Unobserved confounder: Moderate sensitivity

