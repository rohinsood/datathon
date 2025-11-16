# Task List: Affordability Gap and Economic Mobility Causal Analysis

## Relevant Files

### Primary Python Scripts
- `/src/01_data_preparation.py` - Data loading, cleaning, merging, and feature engineering
- `/src/02_exploratory_analysis.py` - Descriptive statistics and initial visualizations
- `/src/03_causal_inference.py` - All causal methods (PSM, DR, DoWhy, Regression)
- `/src/04_equity_analysis.py` - Heterogeneous effects and subgroup analysis
- `/src/05_visualizations.py` - Publication-ready plots and figures
- `/src/06_final_report.py` - Report generation with findings synthesis
- `/src/utils.py` - Helper functions (data processing, causal inference, visualization utilities)

### Support Files
- `/outputs/figures/` - Directory for all plots (PNG/SVG)
- `/outputs/tables/` - Directory for CSV tables with results
- `/outputs/data/` - Cleaned and processed datasets
- `/outputs/logs/` - Analysis logs documenting decisions and findings at each step
- `/outputs/methodology_summary.pdf` - Final methodology document
- `/outputs/presentation_slides.pptx` - Final slide deck
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation and instructions

### Notes

**CRITICAL DEVELOPMENT APPROACH:**
- All analysis conducted in Python scripts in `/src/` directory
- **BUT execute scripts ITERATIVELY like a Jupyter notebook:** Run small sections, review outputs, then proceed
- **THINK LIKE A DATA SCIENTIST:** At each step, STOP, analyze the output, draw conclusions, document findings, and adjust your approach based on what the data tells you
- After running each script section, save intermediate outputs to `/outputs/data/` and `/outputs/logs/`
- Document key decisions and findings in `/outputs/logs/analysis_log.md` as you go
- Use print statements liberally to inspect data at each step
- When you discover something unexpected, investigate before proceeding
- Particularly during data cleaning: let the data guide your decisions about filtering, imputation, outlier handling

**Workflow Pattern for Each Script:**
1. Write code for one logical section
2. Run that section
3. **STOP AND ANALYZE:** Print outputs, inspect distributions, check for issues
4. **DOCUMENT:** Write findings to log file - what did you learn? Any surprises?
5. **DECIDE:** Based on findings, should you adjust approach? Modify filters? Try different imputation?
6. **PROCEED:** Move to next section only after understanding current results

## Instructions for Completing Tasks

**IMPORTANT:** As you complete each task, you must check it off in this markdown file by changing `- [ ]` to `- [x]`. This helps track progress and ensures you don't skip any steps.

Example:
- `- [ ] 1.1 Read file` → `- [x] 1.1 Read file` (after completing)

Update the file after completing each sub-task, not just after completing an entire parent task.

## Tasks

- [x] 0.0 Create feature branch and project structure
  - [x] 0.1 Create and checkout a new branch (e.g., `git checkout -b analysis/affordability-mobility`)
  - [x] 0.2 Create directory structure: `/src/`, `/outputs/`, `/outputs/figures/`, `/outputs/tables/`, `/outputs/data/`, `/outputs/logs/`
  - [x] 0.3 Create `requirements.txt` with dependencies: pandas, numpy, scipy, statsmodels, scikit-learn, dowhy, econml, causalml, matplotlib, seaborn, plotly, shap, jupyter, nbformat, ipykernel
  - [x] 0.4 Initialize virtual environment and install dependencies
  - [x] 0.5 Create placeholder Python scripts: `01_data_preparation.py`, `02_exploratory_analysis.py`, `03_causal_inference.py`, `04_equity_analysis.py`, `05_visualizations.py`, `06_final_report.py`
  - [x] 0.6 Create `/src/utils.py` for helper functions
  - [x] 0.7 Create `/outputs/logs/analysis_log.md` to document findings and decisions at each step
  - [x] 0.8 Set up `.gitignore` to exclude large data files, outputs, and __pycache__/

- [x] 1.0 Data loading, cleaning, and merge (Script: `01_data_preparation.py`)
  - [x] 1.1 **DATA LOADING SECTION** - Write code to load both datasets with proper encoding and dtypes
  - [x] 1.2 **RUN & ANALYZE:** Execute loading code, print shapes (~21K and ~6K rows expected), display first 5 rows of each dataset
  - [x] 1.3 **STOP AND THINK:** Do the shapes match expectations? Are column names readable? Any obvious encoding issues? Document in analysis_log.md
  - [x] 1.4 **DATA INSPECTION** - Write code to print all column names and data types for both datasets
  - [x] 1.5 **RUN & ANALYZE:** Execute inspection code, review column lists carefully
  - [x] 1.6 **STOP AND THINK:** Identify which columns represent: Unit ID, Affordability Gap, Net Price, Earnings, Grad Rates. Are column names consistent between datasets? Document key columns in log.
  - [x] 1.7 **COLUMN STANDARDIZATION** - Based on your inspection, write code to standardize institution ID column to 'unit_id' in both datasets
  - [x] 1.8 **DATA FILTERING: 4-YEAR INSTITUTIONS** - Write code to identify and filter to 4-year bachelor's-granting institutions
  - [x] 1.9 **RUN & ANALYZE:** Execute filtering code, print counts before/after for BOTH datasets (expect 1,000-3,000 each)
  - [x] 1.10 **STOP AND THINK:** Did filtering work as expected? Are counts reasonable? Should you adjust criteria? Check what you filtered OUT - any surprises? Document decision in log.
  - [x] 1.11 **DATA MERGING** - Write code to merge datasets on unit_id (inner join)
  - [x] 1.12 **RUN & ANALYZE:** Execute merge, print: # from left dataset, # from right dataset, # matched, merge rate (matched/total)
  - [x] 1.13 **STOP AND THINK:** Is merge rate acceptable (aim for >30%)? If low, investigate: Are unit_id formats different? Do you need to clean IDs? Check sample of unmatched records. Document findings.
  - [x] 1.14 **MISSING DATA ANALYSIS** - Write code to calculate missing percentage for ALL columns, create missingness heatmap
  - [x] 1.15 **RUN & ANALYZE:** Execute missing data analysis, print top 20 columns with most missing data, display heatmap
  - [x] 1.16 **STOP AND THINK:** Which critical variables have >20% missing? Are there patterns (certain institution types have more missing)? Can you infer why? Document missingness patterns in log.
  - [x] 1.17 **IDENTIFY CRITICAL VARIABLES** - Based on your analysis, write code to check missingness for: affordability gap, earnings (10-year), grad rates, admit rate, SAT/ACT, Pell %, demographics
  - [x] 1.18 **RUN & ANALYZE:** Execute critical variable check, print missingness % for each
  - [x] 1.19 **STOP AND THINK:** Which critical variables can you tolerate missing? Which are essential? Should you use listwise deletion or imputation? Make a decision and document rationale in log.
  - [x] 1.20 **DATA CLEANING** - Based on your decision, write code to handle missing values (listwise deletion for critical vars)
  - [x] 1.21 **RUN & ANALYZE:** Execute cleaning, print count before/after, verify no missing in critical columns
  - [x] 1.22 **STOP AND THINK:** Did you lose too many observations? Final sample should be 500+. If <500, reconsider which variables are truly "critical". Document final sample size and justification.
  - [x] 1.23 **SAVE CHECKPOINT** - Save cleaned merged dataset to `/outputs/data/merged_clean.csv`
  - [x] 1.24 **FINAL CHECKPOINT:** Print final shape (~500+ rows, ~150+ columns), display sample of cleaned data, verify key variables present. Document in log: "Data cleaning complete. Final N=[X]."

