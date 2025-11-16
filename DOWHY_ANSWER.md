# DoWhy Analysis: Direct Answer to Your Question

## Your Question from the Prompt:

> "What is the causal effect of being in a low affordability gap institution on 10-year earnings, after controlling for selectivity, demographics, resources, etc.?"

---

## DoWhy's Answer:

### 📉 Near zero and robust? NO

### 📈 Positive and robust? NO

### 📉 NEGATIVE and mostly robust: **YES**

---

## The Finding:

**Being in a LOW affordability gap institution (vs HIGH gap) is associated with approximately $2,900 LOWER 10-year earnings, even after controlling for selectivity, demographics, resources, sector, and MSI status.**

### Three different causal methods all agree:
- IPW: **-$2,863**
- Stratification: **-$3,421**
- Regression: **-$2,428**
- **Average: -$2,904**

✅ All same direction → Consistent across methods  
✅ Overlapping confidence intervals → Robust  
⚠️ But failed placebo test → Potential unobserved confounding

---

## What This Means:

### Based on YOUR prompt's framework:

> "If, after that, the causal effect of low gap on earnings is:"

> **"Near zero and robust → You can cautiously say: 'In this dataset and under our assumptions, lowering institutional affordability gaps doesn't have a large average effect on 10-year earnings. Affordability may matter more for debt, risk, and equity than for average earnings.'"**

### ❌ NOT APPLICABLE - Effect is ~$3K, not near zero

---

> **"Positive and robust → 'We find evidence that, for comparable institutions, lower affordability gaps are associated with higher 10-year earnings.'"**

### ❌ NOT APPLICABLE - Effect is negative, not positive

---

### ✅ ACTUAL FINDING:

**"Negative but with concerns about validity"**

**"In this dataset and under our causal assumptions, we find that being in a low affordability gap institution is associated with approximately $3,000 LOWER 10-year earnings compared to high-gap institutions, after controlling for selectivity, demographics, resources, and institutional characteristics.**

**However, the failed placebo refutation test suggests this may not be a true causal effect. There are likely important unobserved confounders—particularly field of study, career preferences, alumni networks, and geographic sorting—that we have not measured.**

**Therefore, we CANNOT conclude that affordability causally reduces earnings. Instead, students who attend affordable institutions may systematically differ in ways we haven't captured, and those differences drive the observed earnings gap."**

---

## Why This Result Makes Sense (and Doesn't)

### The PARADOX:

**Raw data:**
- Low-gap institutions: $40,437 average earnings
- High-gap institutions: $45,719 average earnings  
- **Raw gap: -$5,282**

**After controlling for 30+ confounders:**
- **Causal effect: -$2,904**

### What happened:

Controlling for confounders **REDUCED the gap by 45%** (-$5,282 → -$2,904), but didn't eliminate it.

This means:
1. ✅ Low-gap institutions DO tend to have characteristics that predict lower earnings (less selective, fewer resources, etc.)
2. ✅ Controlling for those factors helps explain the gap
3. ⚠️ But a ~$3K gap REMAINS even after controls
4. ❌ This remaining gap is likely due to **UNOBSERVED** factors, not affordability itself

---

## What DoWhy Revealed That We Couldn't See Before

### Without DoWhy, we might naively conclude:
- "Low-gap institutions have $5K lower earnings. Affordability doesn't help earnings."

### With DoWhy, we learn:
1. **About $2.4K of that gap is explained by selectivity, resources, demographics** (things that are measurable)
2. **About $2.9K remains unexplained** after controlling for observables
3. **The unexplained portion is likely NOT causal** (failed placebo test)
4. **We're missing important confounders**, especially:
   - Field of study / major choice
   - Career preferences (public service vs high-paying corporate jobs)
   - Alumni network effects
   - Geographic cost-of-living differences

---

## The Correct Policy Conclusion:

### ❌ DON'T SAY:
- "Making college more affordable reduces earnings"
- "Affordability doesn't matter for economic mobility"
- "We should focus on expensive institutions because they produce higher earnings"

### ✅ DO SAY:
**"Based on observational data, students at more affordable institutions earn less 10 years after graduation. However, this association appears to be driven primarily by student selection and omitted variables rather than affordability itself.**

