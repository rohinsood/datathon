# PRD: Affordability Gap and Economic Mobility Causal Analysis

## Introduction/Overview

This project investigates the causal relationship between institutional affordability gaps and long-term student outcomes (10-year earnings and bachelor's degree completion rates). The core research question is: **"Does Affordability Actually Buy Mobility?"** - specifically, whether institutions with lower affordability gaps produce better earnings and graduation outcomes, particularly for low-income and minoritized students, when controlling for selectivity and student composition.

**Problem Statement:** While many institutions claim to provide accessible, affordable education that promotes economic mobility, it's unclear whether lower affordability gaps actually translate into better student outcomes when accounting for institutional selectivity, resources, and student demographics.

**Dataset Context:**
- Affordability Gap Data (AY2022-23): ~21,300 institutions with net price, affordability gap metrics, student-parent gaps, state minimum wage data
- College Results Data (2021): ~6,290 institutions with earnings outcomes, graduation rates, demographics, selectivity, and institutional characteristics

**Temporal Note:** The outcomes data (2021) precedes the affordability measures (2022-23). This analysis treats 2021 institutional characteristics as predictive/correlational with affordability patterns, acknowledging this limitation in causal interpretation.

## Goals

1. **Primary Goal:** Quantify the causal/predictive relationship between affordability gaps and student outcomes (10-year median earnings and 6-year bachelor's graduation rates)

2. **Equity Goal:** Identify heterogeneous treatment effects - how affordability gaps differentially impact outcomes for:
   - Pell-eligible (low-income) students
   - Underrepresented minority students (by race/ethnicity)
   - Students at Minority-Serving Institutions (HBCUs, HSIs, TCUs, etc.)
   - Intersectional analysis (e.g., low-income URM students)

3. **Methodological Goal:** Apply multiple causal inference techniques with sensitivity analysis using DoWhy framework to ensure robust findings

4. **Communication Goal:** Deliver findings through multiple formats (methodology summary, policy brief, visualizations, slide deck, interactive notebook) suitable for diverse stakeholders

## User Stories

**As a policy researcher**, I want to understand whether investing in institutional affordability actually improves student outcomes, so that I can make evidence-based recommendations on financial aid policy.

**As a higher education administrator**, I want to see which affordability-related interventions have the strongest effects on graduation and earnings, so that I can prioritize resource allocation.

**As an equity advocate**, I want to understand how affordability gaps differentially affect low-income and minoritized students, so that I can identify where interventions would have the greatest equity impact.

**As a data scientist**, I want to explore the analysis interactively with transparent methodology, so that I can validate findings and extend the research.

**As a foundation program officer**, I want visualizations showing "bang-for-buck" institutions (low affordability gap, high outcomes), so that I can identify effective investment targets.

## Functional Requirements

### Data Processing & Integration

**FR1.** The system shall merge Affordability Gap Data (AY2022-23) with College Results Data (2021) using institution identifiers (Unit ID / UNIQUE_IDENTIFICATION_NUMBER)

**FR2.** The system shall filter to include only 4-year bachelor's-granting institutions with complete data on:
- Affordability gap metrics
- 10-year median earnings (overall, dependent, independent students)
- 6-year bachelor's graduation rates (overall and by subgroup)
- Key confounders (selectivity, demographics, expenditures)

**FR3.** The system shall handle missing data appropriately:
- Document missingness patterns
- Apply listwise deletion for primary analysis
- Conduct sensitivity analysis with multiple imputation if >10% missing

**FR4.** The system shall create derived variables:
- Treatment variable: Affordability gap quartiles (bottom 25% = "low gap", top 25% = "high gap")
- State-adjusted affordability measures (accounting for regional cost differences)
- Composite equity indices (Pell percentage × URM percentage)

### Causal Inference Analysis

**FR5.** The system shall implement **Propensity Score Matching/Weighting**:
- Estimate propensity scores: P(low affordability gap | confounders)
- Use confounders: selectivity (admit rate, SAT/ACT), sector, size, state, demographics, expenditures, MSI status
- Apply inverse probability weighting (IPW) or 1:1 matching
- Check covariate balance before/after matching

**FR6.** The system shall implement **Doubly Robust Estimation**:
- Use outcome regression + propensity score weighting
- Implement via econML or causalml libraries
- Provides protection against model misspecification

**FR7.** The system shall implement **Causal Forest / Meta-learners** for heterogeneous treatment effects:
- Estimate conditional average treatment effects (CATE)
- Identify how affordability gap effects vary by: Pell %, URM %, MSI status, selectivity
- Use econML's CausalForestDML or DR-learner

**FR8.** The system shall implement **Regression-based approaches** as baseline:
- OLS with robust controls
- Clustered standard errors by state
- Present as transparent benchmark

**FR9.** The system shall use **DoWhy framework** for:
- Causal graph specification (DAG)
- Identifying causal estimands
- Estimating effects with multiple methods
- Conducting refutation tests (placebo treatment, data subset validation, random cause)

**FR10.** The system shall conduct **sensitivity analysis**:
- Rosenbaum bounds for unobserved confounding
- E-value calculation
- Cross-method comparison (do all methods agree?)

### Equity-Focused Subgroup Analysis

**FR11.** The system shall analyze heterogeneous effects for **Pell-eligible students**:
- Compare graduation rates for Pell vs non-Pell at low vs high gap institutions
- Estimate differential earnings effects

**FR12.** The system shall analyze heterogeneous effects by **race/ethnicity**:
- Graduation rate gaps by race (White, Black, Latino, Asian, Native American)
- Where data permits, earnings by race

**FR13.** The system shall analyze heterogeneous effects for **Minority-Serving Institutions**:
- Separate analyses for HBCUs, HSIs, TCUs, AANAPISIs, PBIs
- Compare MSI vs non-MSI effectiveness of affordability

**FR14.** The system shall conduct **intersectional analysis**:
- Low-income URM students at MSIs
- Interaction effects (Pell × Race × Affordability Gap)

### Visualization & Reporting

**FR15.** The system shall generate **CATE plots** showing:
- Treatment effect of low affordability gap by subgroup
- Confidence intervals
- Sample sizes per group

**FR16.** The system shall generate **partial dependence plots / SHAP plots**:
- Affordability gap vs median earnings
- Feature importance for graduation rates

**FR17.** The system shall generate **"bang-for-buck" scatter plots**:
- X-axis: Affordability gap
- Y-axis: Median earnings (or graduation rate)
- Color: % Pell students
- Size: Enrollment
- Annotations for notable institutions

**FR18.** The system shall generate **covariate balance plots**:
- Before/after matching standardized mean differences
- Love plots showing balance improvement

**FR19.** The system shall create **methodology summary document** (concise, 2-4 pages):
- Causal question & DAG
- Treatment/outcome definitions
- Confounders included
- Methods applied
- Key assumptions and limitations

**FR20.** The system shall create **slide deck** (10-15 slides):
- Executive summary with key finding
- 2-3 core visualizations (CATE plots, bang-for-buck scatter)
- Equity implications highlighted
- Actionable recommendations

**FR21.** The system shall create **interactive Jupyter notebook**:
- Documented code with markdown explanations
- Reproducible analysis pipeline
- Explorable visualizations (plotly for interactivity)

**FR22.** The system shall generate **data summary statistics table**:
- Before/after merge sample sizes
- Descriptive statistics by treatment group
- Outcome variable distributions

## Non-Goals (Out of Scope)

**NG1.** Deep-dive into 2-year colleges or sub-baccalaureate programs (focused on 4-year bachelor's outcomes only)

**NG2.** Student-parent specific outcome analysis (data not available; only affordability gaps for student parents)

**NG3.** Time-series/longitudinal panel analysis (only cross-sectional data available)

**NG4.** Individual student-level data analysis (using institution-level aggregates only)

**NG5.** Resolving the temporal mismatch with new data collection (accepting limitation, documenting clearly)

**NG6.** Publication-quality academic paper (methodology summary sufficient)

**NG7.** Predictive modeling for future outcomes (focus is causal/correlational, not prediction)

**NG8.** Cost-benefit analysis or ROI calculations for specific interventions

## Technical Considerations

### Required Libraries & Tools
- **Data manipulation:** pandas, numpy
- **Causal inference:** DoWhy, econML, causalml
- **Propensity scoring:** scikit-learn, statsmodels
- **Visualization:** matplotlib, seaborn, plotly (interactive)
- **Feature importance:** SHAP
- **Statistical testing:** scipy, statsmodels

### Data Pipeline
1. Load both CSV files
2. Merge on institution ID
3. Filter to 4-year bachelor's institutions
4. Create treatment/outcome/confounder variables
5. Handle missing data
6. Split into analysis cohorts (full sample, subgroups)

### Computational Constraints
- **Timeline:** 24 hours - requires efficient code, minimal iteration
- **Priority order:** Core causal estimates → Equity subgroups → Visualizations → Deliverables
- Institution-level data (~1,000-3,000 observations) should be computationally manageable

### Causal Graph (DAG)
```
State/Region → Affordability Gap → Outcomes (Earnings, Graduation)
           ↘                    ↗
Selectivity → 
Demographics →
Resources (Expenditures) →
Sector/MSI Status →
```

**Key confounders to control:**
- Selectivity (admit rate, test scores)
- Demographics (% Pell, % URM, % White, gender ratio)
- Resources (instructional expenditure per student, endowment)
- Institutional characteristics (sector, size, Carnegie classification, MSI)
- Geography (state, region, urbanization)

## Design Considerations

### Visualization Style
- **Color palette:** Use colorblind-friendly schemes (viridis, colorbrewer)
- **Equity emphasis:** Use distinct colors for Pell vs non-Pell, URM vs non-URM
- **Clarity:** Large fonts, clear labels, minimal clutter
- **Annotations:** Highlight key institutions (e.g., HBCUs with low gaps + high outcomes)

### Reporting Format
- **Methodology summary:** Academic tone but accessible language, PDF format
- **Slide deck:** PowerPoint/Google Slides, visual-heavy, minimal text
- **Notebook:** Well-documented Jupyter notebook with markdown cells explaining each step
- **Visualizations:** Export as high-res PNG/SVG for presentations

## Success Metrics

**SM1. Analytical Rigor:**
- ✅ At least 3 causal methods implemented with consistent directionality of findings
- ✅ DoWhy refutation tests pass (or failures explained)
- ✅ Covariate balance achieved (standardized mean differences <0.1 after matching)

**SM2. Sample Size & Coverage:**
- ✅ Final analysis sample ≥500 4-year institutions (preferably 1,000+)
- ✅ Subgroup analyses have ≥50 institutions per group (for reliability)

**SM3. Equity Insights:**
- ✅ Heterogeneous effects estimated for at least 3 subgroups (Pell, URM, MSI)
- ✅ Intersectional analysis conducted (e.g., Pell × Race)
- ✅ Policy-relevant findings identified (e.g., "low-gap HBCUs have X% higher earnings")

**SM4. Deliverables Completeness:**
- ✅ All 5 deliverable formats produced within 24 hours:
  - Methodology summary (2-4 pages)
  - Slide deck (10-15 slides)
  - Interactive notebook (fully documented)
  - Key visualizations (≥5 publication-ready plots)
  - Data summary tables

**SM5. Reproducibility:**
- ✅ Code runs end-to-end without errors
- ✅ Random seeds set for replicability
- ✅ Requirements.txt or environment.yml provided

**SM6. Actionability:**
- ✅ At least 3 concrete policy/practice recommendations derived from findings
- ✅ Identification of "high-impact" institutions (low gap + high outcomes) for replication

## Open Questions

**OQ1.** What threshold should we use for "low" vs "high" affordability gap? (Quartiles? Terciles? Continuous?)
- **Recommendation:** Start with quartiles (bottom 25% vs top 25%), but also report continuous effects

**OQ2.** How should we handle institutions with negative affordability gaps (where earnings from 10hr/week work exceed net price)?
- **Recommendation:** Include in analysis but flag as special case; may represent very low-cost community colleges

**OQ3.** Should we adjust for multiple comparisons when testing many subgroups?
- **Recommendation:** Yes, apply Bonferroni or Benjamini-Hochberg correction for subgroup analyses; report both adjusted and unadjusted p-values

**OQ4.** How should we weight institutions in analysis - by enrollment size or equally?
- **Recommendation:** Primary analysis unweighted (institution-level effects); sensitivity analysis with enrollment weighting

**OQ5.** What if different causal methods produce conflicting results?
- **Recommendation:** Report all methods transparently; discuss which assumptions are most plausible; consider range of estimates

**OQ6.** How to handle for-profit institutions if they appear in 4-year filtered data?
- **Recommendation:** Include in main analysis but conduct sensitivity analysis excluding for-profits (often different student composition and outcomes)

**OQ7.** Given the temporal mismatch, should we reframe findings as "predictive" rather than "causal"?
- **Recommendation:** Use cautious language: "Under the assumption of temporal stability, lower affordability gaps are associated with..." Emphasize this is cross-sectional correlational evidence with causal-style controls

## Implementation Notes for Developer

### Task Breakdown Priority (24-hour timeline)
**Hours 0-4:** Data pipeline & exploratory analysis
- Load, merge, clean data
- Generate descriptive statistics
- Check sample sizes and missingness

**Hours 4-10:** Core causal inference
- Implement propensity score matching
- Run DoWhy causal graph + estimation + refutation
- Implement doubly robust estimation
- Run baseline regression

**Hours 10-16:** Equity subgroup analysis
- Heterogeneous effects (causal forests or stratified analysis)
- Pell, URM, MSI subgroups
- Generate CATE plots

**Hours 16-20:** Visualizations & interpretation
- Bang-for-buck scatter plots
- Feature importance plots
- Balance plots
- Identify key findings

**Hours 20-24:** Deliverables assembly
- Methodology summary document
- Slide deck creation
- Notebook documentation cleanup
- Final exports

### Code Organization
```
/tasks/
  prd-affordability-mobility-causal-analysis.md (this file)
/src/
  01_data_loading.py
  02_data_cleaning_merge.py
  03_causal_inference_psm.py
  04_causal_inference_doublerobust.py
  05_causal_inference_dowhy.py
  06_heterogeneous_effects.py
  07_visualizations.py
  08_generate_reports.py
/notebooks/
  affordability_mobility_analysis.ipynb
/outputs/
  /figures/
  /tables/
  methodology_summary.pdf
  presentation_slides.pptx
```

### Key Functions to Implement
- `load_and_merge_data()` - data pipeline
- `create_treatment_outcome_vars()` - variable engineering
- `estimate_propensity_scores()` - PSM implementation
- `run_dowhy_analysis()` - DoWhy workflow
- `estimate_heterogeneous_effects()` - subgroup CATE
- `generate_visualizations()` - all plots
- `create_summary_tables()` - descriptive stats
- `export_deliverables()` - final outputs

---

**Document Version:** 1.0  
**Created:** Based on user requirements for 24-hour datathon analysis  
**Target Completion:** 24 hours from project start