- [x] 2.0 Feature engineering (Continue in `01_data_preparation.py`)
  - [x] 2.1 **TREATMENT VARIABLE** - Write code to calculate affordability gap quartiles, create treatment variable (bottom 25% = low gap = 1, top 25% = high gap = 0)
  - [x] 2.2 **RUN & ANALYZE:** Execute treatment creation, print counts and percentages for each quartile
  - [x] 2.3 **STOP AND THINK:** Are quartiles balanced (~25% each)? What are the affordability gap values for each quartile? Are they meaningful? Should you use quartiles or a different cutoff? Document decision.
  - [x] 2.4 **VISUALIZE TREATMENT** - Write code to plot affordability gap distribution with quartile lines, show mean gap for each quartile
  - [x] 2.5 **RUN & ANALYZE:** Execute visualization, inspect plot carefully
  - [x] 2.6 **STOP AND THINK:** Is distribution normal, skewed, bimodal? Any extreme outliers? Do quartile cutoffs make sense visually? Document distribution characteristics.
  - [x] 2.7 **OUTCOME VARIABLES: EARNINGS** - Write code to extract median earnings variables (10-year overall, dependent, independent students)
  - [x] 2.8 **RUN & ANALYZE:** Execute extraction, print descriptive stats (mean, median, min, max, missing %) for each earnings variable
  - [x] 2.9 **STOP AND THINK:** Are earnings in reasonable range ($20K-$100K)? Any suppressed values (coded as -999 or similar)? Which earnings variable is best for primary analysis? Document choice and rationale.
  - [x] 2.10 **OUTCOME VARIABLES: GRADUATION RATES** - Write code to extract 6-year bachelor's graduation rate (overall)
  - [x] 2.11 **RUN & ANALYZE:** Execute extraction, print descriptive stats, plot distribution histogram
  - [x] 2.12 **STOP AND THINK:** Are grad rates 0-100%? Check for impossible values. What's the distribution shape? Is there a floor/ceiling effect? Document.
  - [x] 2.13 **CONFOUNDERS: SELECTIVITY** - Write code to extract selectivity variables (admit rate, SAT 25th/75th, ACT 25th/75th)
  - [x] 2.14 **RUN & ANALYZE:** Execute extraction, print descriptive stats and missing % for each selectivity measure
  - [x] 2.15 **STOP AND THINK:** Which institutions have missing test scores? Are they test-optional or just missing data? Should you create a composite selectivity index? Should you include missing flags? Document decisions.
  - [x] 2.16 **CONFOUNDERS: INSTITUTIONAL** - Write code to extract sector, size category, state, region variables
  - [x] 2.17 **RUN & ANALYZE:** Execute extraction, print value counts for sector (public/private/for-profit), size, state distribution
  - [x] 2.18 **STOP AND THINK:** Are sectors balanced? Any states dominating sample? Should you group small states into regions? Do you need to create dummy variables? Document approach.
  - [x] 2.19 **CONFOUNDERS: DEMOGRAPHICS** - Write code to extract demographic variables (% Pell, % White, % Black, % Latino, % Asian, % women)
  - [x] 2.20 **RUN & ANALYZE:** Execute extraction, print descriptive stats (mean, min, max) for each demographic variable
  - [x] 2.21 **STOP AND THINK:** Do percentages sum to ~100%? Any extreme/impossible values (>100%)? Check correlations between race percentages. Should you create composite "% URM" variable? Document decisions.
  - [x] 2.22 **CONFOUNDERS: RESOURCES** - Write code to extract instructional expenditure per student, endowment per student
  - [x] 2.23 **RUN & ANALYZE:** Execute extraction, print descriptive stats, plot distributions
  - [x] 2.24 **STOP AND THINK:** Are expenditures in reasonable range ($5K-$50K/student)? Are distributions highly skewed? Should you log-transform? Many zeros in endowment? How to handle? Document approach.
  - [x] 2.25 **MSI INDICATORS** - Write code to extract MSI flags (HBCU, HSI, TCU, AANAPISI, PBI), create binary indicators
  - [x] 2.26 **RUN & ANALYZE:** Execute extraction, print counts for each MSI type, check for institutions with multiple MSI designations
  - [x] 2.27 **STOP AND THINK:** How many MSIs in sample? Enough for subgroup analysis (>50)? Should you create "Any MSI" flag or keep separate? Document.
  - [x] 2.28 **HANDLE MISSING CONFOUNDERS** - Based on all previous analyses, write code to impute remaining missing confounders
  - [x] 2.29 **RUN & ANALYZE:** Execute imputation (mean for continuous, mode for categorical), add missingness indicator flags, verify no missing values remain
  - [x] 2.30 **STOP AND THINK:** Review imputation decisions - are they defensible? Should you note in limitations that X% was imputed? Document imputation summary.
  - [x] 2.31 **CREATE FINAL VARIABLE LIST** - Write code to create clean lists of: treatment_var, outcome_vars, confounder_vars for use in causal analysis
  - [x] 2.32 **RUN & ANALYZE:** Print final variable lists, verify all variables exist in dataset
  - [x] 2.33 **STOP AND THINK:** Have you included all important confounders? Missing anything from causal graph? Review PRD DAG. Document final variable selections.
  - [x] 2.34 **SAVE ANALYSIS-READY DATA** - Save feature-engineered dataset to `/outputs/data/analysis_ready.csv`, also save variable lists to `/outputs/data/variable_lists.json`
  - [x] 2.35 **FINAL CHECKPOINT:** Print summary: total N, treatment group sizes (both >200?), outcome variable ranges, number of confounders. Document: "Feature engineering complete. Ready for causal analysis."