**Most importantly, affordability likely matters for outcomes OTHER than average earnings:**
- **Debt burden** (clear mechanism)
- **Access and completion** (especially for low-SES students)
- **Equity** (reducing gaps by race and income)
- **Student wellbeing** (reducing financial stress)
- **Career flexibility** (ability to pursue lower-paying but socially valuable careers)

**10-year earnings is a poor metric for evaluating affordability's impact because it's too influenced by individual career choices and field of study, which we don't adequately control for in this analysis."**

---

## Refutation Tests Summary

### What DoWhy checked:

| Test | Purpose | Result | Interpretation |
|------|---------|--------|----------------|
| **Random Common Cause** | Is the model overfitting? | ✅ PASSED | Adding noise doesn't change estimate |
| **Placebo Treatment** | Is this a spurious association? | ⚠️ WARNING | Random treatment still shows large effect → likely unobserved confounding |
| **Data Subset** | Is the effect stable? | ✅ PASSED | Effect consistent across subsamples |
| **Unobserved Confounder** | Sensitivity to hidden variables? | ⚠️ MODERATE | Effect changes by $433 with simulated confounder |

### Bottom line:
The **placebo test failure is a red flag**. It means that even when we randomly shuffle who gets "treatment," we still see a large effect. This indicates our causal identification strategy is flawed—we're not capturing all important confounders.

---

## Next Steps to Answer This Question Better

### To get a credible causal estimate, you would need:

1. **Field of Study Controls** (CRITICAL)
   - Re-run analysis controlling for major/degree program
   - This is probably the single biggest omitted variable

2. **Geographic Adjustments**
   - Adjust earnings for cost of living
   - Control for region of employment

3. **Instrumental Variables**
   - Find a quasi-experimental source of variation in affordability
   - E.g., state policy changes, merit aid discontinuities

4. **Better Outcome Measures**
   - Graduation rates (less subject to individual choice)
   - Debt burden (clearer link to affordability)
   - Earnings within-field (controls for major choice)

5. **Heterogeneous Effects**
   - Does affordability matter more for Pell students?
   - Different effects by sector, MSI status, or student demographics?

---

## The Meta-Lesson: What DoWhy Is Good For

### DoWhy helped us:
✅ **Formalize causal assumptions** explicitly  
✅ **Test multiple causal methods** and check consistency  
✅ **Run robustness checks** automatically  
✅ **Reveal limitations** in our identification strategy  

### DoWhy did NOT:
❌ Give us the "true" causal effect (we lack the right data)  
❌ Solve the omitted variable problem  
❌ Replace good research design (we need better variation)  

### The value:
**DoWhy told us that our causal claims would NOT be credible with this data. That's actually a GOOD outcome—it prevented us from making false claims about causality.**

**We now know:**
- We have an association (negative)
- It's consistent across methods
- But it's NOT credible as a causal effect
- We need better data or quasi-experimental design

---

## Final Verdict

### Your original insight was correct:

> "Either way, that's a data-backed causal statement about earnings, not a sweeping claim about 'trust in the education system.'"

**Exactly right. DoWhy gives us a data-backed statement:**

**"In our data, after controlling for observables, low-gap institutions are associated with ~$3K lower earnings. But we cannot make a credible causal claim because of likely unobserved confounding. This association does NOT support sweeping policy conclusions about affordability being 'bad' for students."**

---

## TL;DR

**What DoWhy told us:**
- Effect is **negative** (~$3K lower earnings at low-gap institutions)
- **Consistent** across methods  
- But **NOT causally credible** (failed placebo test)
- Likely due to **omitted variables** (field of study, career preferences)

**What we should conclude:**
- Don't claim affordability "causes" lower earnings
- Do acknowledge students at affordable institutions earn less on average
- Do emphasize this is likely due to student selection and omitted variables
- Do argue affordability matters for OTHER important outcomes (debt, equity, access)
- Do recommend better data/design to answer this question definitively

**What this means for policy:**
- Making college more affordable is still good policy
- But don't oversell earnings benefits (uncertain from this data)
- Focus on equity, access, debt, and completion as the main rationales