- [ ] 3.0 Exploratory data analysis (Script: `02_exploratory_analysis.py`)
  - [ ] 3.1 **LOAD ANALYSIS-READY DATA** - Write code to load `/outputs/data/analysis_ready.csv` and variable lists
  - [ ] 3.2 **RUN & ANALYZE:** Execute load, print shape and verify all engineered features present
  - [ ] 3.3 **STOP AND THINK:** Does data look correct? Any unexpected changes from saved file? Verify treatment/outcome/confounder variables all present.
  - [ ] 3.4 **DESCRIPTIVE STATS BY TREATMENT GROUP** - Write code to generate descriptive statistics table comparing low gap vs high gap institutions
  - [ ] 3.5 **RUN & ANALYZE:** Execute comparison, print mean, std, min, max for key variables by treatment group
  - [ ] 3.6 **STOP AND THINK:** Do low-gap institutions look different from high-gap on outcomes? On confounders? If outcomes already differ without controlling for confounders, note this. Document initial patterns.
  - [ ] 3.7 **SAVE DESCRIPTIVE TABLE** - Save descriptive stats to `/outputs/tables/descriptive_stats.csv`
  - [ ] 3.8 **CORRELATION ANALYSIS** - Write code to create correlation matrix for key continuous variables (treatment, outcomes, main confounders)
  - [ ] 3.9 **RUN & ANALYZE:** Execute correlation analysis, visualize with heatmap, print highly correlated pairs (|r| > 0.7)
  - [ ] 3.10 **STOP AND THINK:** Which confounders are multicollinear? Should you drop any or create composite indices? Is treatment correlated with outcomes (good - suggests signal)? Is treatment correlated with confounders (expected - that's why we need causal methods)? Document multicollinearity concerns.
  - [ ] 3.11 **OUTCOME DISTRIBUTIONS** - Write code to plot histograms for earnings and graduation rate outcomes with KDE overlay
  - [ ] 3.12 **RUN & ANALYZE:** Execute distribution plots, create separate box plots by treatment group
  - [ ] 3.13 **STOP AND THINK:** Are distributions normal, skewed, bimodal? Do treatment groups have different distributions? Check for outliers (>3 SD from mean). Should you transform outcomes or trim outliers? Document decision.
  - [ ] 3.14 **OUTLIER DETECTION** - Based on your observation, write code to identify outliers using IQR method or z-scores
  - [ ] 3.15 **RUN & ANALYZE:** Execute outlier detection, print number and characteristics of outliers
  - [ ] 3.16 **STOP AND THINK:** Are outliers data errors or legitimate extreme values? Should you winsorize at 1st/99th percentile or exclude entirely? What's the impact on sample size? Make decision and document rationale.
  - [ ] 3.17 **APPLY OUTLIER HANDLING** - If you decided to handle outliers, write and execute code to do so, save updated data
  - [ ] 3.18 **TREATMENT GROUP BALANCE CHECK (PRE-MATCHING)** - Write code to calculate standardized mean differences (SMD) for all confounders between treatment groups
  - [ ] 3.19 **RUN & ANALYZE:** Execute balance check, print SMD for each confounder, identify which have |SMD| > 0.1 (imbalanced)
  - [ ] 3.20 **STOP AND THINK:** How many confounders are imbalanced? This is expected pre-matching - it justifies using causal methods. Which confounders have largest imbalance? These are most important to balance. Document pre-matching imbalance.
  - [ ] 3.21 **CREATE BALANCE TABLE** - Write code to create formatted balance table with SMD for key confounders, save to `/outputs/tables/balance_pre_matching.csv`
  - [ ] 3.22 **FINAL EDA CHECKPOINT:** Verify treatment groups have >200 each, outcomes vary meaningfully, confounders show imbalance. Document: "EDA complete. Proceeding to causal inference with N=[X], treatment imbalanced on [Y] confounders."

- [ ] 4.0 Implement core causal inference methods (Script: `03_causal_inference.py`)
  - [ ] 4.1 **SETUP CAUSAL ANALYSIS** - Write code to load analysis-ready data, import causal inference libraries, define treatment/outcome/confounder lists
  - [ ] 4.2 **RUN & ANALYZE:** Execute setup, print variable lists, verify data loaded correctly
  - [ ] 4.3 **STOP AND THINK:** Double-check variable lists match your causal graph from PRD. Any confounders missing? Document causal assumptions.
  - [ ] 4.4 **PROPENSITY SCORE MODEL** - Write code to specify logistic regression model: treatment ~ all confounders
  - [ ] 4.5 **RUN & ANALYZE:** Fit propensity score model, print model summary, generate predicted propensity scores
  - [ ] 4.6 **STOP AND THINK:** Which confounders are significant predictors of treatment? Check model convergence. Any warnings? Propensity scores should be between 0 and 1. Document model diagnostics.
  - [ ] 4.7 **VISUALIZE PROPENSITY SCORES** - Write code to plot propensity score distributions for treated vs control groups
  - [ ] 4.8 **RUN & ANALYZE:** Execute visualization, check for common support (overlap)
  - [ ] 4.9 **STOP AND THINK:** Is there good overlap? If distributions barely overlap, you may need to trim sample to common support region. Check for extreme propensity scores (near 0 or 1) - these indicate poor overlap. Document common support assessment.
  - [ ] 4.10 **CALCULATE IPW WEIGHTS** - Write code to calculate inverse probability weights from propensity scores
  - [ ] 4.11 **RUN & ANALYZE:** Execute weight calculation, print weight distribution (min, max, mean), calculate effective sample size
  - [ ] 4.12 **STOP AND THINK:** Are weights reasonable? Very large weights (>10) indicate poor overlap. Should you trim weights? What's effective sample size vs actual sample size? Document weighting decisions.
  - [ ] 4.13 **CHECK POST-WEIGHTING BALANCE** - Write code to calculate SMD for all confounders AFTER applying IPW weights
  - [ ] 4.14 **RUN & ANALYZE:** Execute balance check, print SMD for each confounder, compare to pre-matching SMD
  - [ ] 4.15 **STOP AND THINK:** Did balance improve? Aim for |SMD| < 0.1 for most confounders. If some confounders still imbalanced, should you revise propensity model (add interactions, polynomials)? Document balance improvement.
  - [ ] 4.16 **SAVE BALANCE COMPARISON** - Save before/after balance table to `/outputs/tables/balance_comparison.csv`
  - [ ] 4.17 **ESTIMATE ATE: EARNINGS** - Write code to estimate ATE on earnings using IPW, calculate bootstrap standard errors (1000 iterations)
  - [ ] 4.18 **RUN & ANALYZE:** Execute ATE estimation, print point estimate, SE, 95% CI, p-value
  - [ ] 4.19 **STOP AND THINK:** What is the effect direction? Magnitude? Is it statistically significant? Is effect size practically meaningful (e.g., $5K earnings difference)? Document interpretation.
  - [ ] 4.20 **ESTIMATE ATE: GRADUATION RATE** - Write code to estimate ATE on graduation rate using IPW, calculate bootstrap SE
  - [ ] 4.21 **RUN & ANALYZE:** Execute ATE estimation, print results
  - [ ] 4.22 **STOP AND THINK:** Consistent with earnings effect? What's the magnitude (percentage points)? Significant? Document.
  - [ ] 4.23 **FORMAT PSM RESULTS** - Write code to create formatted results table with both outcomes
  - [ ] 4.24 **SAVE PSM RESULTS** - Save to `/outputs/tables/psm_results.csv`
  - [ ] 4.25 **DOUBLY ROBUST ESTIMATION** - Write code to import econML's LinearDML or DRLearner, specify outcome and propensity models
  - [ ] 4.26 **RUN & ANALYZE:** Fit DR estimator for earnings outcome, extract ATE with SE
  - [ ] 4.27 **STOP AND THINK:** Does DR estimate differ from PSM? DR should be more efficient (smaller SE). Check model convergence. Document comparison.
  - [ ] 4.28 **DR: GRADUATION RATE** - Write code to fit DR estimator for graduation rate outcome
  - [ ] 4.29 **RUN & ANALYZE:** Execute DR estimation, extract ATE with SE
  - [ ] 4.30 **STOP AND THINK:** Compare DR and PSM results - are they directionally consistent? If very different, investigate why. Document.
  - [ ] 4.31 **SAVE DR RESULTS** - Format and save to `/outputs/tables/doublerobust_results.csv`
  - [ ] 4.32 **DOWHY: CAUSAL GRAPH** - Write code to specify causal DAG with nodes and edges (all confounders → treatment, all confounders → outcomes, treatment → outcomes)
  - [ ] 4.33 **RUN & ANALYZE:** Create DoWhy CausalModel for earnings outcome, identify causal estimand using backdoor criterion
  - [ ] 4.34 **STOP AND THINK:** Does DoWhy correctly identify the confounders? Print identified estimand and verify it matches your assumptions. Document.
  - [ ] 4.35 **DOWHY: ESTIMATION** - Write code to estimate causal effect using propensity score weighting, extract ATE
  - [ ] 4.36 **RUN & ANALYZE:** Execute DoWhy estimation, print ATE estimate
  - [ ] 4.37 **STOP AND THINK:** Compare to PSM and DR - consistent? Document.
  - [ ] 4.38 **DOWHY: REFUTATION TESTS** - Write code to run refutation tests: (1) add random common cause, (2) replace treatment with placebo, (3) data subset validation
  - [ ] 4.39 **RUN & ANALYZE:** Execute all 3 refutation tests, print results with p-values
  - [ ] 4.40 **STOP AND THINK:** Did estimate survive refutation tests? Random cause should show no effect (p>0.05). Placebo should fail. Subset should show similar effect. If refutation tests fail, investigate assumptions. Document refutation results and interpret.
  - [ ] 4.41 **DOWHY: GRADUATION RATE** - Repeat DoWhy analysis (model, estimation, refutation) for graduation rate outcome
  - [ ] 4.42 **RUN & ANALYZE:** Execute full DoWhy pipeline for graduation rate
  - [ ] 4.43 **STOP AND THINK:** Do refutation tests pass for graduation rate too? Document.
  - [ ] 4.44 **SAVE DOWHY RESULTS** - Format results with refutation summary, save to `/outputs/tables/dowhy_results.csv`
  - [ ] 4.45 **OLS REGRESSION** - Write code to specify OLS model: Outcome ~ Treatment + all confounders (with dummy variables for categorical vars)
  - [ ] 4.46 **RUN & ANALYZE:** Fit OLS for earnings, print regression summary with clustered SEs by state
  - [ ] 4.47 **STOP AND THINK:** What's the treatment coefficient? Consistent with other methods? Check R-squared (>0.5 good). Check VIF for multicollinearity. Document.
  - [ ] 4.48 **OLS: GRADUATION RATE** - Fit OLS for graduation rate outcome
  - [ ] 4.49 **RUN & ANALYZE:** Execute OLS, print summary
  - [ ] 4.50 **STOP AND THINK:** Treatment coefficient direction and magnitude? R-squared? Document.
  - [ ] 4.51 **SAVE OLS RESULTS** - Extract treatment coefficients, SEs, CIs, p-values, save to `/outputs/tables/regression_results.csv`
  - [ ] 4.52 **COMPARE ALL METHODS** - Write code to combine results from all 4 methods (PSM, DR, DoWhy, OLS) into single comparison table
  - [ ] 4.53 **RUN & ANALYZE:** Execute comparison, print side-by-side results for both outcomes
  - [ ] 4.54 **STOP AND THINK - CRITICAL DECISION POINT:** Do all 4 methods agree on direction (same sign)? Are confidence intervals overlapping? If methods wildly disagree, you have a problem - investigate before proceeding. If methods are consistent, this is strong evidence. Calculate range of estimates. Document methods comparison and your confidence in findings.
  - [ ] 4.55 **SAVE METHODS COMPARISON** - Save comparison table to `/outputs/tables/methods_comparison.csv`
  - [ ] 4.56 **UPDATE UTILS.PY** - Add helper functions used in this script: `calculate_smd()`, `bootstrap_ci()`, `ipw_weights()` to utils.py
  - [ ] 4.57 **CAUSAL INFERENCE CHECKPOINT:** Document in log: "Causal inference complete. All 4 methods show [consistent/inconsistent] direction. ATE for earnings: [range]. ATE for grad rate: [range]. Refutation tests: [passed/failed]."

- [ ] 5.0 Conduct equity-focused subgroup analysis (Script: `04_equity_analysis.py`)
  - [ ] 5.1 **LOAD DATA AND MAIN RESULTS** - Write code to load analysis-ready data and main ATE results from previous script
  - [ ] 5.2 **RUN & ANALYZE:** Execute load, verify data and results loaded correctly
  - [ ] 5.3 **DEFINE SUBGROUPS** - Write code to define High Pell (>40%), Low Pell (<40%), High URM (>30% Black+Latino), Low URM, MSI vs non-MSI
  - [ ] 5.4 **RUN & ANALYZE:** Execute subgroup definitions, print counts for each subgroup
  - [ ] 5.5 **STOP AND THINK:** Are sample sizes adequate (>50 per subgroup)? If any subgroup has <50, note this as limitation - results will be underpowered. Should you adjust thresholds to balance sample sizes? Document subgroup definitions and sample sizes.
  - [ ] 5.6 **DESCRIPTIVE STATS BY SUBGROUP** - Write code to print descriptive stats for each subgroup (mean outcomes, affordability gap, demographics)
  - [ ] 5.7 **RUN & ANALYZE:** Execute descriptive stats
  - [ ] 5.8 **STOP AND THINK:** Do subgroups look different? High Pell schools should have more Pell students (by definition) but check other characteristics. Document subgroup profiles.
  - [ ] 5.9 **SUBGROUP ATE: HIGH PELL** - Write code to filter to High Pell institutions, re-run PSM to estimate ATE on earnings and grad rate
  - [ ] 5.10 **RUN & ANALYZE:** Execute PSM on High Pell subset, print ATE with CI
  - [ ] 5.11 **STOP AND THINK:** What's the ATE for High Pell schools? Larger or smaller than overall ATE? Does this make sense conceptually? Document.
  - [ ] 5.12 **SUBGROUP ATE: LOW PELL** - Write code for Low Pell institutions PSM
  - [ ] 5.13 **RUN & ANALYZE:** Execute PSM on Low Pell subset, print ATE with CI
  - [ ] 5.14 **STOP AND THINK:** Compare High vs Low Pell ATEs. Is difference statistically significant? Test with interaction term. Does affordability matter more/less for high-Pell schools? This is a key equity finding. Document.
  - [ ] 5.15 **SUBGROUP ATE: HIGH URM** - Write code for High URM institutions PSM
  - [ ] 5.16 **RUN & ANALYZE:** Execute PSM on High URM subset
  - [ ] 5.17 **STOP AND THINK:** ATE for High URM schools? Compare to Low URM. Document.
  - [ ] 5.18 **SUBGROUP ATE: LOW URM** - Write code for Low URM institutions PSM
  - [ ] 5.19 **RUN & ANALYZE:** Execute PSM on Low URM subset
  - [ ] 5.20 **STOP AND THINK:** Compare High vs Low URM ATEs. Significant difference? Document equity implications.
  - [ ] 5.21 **SUBGROUP ATE: MSI** - Write code for MSI institutions PSM
  - [ ] 5.22 **RUN & ANALYZE:** Execute PSM on MSI subset
  - [ ] 5.23 **STOP AND THINK:** ATE for MSIs? Sample size adequate? Document.
  - [ ] 5.24 **SUBGROUP ATE: NON-MSI** - Write code for non-MSI institutions PSM
  - [ ] 5.25 **RUN & ANALYZE:** Execute PSM on non-MSI subset
  - [ ] 5.26 **STOP AND THINK:** Compare MSI vs non-MSI. Does affordability matter more at MSIs? Document.
  - [ ] 5.27 **MSI TYPE BREAKDOWN** - If sample sizes permit (>30 each), write code to estimate separate ATEs for HBCU, HSI, TCU
  - [ ] 5.28 **RUN & ANALYZE:** Execute MSI type-specific analyses
  - [ ] 5.29 **STOP AND THINK:** Do different MSI types show different patterns? HBCUs vs HSIs? Note small sample caveats. Document.
  - [ ] 5.30 **CAUSAL FOREST FOR CONTINUOUS CATE** - Write code to import econML's CausalForestDML, fit on full sample to get institution-specific treatment effects
  - [ ] 5.31 **RUN & ANALYZE:** Fit causal forest for earnings, extract CATE predictions for each institution
  - [ ] 5.32 **STOP AND THINK:** Check CATE variation - do some institutions benefit more than others? What's the range of CATEs? Document heterogeneity.
  - [ ] 5.33 **CAUSAL FOREST: GRADUATION RATE** - Fit causal forest for graduation rate outcome
  - [ ] 5.34 **RUN & ANALYZE:** Extract CATE predictions
  - [ ] 5.35 **STOP AND THINK:** CATE variation for grad rates? Document.
  - [ ] 5.36 **CATE ANALYSIS: PELL PERCENTAGE** - Write code to plot CATE vs % Pell (continuous) with loess smoothing
  - [ ] 5.37 **RUN & ANALYZE:** Execute CATE plot, inspect for trends
  - [ ] 5.38 **STOP AND THINK:** Does treatment effect increase/decrease with % Pell? Linear or non-linear relationship? This is key equity insight. Document pattern.
  - [ ] 5.39 **CATE ANALYSIS: URM PERCENTAGE** - Write code to plot CATE vs % URM
  - [ ] 5.40 **RUN & ANALYZE:** Execute CATE plot
  - [ ] 5.41 **STOP AND THINK:** Pattern across URM spectrum? Document.
  - [ ] 5.42 **IDENTIFY EXTREME CATES** - Write code to identify institutions with highest/lowest CATEs, print their characteristics
  - [ ] 5.43 **RUN & ANALYZE:** Print top 10 highest and lowest CATE institutions with their profiles
  - [ ] 5.44 **STOP AND THINK:** What do high-CATE institutions have in common? What about low/negative CATE? Any patterns by sector, size, location? Document insights.
  - [ ] 5.45 **INTERSECTIONAL ANALYSIS** - Write code to create 2×2×2 categories (High/Low Pell × High/Low URM × MSI/non-MSI = 8 groups)
  - [ ] 5.46 **RUN & ANALYZE:** Print sample sizes for all 8 intersectional groups
  - [ ] 5.47 **STOP AND THINK:** Which cells have adequate sample (>30)? Which are too small? This analysis may be underpowered. Document which intersections are analyzable.
  - [ ] 5.48 **INTERSECTIONAL ATES** - For adequately-sized cells, write code to estimate separate ATEs
  - [ ] 5.49 **RUN & ANALYZE:** Execute intersectional ATEs
  - [ ] 5.50 **STOP AND THINK:** Do effects differ for High Pell + High URM + MSI schools? This is the most marginalized group - does affordability matter most here? Or least? Interpret carefully given small samples. Document findings with caveats.
  - [ ] 5.51 **RACE-SPECIFIC GRADUATION RATES** - If data available, write code to estimate treatment effects on graduation rates by race (White, Black, Latino, Asian)
  - [ ] 5.52 **RUN & ANALYZE:** Execute race-specific analyses
  - [ ] 5.53 **STOP AND THINK:** Does affordability reduce/increase racial graduation gaps? Key equity question. Document.
  - [ ] 5.54 **MULTIPLE COMPARISON CORRECTION** - Write code to collect all subgroup p-values, apply Bonferroni correction
  - [ ] 5.55 **RUN & ANALYZE:** Execute correction, compare adjusted vs unadjusted p-values
  - [ ] 5.56 **STOP AND THINK:** Which findings survive Bonferroni correction? Some marginally significant results may become non-significant. Be honest about this in reporting. Document which results are robust to correction.
  - [ ] 5.57 **COMPILE SUBGROUP RESULTS TABLE** - Write code to create comprehensive table with all subgroup ATEs, CIs, p-values (both adjusted and unadjusted)
  - [ ] 5.58 **SAVE HETEROGENEOUS EFFECTS** - Save to `/outputs/tables/heterogeneous_effects.csv`
  - [ ] 5.59 **EQUITY ANALYSIS CHECKPOINT:** Document in log: "Subgroup analysis complete. Key finding: Affordability effects are [stronger/weaker/similar] for High Pell institutions (ATE=[X] vs [Y]). [X] of [Y] subgroup findings survive multiple comparison correction."

- [ ] 6.0 Generate visualizations (Script: `05_visualizations.py`)
  - [ ] 6.1 **SETUP PLOTTING ENVIRONMENT** - Write code to set up plotting config (seaborn colorblind palette, font size 12+, figure size 10×8 inches, 300 dpi)
  - [ ] 6.2 **RUN & ANALYZE:** Execute setup, import visualization libraries
  - [ ] 6.3 **LOAD ALL RESULTS TABLES** - Write code to load results from previous scripts (balance, methods comparison, subgroup effects, CATE predictions)
  - [ ] 6.4 **RUN & ANALYZE:** Execute loads, verify all tables loaded correctly
  - [ ] 6.5 **FIGURE 1: COVARIATE BALANCE (LOVE PLOT)** - Write code to create Love plot showing SMDs before/after matching with 0.1 threshold line
  - [ ] 6.6 **RUN & ANALYZE:** Execute plot, display figure
  - [ ] 6.7 **STOP AND THINK:** Does plot clearly show balance improvement? Are labels readable? Is 0.1 threshold line visible? Adjust aesthetics if needed. Document.
  - [ ] 6.8 **SAVE FIGURE 1** - Save covariate balance plot to `/outputs/figures/covariate_balance.png` at 300 dpi
  - [ ] 6.9 **FIGURE 2: CATE BY PELL PERCENTAGE** - Write code to create scatter plot (x=% Pell, y=CATE) with loess smoothing and 95% confidence bands
  - [ ] 6.10 **RUN & ANALYZE:** Execute plot, inspect trend
  - [ ] 6.11 **STOP AND THINK:** Is trend visible? Are confidence bands reasonable width? Does plot support your earlier finding about Pell heterogeneity? Adjust if needed.
  - [ ] 6.12 **SAVE FIGURE 2** - Save CATE-Pell plot to `/outputs/figures/cate_pell.png`
  - [ ] 6.13 **FIGURE 3: CATE BY URM PERCENTAGE** - Write code to create scatter plot (x=% URM, y=CATE) with loess smoothing
  - [ ] 6.14 **RUN & ANALYZE:** Execute plot
  - [ ] 6.15 **STOP AND THINK:** Compare to Pell plot - similar pattern? Different? Adjust aesthetics.
  - [ ] 6.16 **SAVE FIGURE 3** - Save CATE-URM plot to `/outputs/figures/cate_urm.png`
  - [ ] 6.17 **FIGURE 4: CATE BY MSI TYPE** - Write code to create bar chart with ATEs by MSI type (HBCU, HSI, TCU, non-MSI) with 95% CI error bars
  - [ ] 6.18 **RUN & ANALYZE:** Execute plot
  - [ ] 6.19 **STOP AND THINK:** Are error bars visible? Do bars clearly show which MSI types have larger effects? Adjust.
  - [ ] 6.20 **SAVE FIGURE 4** - Save MSI comparison plot to `/outputs/figures/cate_msi.png`
  - [ ] 6.21 **FIGURE 5: BANG-FOR-BUCK SCATTER** - Write code to create scatter (x=Affordability Gap, y=Median Earnings), color by % Pell (continuous colormap), size by enrollment
  - [ ] 6.22 **RUN & ANALYZE:** Execute plot, add annotations for notable institutions (HBCUs, HSIs with low gap + high earnings)
  - [ ] 6.23 **STOP AND THINK:** Does plot show "high value" institutions in lower-left quadrant? Are annotations readable? Should you add quadrant lines? This is a KEY figure for policy audience. Make it compelling.
  - [ ] 6.24 **SAVE FIGURE 5** - Save bang-for-buck scatter to `/outputs/figures/bang_for_buck_scatter.png`
  - [ ] 6.25 **FIGURE 6: SHAP FEATURE IMPORTANCE** - Write code to train gradient boosting model for grad rate prediction, compute SHAP values
  - [ ] 6.26 **RUN & ANALYZE:** Fit model, compute SHAP, create summary plot
  - [ ] 6.27 **STOP AND THINK:** Is affordability gap among top features? What else matters for grad rates? Document feature importance order.
  - [ ] 6.28 **SAVE FIGURE 6** - Save SHAP importance plot to `/outputs/figures/shap_importance.png`
  - [ ] 6.29 **FIGURE 7: SHAP DEPENDENCE** - Write code to create SHAP dependence plot for Affordability Gap feature (interaction with % Pell colored)
  - [ ] 6.30 **RUN & ANALYZE:** Execute plot
  - [ ] 6.31 **STOP AND THINK:** Non-linear relationship? Interaction visible? Document.
  - [ ] 6.32 **SAVE FIGURE 7** - Save SHAP dependence plot to `/outputs/figures/shap_dependence.png`
  - [ ] 6.33 **FIGURE 8: METHODS COMPARISON FOREST PLOT** - Write code to create forest plot with all 4 methods (PSM, DR, DoWhy, OLS) showing estimates with 95% CIs
  - [ ] 6.34 **RUN & ANALYZE:** Execute plot, create separate panels for earnings and grad rate
  - [ ] 6.35 **STOP AND THINK:** Do CIs overlap (good - methods agree)? Is plot clear and professional? This is KEY figure for methodological rigor.
  - [ ] 6.36 **SAVE FIGURE 8** - Save methods comparison plot to `/outputs/figures/methods_comparison.png`
  - [ ] 6.37 **FIGURE 9: SUBGROUP EFFECTS** - Write code to create grouped bar chart for Pell/URM/MSI subgroups with error bars and significance stars
  - [ ] 6.38 **RUN & ANALYZE:** Execute plot, add stars (* p<0.05, ** p<0.01) for adjusted p-values
  - [ ] 6.39 **STOP AND THINK:** Does plot clearly show which subgroups have stronger effects? This is KEY equity figure. Make it clear and impactful.
  - [ ] 6.40 **SAVE FIGURE 9** - Save subgroup effects plot to `/outputs/figures/subgroup_effects.png`
  - [ ] 6.41 **REVIEW ALL FIGURES** - Write code to display all 9 figures in grid for quality check
  - [ ] 6.42 **RUN & ANALYZE:** Display all figures
  - [ ] 6.43 **STOP AND THINK - QUALITY CHECK:** Are all figures high-quality, readable, properly labeled? Colorblind-friendly? Do they tell a coherent story? Make any final adjustments needed.
  - [ ] 6.44 **UPDATE UTILS.PY** - Add helper functions: `apply_plot_style()`, `save_figure()`, `annotate_plot()` to utils.py
  - [ ] 6.45 **VISUALIZATION CHECKPOINT:** Document: "All 9 figures generated at 300 dpi. Figures saved to /outputs/figures/. Visual QA complete."

- [ ] 7.0 Create final report and deliverables (Script: `06_final_report.py`)
  - [ ] 7.1 **LOAD ALL RESULTS** - Write code to load all tables and prepare data for report generation
  - [ ] 7.2 **RUN & ANALYZE:** Execute loads, verify all results available
  - [ ] 7.3 **SYNTHESIZE KEY FINDINGS** - Write code to extract headline findings: overall ATE ranges, key subgroup differences, robustness of results
  - [ ] 7.4 **RUN & ANALYZE:** Print synthesis
  - [ ] 7.5 **STOP AND THINK:** What is the ONE key finding you would lead with? What are the 2-3 supporting findings? What are the equity implications? Draft these in your mind before generating report.
  - [ ] 7.6 **GENERATE METHODOLOGY SUMMARY** - Write code to create `/outputs/methodology_summary.md` with sections: Introduction, Causal Graph, Methods, Results, Limitations
  - [ ] 7.7 **RUN & ANALYZE:** Execute generation, review markdown file
  - [ ] 7.8 **STOP AND THINK:** Is methodology summary clear for non-technical audience? Does it explain causal approach without jargon? Review and refine.
  - [ ] 7.9 **GENERATE POWERPOINT SLIDES** - Write code using python-pptx to create 8-slide deck: (1) Title, (2) Data, (3) Methods, (4) Main Results, (5) Bang-for-Buck, (6) Equity Findings, (7) Limitations, (8) Recommendations
  - [ ] 7.10 **RUN & ANALYZE:** Execute slide generation, save to `/outputs/presentation_slides.pptx`
  - [ ] 7.11 **STOP AND THINK:** Open slides and review. Are key figures included? Is text concise? Would this convince a policymaker? Refine if needed.
  - [ ] 7.12 **GENERATE INTERACTIVE VISUALIZATION** - Write code to create interactive Plotly version of bang-for-buck scatter with hover (institution name, state, MSI status, outcomes)
  - [ ] 7.13 **RUN & ANALYZE:** Execute interactive viz, save as HTML
  - [ ] 7.14 **STOP AND THINK:** Test interactivity - do hovers work? Is it useful for exploration? Document.
  - [ ] 7.15 **COMPILE RECOMMENDATIONS** - Based on all findings, write code to generate 3-5 specific, actionable recommendations with supporting data
  - [ ] 7.16 **RUN & ANALYZE:** Print recommendations
  - [ ] 7.17 **STOP AND THINK - CRITICAL:** Are recommendations justified by data? Are they specific enough to act on? Are they equitable? Revise if needed. Document final recommendations.
  - [ ] 7.18 **UPDATE README** - Write code to update `README.md` with: project overview, research question, key findings, how to run, dependencies, outputs
  - [ ] 7.19 **RUN & ANALYZE:** Execute README update, review file
  - [ ] 7.20 **CONVERT METHODOLOGY TO PDF** - Run command: `pandoc methodology_summary.md -o methodology_summary.pdf`
  - [ ] 7.21 **VERIFY ALL DELIVERABLES** - Write code to check that all required files exist and are non-empty
  - [ ] 7.22 **RUN & ANALYZE:** Execute verification, print checklist
  - [ ] 7.23 **STOP AND THINK:** All deliverables complete? Open each one to verify quality. Document completion.
  - [ ] 7.24 **REPORT GENERATION CHECKPOINT:** Document: "All deliverables complete. Methodology summary, slides, interactive viz, README all generated. Ready for final QA."

- [ ] 8.0 Final review and quality assurance
  - [ ] 8.1 **QA CHECK 1: COVARIATE BALANCE** - Write code to verify SMD <0.1 for at least 80% of confounders after matching
  - [ ] 8.2 **RUN & ANALYZE:** Execute check, calculate % balanced
  - [ ] 8.3 **STOP AND THINK:** Did you achieve adequate balance? If not, document which confounders remain imbalanced and why. This is a limitation.
  - [ ] 8.4 **QA CHECK 2: SAMPLE SIZES** - Write code to verify main analysis >500, treatment groups >200, subgroups >50
  - [ ] 8.5 **RUN & ANALYZE:** Print all sample sizes
  - [ ] 8.6 **STOP AND THINK:** Any analyses underpowered? Document sample size limitations.
  - [ ] 8.7 **QA CHECK 3: METHODS CONSISTENCY** - Write code to verify all 4 methods have same sign, overlapping CIs
  - [ ] 8.8 **RUN & ANALYZE:** Execute consistency check
  - [ ] 8.9 **STOP AND THINK:** Are methods consistent? If not, this is a major concern - revisit analysis. Document agreement level.
  - [ ] 8.10 **QA CHECK 4: STATISTICAL SIGNIFICANCE** - Write code to create table of all ATEs with significance flags (unadjusted and Bonferroni-adjusted)
  - [ ] 8.11 **RUN & ANALYZE:** Execute significance summary
  - [ ] 8.12 **STOP AND THINK:** How many findings are robust to multiple comparison correction? Don't overstate non-significant results. Document.
  - [ ] 8.13 **QA CHECK 5: VISUALIZATION QUALITY** - Manually review all figures in `/outputs/figures/` for quality, readability, colorblind-safety
  - [ ] 8.14 **STOP AND THINK:** Are all figures publication-quality? Would they look good in a presentation? Make final adjustments if needed.
  - [ ] 8.15 **QA CHECK 6: CODE QUALITY** - Review all scripts for: comments, no unused variables, consistent naming, no hardcoded paths
  - [ ] 8.16 **STOP AND THINK:** Is code readable and maintainable? Add comments where needed. Clean up.
  - [ ] 8.17 **QA CHECK 7: REPRODUCIBILITY** - Run all scripts sequentially from scratch in clean environment to verify end-to-end reproducibility
  - [ ] 8.18 **RUN & ANALYZE:** Execute full pipeline, capture any errors
  - [ ] 8.19 **STOP AND THINK:** Does everything run without errors? Are outputs identical to previous runs (accounting for bootstrap randomness with seed)? Document reproducibility.
  - [ ] 8.20 **FINAL SYNTHESIS** - Create comprehensive summary table with all ATEs from all methods and subgroups
  - [ ] 8.21 **SAVE FINAL SUMMARY** - Save to `/outputs/tables/final_summary.csv`
  - [ ] 8.22 **DOCUMENT SURPRISING FINDINGS** - Write in log: any unexpected results, counterintuitive patterns, findings that contradict expectations
  - [ ] 8.23 **STOP AND THINK - FINAL REFLECTION:** Step back and consider: What is the story the data tells? Does affordability matter for mobility? For whom does it matter most? What are the equity implications? Are you confident in these conclusions? What are the limitations? Document final reflection.
  - [ ] 8.24 **PREPARE FOR GIT COMMIT** - Stage all files: `git add src/ outputs/ README.md requirements.txt`
  - [ ] 8.25 **COMMIT ANALYSIS** - Commit with message: `git commit -m "Complete affordability-mobility causal analysis with 4 methods, equity subgroups, and deliverables"`
  - [ ] 8.26 **FINAL QA CHECKPOINT:** Document in log: "✅ ANALYSIS COMPLETE. Final N=[X]. Main finding: [One sentence]. Methods consistent: [Y/N]. Equity finding: [One sentence]. Limitations: [Brief]. Recommendations: [3-5 bullets]. Ready for stakeholder presentation."

## End of Task List

**REMEMBER:** This is an iterative, exploratory process. Let the data guide you. When you find something unexpected, investigate before proceeding. Document your thinking at each step. Good data science is about careful observation and thoughtful decision-making, not just running code.

**Analysis Philosophy:**
- Be curious: Ask "why?" when you see patterns
- Be skeptical: Question your assumptions
- Be transparent: Document decisions and limitations
- Be adaptive: Adjust your approach based on what you learn
- Be rigorous: Verify findings with multiple methods
- Be equitable: Center marginalized groups in your analysis
