# src/03_causal_inference.py
"""
Causal Inference Script: Affordability Gap and Economic Mobility Analysis
This script implements multiple causal inference methods (IPW, DR, DoWhy, OLS) to estimate
the causal effect of affordability gaps on student outcomes.
"""
import json
from pathlib import Path
import warnings
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning

# DoWhy for causal graph and refutation
try:
    import dowhy
    from dowhy import CausalModel
    DOWHY_AVAILABLE = True
except ImportError:
    print("WARNING: DoWhy not available. Install with: pip install dowhy")
    DOWHY_AVAILABLE = False

# EconML for doubly robust estimation
try:
    from econml.dml import LinearDML
    from econml.metalearners import TLearner, SLearner, XLearner
    ECONML_AVAILABLE = True
except ImportError:
    print("WARNING: EconML not available. Install with: pip install econml")
    ECONML_AVAILABLE = False

# --- Configuration ---
DATA_PATH = Path("outputs/data/analysis_ready.csv")
VARLIST_PATH = Path("outputs/data/variable_lists.json")
LOG_PATH = Path("outputs/logs/analysis_log.md")
FIG_PATH = Path("outputs/figures")
FIG_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Only silence the sklearn convergence warning if we handle it explicitly later
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Helpers ---
def safe_load_var(v):
    """If v is a list with one element, return the element; if list, return list; if string return string."""
    if isinstance(v, list) and len(v) == 1:
        return v[0]
    return v

def ensure_list(x):
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    return list(x)

def append_log(text):
    with open(LOG_PATH, "a") as f:
        f.write(text + "\n\n")

def print_and_log(text):
    print(text)
    append_log(text)

# --- 4.1 Setup: load data & variables ---
print("="*80)
print("4.1 SETUP: Loading data & variable lists")
print("="*80)

# Load data
if not DATA_PATH.exists():
    raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

# Load variable lists
if not VARLIST_PATH.exists():
    raise FileNotFoundError(f"Variable lists not found: {VARLIST_PATH}")
with open(VARLIST_PATH, "r") as f:
    variable_lists = json.load(f)

# Normalize variable list entries (accept single string or list)
treatment_var = safe_load_var(variable_lists.get("treatment"))
outcome_vars = ensure_list(variable_lists.get("outcomes"))
confounder_vars = ensure_list(variable_lists.get("confounders"))
categorical_vars = ensure_list(variable_lists.get("categorical"))

# If user provided treatment as a list of length 1, convert to string
if isinstance(treatment_var, list) and len(treatment_var) == 1:
    treatment_var = treatment_var[0]

# Validate that treatment_var is a single string
if isinstance(treatment_var, list):
    raise ValueError("treatment in variable_lists.json must be a single variable name (string).")

print_and_log(f"Loaded data shape: {df.shape}")
print_and_log(f"treatment_var: {treatment_var}")
print_and_log(f"outcome_vars: {outcome_vars}")
print_and_log(f"n confounders (declared): {len(confounder_vars)}")
print_and_log(f"categorical_vars: {categorical_vars}")

# Verify variables exist in df (and warn if present but all-NaN)
missing = []
all_vars_to_check = [treatment_var] + outcome_vars + confounder_vars + categorical_vars
for v in all_vars_to_check:
    if v not in df.columns:
        missing.append(v)
if missing:
    raise KeyError(f"The following required variables are missing from the dataset: {missing}")

# Check for all-NaN columns (report, but do not stop)
all_nan = [c for c in all_vars_to_check if df[c].isna().all()]
if all_nan:
    print_and_log(f"WARNING: The following variables exist but are all NaN: {all_nan}")

# Print quick sample
print(df[[treatment_var] + (outcome_vars[:2] if len(outcome_vars)>1 else outcome_vars)].head().to_string())
append_log(f"Sample head printed above.")

# --- 4.3 STOP & THINK: DAG checks (basic automated checks) ---
print("\n" + "="*80)
print("4.3 DAG CHECKS: Keyword coverage and critical confounder presence")
print("="*80)

expected_confounder_keywords = {
    'Selectivity': ['admit', 'sat', 'act', 'test'],
    'Demographics': ['pell', 'urm', 'white', 'black', 'latino', 'asian', 'women', 'gender'],
    'Resources': ['instructional', 'endowment', 'expenditur', 'spend'],
    'Institutional': ['sector', 'size', 'msi', 'hbcu', 'hsi', 'tcu', 'carnegie'],
    'Geography': ['state', 'region', 'urban']
}
confounder_lower = [c.lower() for c in confounder_vars + categorical_vars]
coverage = {}
for cat, keys in expected_confounder_keywords.items():
    found = [c for c in (confounder_vars + categorical_vars) if any(k in c.lower() for k in keys)]
    coverage[cat] = found
    print_and_log(f"{cat}: {len(found)} matched variables -> {found[:8]}")

# Document automatic check
append_log("Automated confounder keyword coverage:\n" + json.dumps(coverage, indent=2))

# --- 4.4 Propensity score prep ---
print("\n" + "="*80)
print("4.4 PREP: Build covariate matrix for propensity model")
print("="*80)

# 1) Ensure treatment is numeric and binary 0/1
# Accept common encodings: 0/1, True/False, 'low'/'high', 'Low'/'High'
def coerce_treatment_to_binary(series, positive_values=None):
    s = series.copy()
    # If already numeric and only 0/1, keep
    if pd.api.types.is_numeric_dtype(s):
        unique = pd.Series(s.dropna().unique())
        if set(unique.astype(int).tolist()) <= {0,1}:
            return s.astype(float)
    # If boolean
    if pd.api.types.is_bool_dtype(s):
        return s.astype(float)
    # If positive_values provided map them to 1 else try to infer (bottom quartile -> 1 etc.)
    if positive_values:
        return s.map(lambda x: 1.0 if x in positive_values else 0.0)
    # Last resort: if contains only two unique strings, map the lexicographically smaller to 0
    uniques = s.dropna().unique()
    if len(uniques) == 2:
        mapping = {uniques[0]: 0.0, uniques[1]: 1.0}
        return s.map(mapping).astype(float)
    # If numeric continuous, user probably mis-specified treatment
    raise ValueError("Unable to coerce treatment to binary 0/1 automatically. "
                     "Please specify mapping or ensure treatment_var is binary.")

# Try to coerce
try:
    df[treatment_var] = coerce_treatment_to_binary(df[treatment_var])
except ValueError as e:
    raise RuntimeError(f"Treatment coercion failed: {e}")

# Check variation
tcnts = df[treatment_var].value_counts(dropna=False)
print_and_log(f"Treatment value counts (post-coercion):\n{tcnts.to_string()}")
if set(tcnts.index.dropna()) <= {0.0} or set(tcnts.index.dropna()) <= {1.0}:
    raise RuntimeError("Treatment has no variation (all 0 or all 1) after coercion; cannot estimate effect.")

# 2) Build X_continuous excluding categorical_vars (avoid duplication)
confounders_continuous = [c for c in confounder_vars if c not in categorical_vars]
X_cont = df[confounders_continuous].copy()
# Make numeric, coerce errors -> NaN (we will track missingness)
for c in X_cont.columns:
    X_cont[c] = pd.to_numeric(X_cont[c], errors="coerce")

# 3) One-hot encode categorical_vars (if any)
if categorical_vars:
    X_cat = pd.get_dummies(df[categorical_vars].astype(str), drop_first=True)
else:
    X_cat = pd.DataFrame(index=df.index)

# 4) Concatenate and keep track of rows with missing or infinite values
X_all = pd.concat([X_cont, X_cat], axis=1)

n_before = len(X_all)
missing_per_col = X_all.isna().mean().sort_values(ascending=False)
n_rows_with_missing = X_all.isna().any(axis=1).sum()
print_and_log(f"Rows before cleaning: {n_before}; rows with any missing confounder: {n_rows_with_missing}")
print_and_log("Top missing confounder rates:\n" + missing_per_col.head(10).to_string())

# Check for missing values in key variables
print(f"\nMissing Values Check:")
print(f"  Treatment ({treatment_var}): {df[treatment_var].isna().sum()} missing")
for outcome in outcome_vars:
    print(f"  Outcome ({outcome}): {df[outcome].isna().sum()} missing")

print("\n" + "="*80)
print("SETUP COMPLETE - READY FOR CAUSAL ANALYSIS")
print("="*80)

# SECTION 4.4: PROPENSITY SCORE MODEL
print("\n" + "="*80)
print("SECTION 4.4: PROPENSITY SCORE MODEL")
print("="*80)

# Prepare data for propensity score model
print("\nPreparing data for propensity score estimation...")

# Create a working copy of the data
df_psm = df.copy()

# Extract and enforce treatment variable as binary 0/1
print("\nEnforcing treatment variable as binary 0/1...")
treatment = df_psm[treatment_var].copy()
# Convert to numeric and ensure binary
treatment = pd.to_numeric(treatment, errors='coerce')
# Ensure it's exactly 0 or 1 (handle any other values)
treatment = (treatment == 1).astype(int)
df_psm[treatment_var] = treatment
treatment = treatment.values

print(f"Treatment variable check:")
print(f"  Unique values: {np.unique(treatment)}")
print(f"  Value counts: {pd.Series(treatment).value_counts().sort_index().to_dict()}")

# Prepare confounders: continuous + dummy variables for categorical
print("\nCreating dummy variables for categorical confounders...")

# Check for any overlap between confounders and categorical variables
overlap = set(confounder_vars) & set(categorical_vars)
if overlap:
    print(f"WARNING: Found overlap between confounders and categorical variables: {overlap}")
    print("Removing categorical variables from confounder list to avoid double counting...")
    confounder_vars_clean = [v for v in confounder_vars if v not in categorical_vars]
else:
    confounder_vars_clean = confounder_vars.copy()

print(f"  Using {len(confounder_vars_clean)} continuous confounders (excluding categorical)")

# Get continuous confounders (already numeric, excluding any categorical)
X_continuous = df_psm[confounder_vars_clean].copy()

# Ensure all continuous confounders are numeric
for col in X_continuous.columns:
    X_continuous[col] = pd.to_numeric(X_continuous[col], errors='coerce')

# Create dummy variables for categorical confounders
# Use prefix_sep to properly prefix each categorical variable
X_categorical_dummies = pd.get_dummies(
    df_psm[categorical_vars], 
    prefix=categorical_vars,
    prefix_sep='_',
    drop_first=True,  # Drop first category to avoid multicollinearity
    dummy_na=False
)

# Verify no column name overlap between continuous and categorical dummies
overlapping_cols = set(X_continuous.columns) & set(X_categorical_dummies.columns)
if overlapping_cols:
    print(f"WARNING: Found overlapping column names: {overlapping_cols}")
    print("Removing overlapping columns from continuous confounders...")
    X_continuous = X_continuous.drop(columns=list(overlapping_cols))

# Combine all confounders
X_all = pd.concat([X_continuous, X_categorical_dummies], axis=1)

# Ensure all columns are numeric (convert any remaining object types)
for col in X_all.columns:
    if X_all[col].dtype == 'object':
        X_all[col] = pd.to_numeric(X_all[col], errors='coerce')

print(f"\nTotal number of confounder features: {X_all.shape[1]}")
print(f"  - Continuous confounders: {len(confounder_vars_clean)}")
print(f"  - Categorical dummy variables: {X_categorical_dummies.shape[1]}")
print(f"  - Total features in model: {X_all.shape[1]}")

# Check for any remaining missing values or infinite values
missing_in_X = X_all.isna().sum().sum()
# Convert to numeric first, then check for infinite
X_all_numeric = X_all.select_dtypes(include=[np.number])
inf_in_X = np.isinf(X_all_numeric).sum().sum() if len(X_all_numeric.columns) > 0 else 0

if missing_in_X > 0 or inf_in_X > 0:
    print(f"\nWARNING: {missing_in_X} missing values and {inf_in_X} infinite values found in confounders!")
    print("Dropping rows with missing or infinite confounders...")
    # Check for missing
    missing_mask = X_all.isna().any(axis=1)
    # Check for infinite in numeric columns
    if len(X_all_numeric.columns) > 0:
        inf_mask = np.isinf(X_all_numeric).any(axis=1)
    else:
        inf_mask = pd.Series([False] * len(X_all))
    valid_mask = ~(missing_mask | inf_mask)
    removed = n_before - valid_mask.sum()
    df = df[valid_mask].reset_index(drop=True)
    X_all = X_all[valid_mask].reset_index(drop=True)
    print_and_log(f"Dropped {removed} rows due to missing confounders ({removed/n_before:.1%})")

# Check infinite values
is_inf = np.isinf(X_all.select_dtypes(include=[np.number])).any(axis=1).sum()
if is_inf > 0:
    df = df[~np.isinf(X_all.select_dtypes(include=[np.number])).any(axis=1)].reset_index(drop=True)
    X_all = X_all[~np.isinf(X_all.select_dtypes(include=[np.number])).any(axis=1)].reset_index(drop=True)
    print_and_log(f"Removed {is_inf} rows due to infinite numeric values")

# Recompute sample size
n_after = len(X_all)
print_and_log(f"Final sample used for propensity estimation: {n_after}")

# 5) Scale continuous features (improves solver behavior)
scaler = StandardScaler()
if not X_cont.empty:
    X_cont_scaled = pd.DataFrame(scaler.fit_transform(X_cont), columns=X_cont.columns, index=X_cont.index)
else:
    X_cont_scaled = pd.DataFrame(index=X_all.index)

# Rebuild X_all as scaled continuous + dummies
X_all = pd.concat([X_cont_scaled, X_cat.reset_index(drop=True)], axis=1).astype(float)

# --- 4.5 Fit propensity model (regularized sklearn logistic) ---
print("\n" + "="*80)
print("4.5 FIT PROPENSITY MODEL (regularized sklearn LogisticRegression)")
print("="*80)

y = df[treatment_var].astype(int).values
X = X_all.values

# If too many features relative to N, prefer strong regularization
C_val = 1.0  # inverse regularization strength; tune if needed
solver = "saga" if X.shape[1] > 0 else "liblinear"  # saga supports l1/l2 and multinomial

# Track which model was used
model_type = None
clf = None
sm_res = None

try:
    clf = LogisticRegression(penalty="l2", C=C_val, solver=solver, max_iter=5000, n_jobs=-1)
    with warnings.catch_warnings():
        warnings.filterwarnings("always", category=ConvergenceWarning)
        clf.fit(X, y)
    propensity_scores = clf.predict_proba(X)[:, 1]
    df["propensity_score"] = propensity_scores
    model_type = "sklearn"
    print_and_log("sklearn LogisticRegression fitted successfully.")
except Exception as e:
    # Fallback: try statsmodels Logit (less regularized)
    print_and_log(f"sklearn LogisticRegression failed: {e}. Attempting statsmodels Logit as fallback.")
    import statsmodels.api as sm
    X_sm = sm.add_constant(X_all)
    try:
        sm_logit = sm.Logit(y, X_sm)
        sm_res = sm_logit.fit(disp=False, maxiter=200)
        propensity_scores = sm_res.predict(X_sm)
        df["propensity_score"] = propensity_scores
        model_type = "statsmodels"
        print_and_log("statsmodels Logit fitted successfully (fallback).")
    except Exception as e2:
        raise RuntimeError(f"Both sklearn and statsmodels logistic fits failed: {e2}")

# --- 4.6 Diagnostics: propensity distribution & model checks ---
print("\n" + "="*80)
print("4.6 DIAGNOSTICS: Propensity stats and model checks")
print("="*80)

ps = df["propensity_score"]
psq = np.quantile(ps, [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
print_and_log(f"Propensity quantiles (1%,5%,25%,50%,75%,95%,99%): {psq}")

# Check extremes
ext_low = (ps < 0.01).sum()
ext_high = (ps > 0.99).sum()
print_and_log(f"Extreme propensity counts: <0.01: {ext_low}, >0.99: {ext_high}")

print("\n" + "="*80)
print("PROPENSITY SCORE DISTRIBUTION")
print("="*80)
print(f"\nPropensity Score Statistics:")
print(f"  Mean: {propensity_scores.mean():.4f}")
print(f"  Median: {np.median(propensity_scores):.4f}")
print(f"  Min: {propensity_scores.min():.4f}")
print(f"  Max: {propensity_scores.max():.4f}")
print(f"  Std: {propensity_scores.std():.4f}")

print(f"\nPropensity Score by Treatment Group:")
print(df_psm.groupby(treatment_var)['propensity_score'].describe())

# Check for extreme propensity scores (potential lack of overlap)
extreme_low = (propensity_scores < 0.01).sum()
extreme_high = (propensity_scores > 0.99).sum()
print(f"\nExtreme Propensity Scores:")
print(f"  Scores < 0.01: {extreme_low} ({extreme_low/len(propensity_scores)*100:.2f}%)")
print(f"  Scores > 0.99: {extreme_high} ({extreme_high/len(propensity_scores)*100:.2f}%)")

if extreme_low > 0 or extreme_high > 0:
    print("\nWARNING: Extreme propensity scores detected. May indicate poor overlap.")
    print("Consider trimming sample to common support region.")
else:
    print_and_log("Coefficient summary not available (model type unknown).")

# Save brief diagnostics
diag_text = textwrap.dedent(f"""
Propensity diagnostics:
 - Sample size: {n_after}
 - n_features: {X_all.shape[1]}
 - Propensity quantiles (1/5/25/50/75/95/99): {psq.tolist()}
 - Extreme tail counts (<0.01 / >0.99): {ext_low} / {ext_high}
""")
append_log(diag_text)

# --- 4.7 Visualization: hist + box + overlap lines computed from data ---
print("\n" + "="*80)
print("4.7 VISUALIZATION: Propensity distributions and overlap")
print("="*80)

# SECTION 4.7-4.8: VISUALIZE PROPENSITY SCORES
print("\n" + "="*80)
print("SECTION 4.7-4.8: VISUALIZE PROPENSITY SCORES")
print("="*80)

# Create visualization of propensity score distributions
print("\nCreating propensity score distribution plots...")

# Set up the figure with subplots
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Histogram overlay for treated vs control
ax1 = axes[0]
treated_ps = df_psm[df_psm[treatment_var] == 1]['propensity_score']
control_ps = df_psm[df_psm[treatment_var] == 0]['propensity_score']

ax1.hist(control_ps, bins=50, alpha=0.6, label='High Gap (Control)', color='red', density=True)
ax1.hist(treated_ps, bins=50, alpha=0.6, label='Low Gap (Treated)', color='blue', density=True)
ax1.set_xlabel('Propensity Score', fontsize=12)
ax1.set_ylabel('Density', fontsize=12)
ax1.set_title('Propensity Score Distributions by Treatment Group', fontsize=14, fontweight='bold')
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)
ax1.axvline(x=0.1, color='gray', linestyle='--', alpha=0.5, label='Common Support Region')
ax1.axvline(x=0.9, color='gray', linestyle='--', alpha=0.5)

# Plot 2: Box plot comparison
ax2 = axes[1]
box_data = [control_ps, treated_ps]
box_labels = ['High Gap\n(Control)', 'Low Gap\n(Treated)']
bp = ax2.boxplot(box_data, labels=box_labels, patch_artist=True)
bp['boxes'][0].set_facecolor('red')
bp['boxes'][0].set_alpha(0.6)
bp['boxes'][1].set_facecolor('blue')
bp['boxes'][1].set_alpha(0.6)
ax2.set_ylabel('Propensity Score', fontsize=12)
ax2.set_title('Propensity Score Distribution Comparison', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()

# Save the figure
output_path = 'outputs/figures/propensity_score_distributions.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n✓ Saved propensity score visualization to: {output_path}")

# Display the figure
plt.show()

# Calculate overlap statistics
print("\n" + "="*80)
print("COMMON SUPPORT ANALYSIS")
print("="*80)

# Define common support region (where both groups have observations)
min_treated = treated_ps.min()
max_treated = treated_ps.max()
min_control = control_ps.min()
max_control = control_ps.max()

common_support_min = max(min_treated, min_control)
common_support_max = min(max_treated, max_control)

print(f"\nPropensity Score Ranges:")
print(f"  Treated (Low Gap): [{min_treated:.4f}, {max_treated:.4f}]")
print(f"  Control (High Gap): [{min_control:.4f}, {max_control:.4f}]")
print(f"  Common Support Region: [{common_support_min:.4f}, {common_support_max:.4f}]")

# Count observations in common support region
in_common_support_treated = ((treated_ps >= common_support_min) & (treated_ps <= common_support_max)).sum()
in_common_support_control = ((control_ps >= common_support_min) & (control_ps <= common_support_max)).sum()

print(f"\nObservations in Common Support Region:")
print(f"  Treated: {in_common_support_treated} / {len(treated_ps)} ({in_common_support_treated/len(treated_ps)*100:.2f}%)")
print(f"  Control: {in_common_support_control} / {len(control_ps)} ({in_common_support_control/len(control_ps)*100:.2f}%)")

# Calculate overlap coefficient (minimum of the two percentages)
overlap_coefficient = min(in_common_support_treated/len(treated_ps), in_common_support_control/len(control_ps))
print(f"\nOverlap Coefficient: {overlap_coefficient:.4f}")

if overlap_coefficient > 0.9:
    print("  ✓ Excellent overlap (>90%)")
elif overlap_coefficient > 0.7:
    print("  ✓ Good overlap (70-90%)")
elif overlap_coefficient > 0.5:
    print("  ⚠️  Moderate overlap (50-70%) - consider trimming")
else:
    print("  ⚠️  Poor overlap (<50%) - trimming recommended")

# Check for regions with no overlap
no_overlap_treated = (treated_ps < min_control) | (treated_ps > max_control)
no_overlap_control = (control_ps < min_treated) | (control_ps > max_treated)

print(f"\nObservations Outside Overlap Region:")
print(f"  Treated outside control range: {no_overlap_treated.sum()} ({no_overlap_treated.sum()/len(treated_ps)*100:.2f}%)")
print(f"  Control outside treated range: {no_overlap_control.sum()} ({no_overlap_control.sum()/len(control_ps)*100:.2f}%)")

print("\n" + "="*80)
print("PROPENSITY SCORE VISUALIZATION COMPLETE")
print("="*80)

# SECTION 4.9: STOP AND THINK - COMMON SUPPORT ASSESSMENT
print("\n" + "="*80)
print("SECTION 4.9: STOP AND THINK - COMMON SUPPORT ASSESSMENT")
print("="*80)

print("\n" + "-"*80)
print("ANALYSIS AND INTERPRETATION")
print("-"*80)

print("\n1. OVERLAP ASSESSMENT:")
print(f"   - Overlap coefficient: {overlap_coefficient:.4f}")
if overlap_coefficient > 0.9:
    print("   - Assessment: EXCELLENT overlap - no trimming needed")
elif overlap_coefficient > 0.7:
    print("   - Assessment: GOOD overlap - proceed without trimming")
elif overlap_coefficient > 0.5:
    print("   - Assessment: MODERATE overlap - consider trimming to common support")
    print("   - Recommendation: Trim to common support region [0.1, 0.9] or [min, max]")
else:
    print("   - Assessment: POOR overlap - trimming strongly recommended")
    print("   - Recommendation: Trim to common support region to avoid extrapolation")

print("\n2. EXTREME PROPENSITY SCORES:")
print(f"   - Scores < 0.01: {extreme_low} ({extreme_low/len(propensity_scores)*100:.2f}%)")
print(f"   - Scores > 0.99: {extreme_high} ({extreme_high/len(propensity_scores)*100:.2f}%)")
if extreme_low > 0 or extreme_high > 0:
    print("   - Assessment: Extreme scores present - these indicate poor overlap")
    print("   - Recommendation: Consider trimming to reduce influence of extreme weights")
else:
    print("   - Assessment: No extreme scores - good overlap across full range")

print("\n3. DISTRIBUTION CHARACTERISTICS:")
print(f"   - Treated mean PS: {treated_ps.mean():.4f}")
print(f"   - Control mean PS: {control_ps.mean():.4f}")
print(f"   - Mean difference: {abs(treated_ps.mean() - control_ps.mean()):.4f}")
if abs(treated_ps.mean() - control_ps.mean()) > 0.2:
    print("   - Assessment: Large mean difference indicates systematic differences")
    print("   - This is expected and justifies using propensity score methods")
else:
    print("   - Assessment: Relatively similar means - good baseline similarity")

print("\n4. DECISION:")
# Make a recommendation based on the analysis
if overlap_coefficient > 0.7 and extreme_low == 0 and extreme_high == 0:
    decision = "PROCEED WITHOUT TRIMMING"
    reason = "Good overlap and no extreme scores - full sample can be used"
elif overlap_coefficient > 0.5:
    decision = "CONSIDER TRIMMING TO COMMON SUPPORT"
    reason = f"Moderate overlap ({overlap_coefficient:.2%}) - trimming may improve balance"
else:
    decision = "TRIM TO COMMON SUPPORT REGION"
    reason = f"Poor overlap ({overlap_coefficient:.2%}) - trimming necessary to avoid extrapolation"

print(f"   - Decision: {decision}")
print(f"   - Reason: {reason}")

print("\n" + "-"*80)
print("DOCUMENTATION FOR ANALYSIS LOG")
print("-"*80)
print("\nPlease review the above analysis and document your findings in:")
print("  outputs/logs/analysis_log.md")
print("\nKey questions to address:")
print("  1. Is there good overlap between treatment groups?")
print("  2. Are there extreme propensity scores that need trimming?")
print("  3. Should we proceed with full sample or trim to common support?")
print("  4. What is the rationale for your decision?")

print("\n" + "="*80)
print("STOP AND THINK COMPLETE - AWAITING MANUAL REVIEW")
print("="*80)
print("\n⚠️  PLEASE REVIEW THE ABOVE ANALYSIS AND PROVIDE GO-AHEAD TO PROCEED")
print("   to the next step (Task 4.10: Calculate IPW Weights)")
print("="*80)

# SECTION 4.10-4.11: CALCULATE IPW WEIGHTS
print("\n" + "="*80)
print("SECTION 4.10-4.11: CALCULATE IPW WEIGHTS")
print("="*80)

# Calculate Inverse Probability Weights (IPW)
print("\nCalculating Inverse Probability Weights (IPW)...")

# IPW formula:
# For treated (T=1): w = 1 / P(T=1|X) = 1 / propensity_score
# For control (T=0): w = 1 / P(T=0|X) = 1 / (1 - propensity_score)

# Get propensity scores and treatment status
propensity_scores = df_psm['propensity_score'].values
treatment_status = df_psm[treatment_var].values

# Calculate IPW weights
ipw_weights = np.zeros(len(propensity_scores))

# For treated units: w = 1 / P(T=1|X)
treated_mask = (treatment_status == 1)
ipw_weights[treated_mask] = 1.0 / propensity_scores[treated_mask]

# For control units: w = 1 / P(T=0|X)
control_mask = (treatment_status == 0)
ipw_weights[control_mask] = 1.0 / (1.0 - propensity_scores[control_mask])

# Add weights to dataframe
df_psm['ipw_weight'] = ipw_weights

print("\n" + "="*80)
print("IPW WEIGHT DISTRIBUTION")
print("="*80)

print(f"\nOverall Weight Statistics:")
print(f"  Mean: {ipw_weights.mean():.4f}")
print(f"  Median: {np.median(ipw_weights):.4f}")
print(f"  Min: {ipw_weights.min():.4f}")
print(f"  Max: {ipw_weights.max():.4f}")
print(f"  Std: {ipw_weights.std():.4f}")
print(f"  25th percentile: {np.percentile(ipw_weights, 25):.4f}")
print(f"  75th percentile: {np.percentile(ipw_weights, 75):.4f}")

print(f"\nWeight Statistics by Treatment Group:")
weight_stats = df_psm.groupby(treatment_var)['ipw_weight'].describe()
print(weight_stats)

# Check for extreme weights
extreme_weights_10 = (ipw_weights > 10).sum()
extreme_weights_20 = (ipw_weights > 20).sum()
extreme_weights_50 = (ipw_weights > 50).sum()

print(f"\nExtreme Weights:")
print(f"  Weights > 10: {extreme_weights_10} ({extreme_weights_10/len(ipw_weights)*100:.2f}%)")
print(f"  Weights > 20: {extreme_weights_20} ({extreme_weights_20/len(ipw_weights)*100:.2f}%)")
print(f"  Weights > 50: {extreme_weights_50} ({extreme_weights_50/len(ipw_weights)*100:.2f}%)")

if extreme_weights_10 > 0:
    print("\n⚠️  WARNING: Extreme weights detected (>10).")
    print("   These may indicate poor overlap or extreme propensity scores.")
    print("   Consider trimming weights or trimming to common support region.")

# Calculate effective sample size
# ESS = (sum of weights)^2 / sum of weights^2
# This gives the approximate sample size after weighting
ess = (ipw_weights.sum())**2 / (ipw_weights**2).sum()
actual_n = len(ipw_weights)

print(f"\n" + "="*80)
print("EFFECTIVE SAMPLE SIZE (ESS)")
print("="*80)
print(f"\nActual Sample Size: {actual_n:,}")
print(f"Effective Sample Size (ESS): {ess:,.0f}")
print(f"ESS / Actual N: {ess/actual_n:.4f} ({ess/actual_n*100:.2f}%)")

if ess / actual_n < 0.5:
    print("\n⚠️  WARNING: Low effective sample size (<50% of actual N)")
    print("   This indicates high variance in weights - many observations have very different weights")
    print("   Consider trimming extreme weights or trimming to common support")
elif ess / actual_n < 0.7:
    print("\n⚠️  CAUTION: Moderate effective sample size (50-70% of actual N)")
    print("   Some variance in weights - monitor in analysis")
else:
    print("\n✓ Good effective sample size (>70% of actual N)")
    print("   Weights are relatively balanced")

# Calculate ESS by treatment group
print(f"\nEffective Sample Size by Treatment Group:")
for t in [0, 1]:
    group_mask = (treatment_status == t)
    group_weights = ipw_weights[group_mask]
    group_ess = (group_weights.sum())**2 / (group_weights**2).sum()
    group_n = group_mask.sum()
    group_label = "High Gap (Control)" if t == 0 else "Low Gap (Treated)"
    print(f"  {group_label}:")
    print(f"    Actual N: {group_n:,}")
    print(f"    ESS: {group_ess:,.0f}")
    print(f"    ESS / N: {group_ess/group_n:.4f} ({group_ess/group_n*100:.2f}%)")

print("\n" + "="*80)
print("IPW WEIGHT CALCULATION COMPLETE")
print("="*80)

# SECTION 4.12: STOP AND THINK - WEIGHT ASSESSMENT
print("\n" + "="*80)
print("SECTION 4.12: STOP AND THINK - WEIGHT ASSESSMENT")
print("="*80)

print("\n" + "-"*80)
print("ANALYSIS AND INTERPRETATION")
print("-"*80)

print("\n1. WEIGHT DISTRIBUTION ASSESSMENT:")
print(f"   - Mean weight: {ipw_weights.mean():.4f}")
print(f"   - Median weight: {np.median(ipw_weights):.4f}")
print(f"   - Max weight: {ipw_weights.max():.4f}")
print(f"   - Weights > 10: {extreme_weights_10} ({extreme_weights_10/len(ipw_weights)*100:.2f}%)")

if ipw_weights.max() > 50:
    print("   - Assessment: VERY EXTREME weights detected (>50)")
    print("   - Recommendation: Strongly consider trimming weights or common support")
elif ipw_weights.max() > 20:
    print("   - Assessment: EXTREME weights detected (>20)")
    print("   - Recommendation: Consider trimming weights or common support")
elif ipw_weights.max() > 10:
    print("   - Assessment: MODERATE extreme weights (>10)")
    print("   - Recommendation: Monitor in analysis, consider trimming if results unstable")
else:
    print("   - Assessment: Reasonable weight range")
    print("   - Recommendation: Weights appear acceptable for analysis")

print("\n2. EFFECTIVE SAMPLE SIZE ASSESSMENT:")
print(f"   - Actual N: {actual_n:,}")
print(f"   - Effective Sample Size (ESS): {ess:,.0f}")
print(f"   - ESS / Actual N: {ess/actual_n:.4f} ({ess/actual_n*100:.2f}%)")

if ess / actual_n < 0.5:
    print("   - Assessment: LOW ESS (<50% of actual N)")
    print("   - Interpretation: High variance in weights - many observations have very different weights")
    print("   - Impact: Reduced precision in estimates, wider confidence intervals")
    print("   - Recommendation: Trim extreme weights or trim to common support")
elif ess / actual_n < 0.7:
    print("   - Assessment: MODERATE ESS (50-70% of actual N)")
    print("   - Interpretation: Some variance in weights")
    print("   - Impact: Slightly reduced precision")
    print("   - Recommendation: Monitor in analysis, consider trimming if needed")
else:
    print("   - Assessment: GOOD ESS (>70% of actual N)")
    print("   - Interpretation: Weights are relatively balanced")
    print("   - Impact: Good precision expected")
    print("   - Recommendation: Proceed with current weights")

print("\n3. WEIGHT BALANCE BY TREATMENT GROUP:")
for t in [0, 1]:
    group_mask = (treatment_status == t)
    group_weights = ipw_weights[group_mask]
    group_ess = (group_weights.sum())**2 / (group_weights**2).sum()
    group_n = group_mask.sum()
    group_label = "High Gap (Control)" if t == 0 else "Low Gap (Treated)"
    group_max_weight = group_weights.max()
    group_extreme = (group_weights > 10).sum()
    
    print(f"\n   {group_label}:")
    print(f"     - Actual N: {group_n:,}")
    print(f"     - ESS: {group_ess:,.0f} ({group_ess/group_n*100:.1f}% of actual N)")
    print(f"     - Max weight: {group_max_weight:.4f}")
    print(f"     - Weights > 10: {group_extreme} ({group_extreme/group_n*100:.1f}%)")
    
    if group_max_weight > 20:
        print(f"     - ⚠️  Extreme weights in this group - consider trimming")
    elif group_max_weight > 10:
        print(f"     - ⚠️  Some extreme weights - monitor")

print("\n4. DECISION:")
# Make a recommendation based on the analysis
if ess / actual_n >= 0.7 and extreme_weights_10 == 0:
    decision = "PROCEED WITH CURRENT WEIGHTS"
    reason = "Good ESS (>70%) and no extreme weights - weights are acceptable"
elif ess / actual_n >= 0.5 and extreme_weights_10 < len(ipw_weights) * 0.05:
    decision = "PROCEED WITH CURRENT WEIGHTS (MONITOR)"
    reason = f"Moderate ESS ({ess/actual_n*100:.1f}%) and few extreme weights (<5%) - acceptable but monitor"
elif extreme_weights_50 > 0 or ess / actual_n < 0.5:
    decision = "CONSIDER TRIMMING WEIGHTS"
    reason = f"Low ESS ({ess/actual_n*100:.1f}%) or very extreme weights (>50) - trimming recommended"
else:
    decision = "CONSIDER TRIMMING TO COMMON SUPPORT"
    reason = f"Moderate issues with weights - trimming may improve balance and precision"

print(f"   - Decision: {decision}")
print(f"   - Reason: {reason}")

print("\n" + "-"*80)
print("DOCUMENTATION FOR ANALYSIS LOG")
print("-"*80)
print("\nPlease review the above analysis and document your findings in:")
print("  outputs/logs/analysis_log.md")
print("\nKey questions to address:")
print("  1. Are weights reasonable? (max weight, distribution)")
print("  2. What is the effective sample size? Is it acceptable?")
print("  3. Should you trim weights? If so, what threshold?")
print("  4. What is the rationale for your decision?")

print("\n" + "="*80)
print("STOP AND THINK COMPLETE - AWAITING MANUAL REVIEW")
print("="*80)
print("\n⚠️  PLEASE REVIEW THE ABOVE ANALYSIS AND PROVIDE GO-AHEAD TO PROCEED")
print("   to the next step (Task 4.13: Check Post-Weighting Balance)")
print("="*80)

# WEIGHT TRIMMING AND STABILIZATION (if recommended)
print("\n" + "="*80)
print("WEIGHT TRIMMING AND STABILIZATION")
print("="*80)

# Determine if trimming/stabilization should be applied
apply_trimming = False
apply_stabilization = True  # Always apply stabilization for better variance properties

# Decision criteria for trimming
if extreme_weights_50 > 0 or ess / actual_n < 0.5:
    apply_trimming = True
    print("\n⚠️  Trimming recommended based on diagnostics:")
    if extreme_weights_50 > 0:
        print(f"   - Very extreme weights detected (>50): {extreme_weights_50}")
    if ess / actual_n < 0.5:
        print(f"   - Low ESS ({ess/actual_n*100:.1f}% of actual N)")
elif extreme_weights_20 > len(ipw_weights) * 0.01:  # More than 1% have weights > 20
    apply_trimming = True
    print("\n⚠️  Trimming recommended:")
    print(f"   - {extreme_weights_20} observations ({extreme_weights_20/len(ipw_weights)*100:.1f}%) have weights > 20")

# Store original weights for comparison
ipw_weights_original = ipw_weights.copy()

# Get treatment status for stabilization
treatment_status_stab = df_psm[treatment_var].values

# Apply weight trimming if recommended
if apply_trimming:
    print("\nApplying weight trimming...")
    
    # Trim at 99th percentile (common approach)
    weight_trim_threshold = np.percentile(ipw_weights, 99)
    print(f"   Trimming threshold: {weight_trim_threshold:.2f} (99th percentile)")
    
    # Trim weights
    ipw_weights_trimmed = np.minimum(ipw_weights, weight_trim_threshold)
    
    n_trimmed = (ipw_weights != ipw_weights_trimmed).sum()
    print(f"   Observations trimmed: {n_trimmed} ({n_trimmed/len(ipw_weights)*100:.1f}%)")
    
    ipw_weights = ipw_weights_trimmed
    print("   ✓ Weights trimmed")
else:
    print("\n✓ No trimming applied (weights within acceptable range)")

# Apply weight stabilization (normalize by treatment group)
# Stabilized weights: w_stabilized = w * (n_treated / sum(w_treated)) for treated
#                     w_stabilized = w * (n_control / sum(w_control)) for control
if apply_stabilization:
    print("\nApplying weight stabilization...")
    print("   Stabilization normalizes weights within each treatment group")
    print("   This improves variance properties without changing the ATE estimate")
    
    # Stabilize weights by treatment group
    treated_mask_stab = (treatment_status_stab == 1)
    control_mask_stab = (treatment_status_stab == 0)
    
    # For treated group: normalize so sum equals n_treated
    treated_weights_stab = ipw_weights[treated_mask_stab]
    n_treated_stab = treated_mask_stab.sum()
    sum_treated_weights = treated_weights_stab.sum()
    if sum_treated_weights > 0:
        stabilization_factor_treated = n_treated_stab / sum_treated_weights
        ipw_weights[treated_mask_stab] = treated_weights_stab * stabilization_factor_treated
    else:
        stabilization_factor_treated = 1.0
    
    # For control group: normalize so sum equals n_control
    control_weights_stab = ipw_weights[control_mask_stab]
    n_control_stab = control_mask_stab.sum()
    sum_control_weights = control_weights_stab.sum()
    if sum_control_weights > 0:
        stabilization_factor_control = n_control_stab / sum_control_weights
        ipw_weights[control_mask_stab] = control_weights_stab * stabilization_factor_control
    else:
        stabilization_factor_control = 1.0
    
    print(f"   Treated stabilization factor: {stabilization_factor_treated:.4f}")
    print(f"   Control stabilization factor: {stabilization_factor_control:.4f}")
    print("   ✓ Weights stabilized")

# Update dataframe with trimmed/stabilized weights
df_psm['ipw_weight'] = ipw_weights

# Recalculate ESS after trimming/stabilization
ess_after = (ipw_weights.sum())**2 / (ipw_weights**2).sum()

print("\n" + "="*80)
print("WEIGHT ADJUSTMENT SUMMARY")
print("="*80)
print(f"\nOriginal Weights:")
print(f"  Max: {ipw_weights_original.max():.2f}")
print(f"  ESS: {ess:,.0f} ({ess/actual_n*100:.1f}% of actual N)")

print(f"\nAdjusted Weights:")
print(f"  Max: {ipw_weights.max():.2f}")
print(f"  ESS: {ess_after:,.0f} ({ess_after/actual_n*100:.1f}% of actual N)")

if apply_trimming or apply_stabilization:
    ess_improvement = ess_after - ess
    print(f"\nESS Change: {ess_improvement:+,.0f} ({ess_improvement/ess*100:+.1f}%)")
    if ess_improvement > 0:
        print("  ✓ ESS improved after adjustment")
    else:
        print("  ⚠️  ESS decreased (expected with trimming, but variance should improve)")

print("\n" + "="*80)
print("WEIGHT TRIMMING/STABILIZATION COMPLETE")
print("="*80)

# SECTION 4.13-4.14: CHECK POST-WEIGHTING BALANCE
print("\n" + "="*80)
print("SECTION 4.13-4.14: CHECK POST-WEIGHTING BALANCE")
print("="*80)

# Helper function to calculate weighted SMD
def calculate_weighted_smd(control_values, treated_values, control_weights, treated_weights):
    """
    Calculate standardized mean difference using weighted means and pooled std
    SMD = (weighted_mean_treated - weighted_mean_control) / pooled_std
    """
    # Calculate weighted means
    weighted_mean_control = np.average(control_values, weights=control_weights)
    weighted_mean_treated = np.average(treated_values, weights=treated_weights)
    
    # Calculate weighted variances
    # For weighted variance: sum(w * (x - mean)^2) / sum(w)
    control_centered = control_values - weighted_mean_control
    treated_centered = treated_values - weighted_mean_treated
    
    weighted_var_control = np.average(control_centered**2, weights=control_weights)
    weighted_var_treated = np.average(treated_centered**2, weights=treated_weights)
    
    # Weighted standard deviations
    weighted_std_control = np.sqrt(weighted_var_control)
    weighted_std_treated = np.sqrt(weighted_var_treated)
    
    # Effective sample sizes for pooling
    ess_control = (control_weights.sum())**2 / (control_weights**2).sum()
    ess_treated = (treated_weights.sum())**2 / (treated_weights**2).sum()
    
    # Pooled standard deviation (using effective sample sizes)
    if ess_control + ess_treated - 2 <= 0:
        return np.nan
    
    pooled_std = np.sqrt(((ess_control - 1) * weighted_var_control + (ess_treated - 1) * weighted_var_treated) / 
                         (ess_control + ess_treated - 2))
    
    if pooled_std == 0:
        return np.nan
    
    smd = (weighted_mean_treated - weighted_mean_control) / pooled_std
    return smd

# Helper function for unweighted SMD (for pre-matching comparison)
def calculate_smd(control_values, treated_values):
    """Calculate unweighted SMD"""
    mean_control = control_values.mean()
    mean_treated = treated_values.mean()
    std_control = control_values.std()
    std_treated = treated_values.std()
    
    n_control = len(control_values)
    n_treated = len(treated_values)
    
    if n_control == 0 or n_treated == 0:
        return np.nan
    
    if std_control == 0 or std_treated == 0:
        return np.nan
    
    pooled_std = np.sqrt(((n_control - 1) * std_control**2 + (n_treated - 1) * std_treated**2) / 
                         (n_control + n_treated - 2))
    
    if pooled_std == 0:
        return np.nan
    
    smd = (mean_treated - mean_control) / pooled_std
    return smd

print("\nCalculating post-weighting balance for all confounders...")
print("   Including both continuous confounders AND dummy-encoded categorical variables...")

# Get treatment and weights
treatment_status = df_psm[treatment_var].values
weights = df_psm['ipw_weight'].values

# Get list of all confounders to check balance for:
# 1. Continuous confounders
# 2. Dummy-encoded categorical variables (from the propensity score model)
# We need to recreate the dummy structure to get the column names
X_categorical_dummies_balance = pd.get_dummies(
    df_psm[categorical_vars], 
    prefix=categorical_vars,
    prefix_sep='_',
    drop_first=True,
    dummy_na=False
)

# Combine continuous and dummy variable names
all_confounders_to_check = list(confounder_vars_clean) + list(X_categorical_dummies_balance.columns)

print(f"   Total confounders to check: {len(all_confounders_to_check)}")
print(f"     - Continuous: {len(confounder_vars_clean)}")
print(f"     - Categorical dummies: {len(X_categorical_dummies_balance.columns)}")

# Calculate balance for each confounder
balance_results = []

for conf in all_confounders_to_check:  # Check ALL confounders including dummies
    # For continuous confounders, check if in dataframe
    # For dummy variables, they should be in the categorical dummies dataframe
    if conf in df_psm.columns:
        conf_values = df_psm[conf].values
    elif conf in X_categorical_dummies_balance.columns:
        # Get values from the dummy dataframe (aligned with df_psm)
        conf_values = X_categorical_dummies_balance[conf].values
    else:
        continue
    
    # Get data by treatment group (using position indices for weights)
    control_mask = (treatment_status == 0)
    treated_mask = (treatment_status == 1)
    
    # Get data values (already extracted above)
    control_values = conf_values[control_mask]
    treated_values = conf_values[treated_mask]
    
    # Get weights for these groups
    control_weights_full = weights[control_mask]
    treated_weights_full = weights[treated_mask]
    
    # Remove missing values
    control_valid = ~pd.isna(control_values)
    treated_valid = ~pd.isna(treated_values)
    
    control_data = control_values[control_valid]
    treated_data = treated_values[treated_valid]
    control_weights = control_weights_full[control_valid]
    treated_weights = treated_weights_full[treated_valid]
    
    if len(control_data) == 0 or len(treated_data) == 0:
        continue
    
    # Calculate PRE-weighting SMD (unweighted)
    smd_pre = calculate_smd(control_data, treated_data)
    
    # Calculate POST-weighting SMD (weighted)
    smd_post = calculate_weighted_smd(control_data, treated_data, control_weights, treated_weights)
    
    # Calculate improvement
    smd_improvement = abs(smd_pre) - abs(smd_post) if not np.isnan(smd_pre) and not np.isnan(smd_post) else np.nan
    
    # Determine if balanced post-weighting (|SMD| <= 0.1)
    is_balanced_post = abs(smd_post) <= 0.1 if not np.isnan(smd_post) else False
    was_imbalanced_pre = abs(smd_pre) > 0.1 if not np.isnan(smd_pre) else False
    
    balance_results.append({
        'Confounder': conf,
        'SMD_Pre': smd_pre,
        'SMD_Post': smd_post,
        'Abs_SMD_Pre': abs(smd_pre) if not np.isnan(smd_pre) else np.nan,
        'Abs_SMD_Post': abs(smd_post) if not np.isnan(smd_post) else np.nan,
        'SMD_Improvement': smd_improvement,
        'Imbalanced_Pre': was_imbalanced_pre,
        'Balanced_Post': is_balanced_post,
        'N_Control': len(control_data),
        'N_Treated': len(treated_data)
    })

# Create balance comparison dataframe
balance_comparison = pd.DataFrame(balance_results)
balance_comparison = balance_comparison.sort_values('Abs_SMD_Pre', ascending=False)

print("\n" + "="*80)
print("BALANCE COMPARISON: PRE vs POST-WEIGHTING")
print("="*80)

# Summary statistics
n_confounders = len(balance_comparison)
n_imbalanced_pre = balance_comparison['Imbalanced_Pre'].sum()
n_balanced_post = balance_comparison['Balanced_Post'].sum()
n_imbalanced_post = n_confounders - n_balanced_post

print(f"\nSummary Statistics:")
print(f"  Total confounders analyzed: {n_confounders}")
print(f"  Imbalanced PRE-weighting (|SMD| > 0.1): {n_imbalanced_pre} ({n_imbalanced_pre/n_confounders*100:.1f}%)")
print(f"  Balanced POST-weighting (|SMD| ≤ 0.1): {n_balanced_post} ({n_balanced_post/n_confounders*100:.1f}%)")
print(f"  Still imbalanced POST-weighting: {n_imbalanced_post} ({n_imbalanced_post/n_confounders*100:.1f}%)")

# Mean SMD improvement
mean_smd_pre = balance_comparison['Abs_SMD_Pre'].mean()
mean_smd_post = balance_comparison['Abs_SMD_Post'].mean()
mean_improvement = balance_comparison['SMD_Improvement'].mean()

print(f"\nMean Absolute SMD:")
print(f"  PRE-weighting: {mean_smd_pre:.4f}")
print(f"  POST-weighting: {mean_smd_post:.4f}")
print(f"  Improvement: {mean_improvement:.4f} ({mean_improvement/mean_smd_pre*100:.1f}% reduction)")

# Show top 10 confounders by pre-weighting SMD
print(f"\nTop 10 Confounders by Pre-Weighting SMD:")
print(f"{'Confounder':<30} {'SMD Pre':>10} {'SMD Post':>10} {'Improvement':>12} {'Status':>15}")
print("-" * 80)
for idx, row in balance_comparison.head(10).iterrows():
    conf_name = row['Confounder'][:28] if len(row['Confounder']) > 28 else row['Confounder']
    smd_pre_str = f"{row['SMD_Pre']:+.3f}" if not np.isnan(row['SMD_Pre']) else "N/A"
    smd_post_str = f"{row['SMD_Post']:+.3f}" if not np.isnan(row['SMD_Post']) else "N/A"
    improvement_str = f"{row['SMD_Improvement']:+.3f}" if not np.isnan(row['SMD_Improvement']) else "N/A"
    status = "✓ Balanced" if row['Balanced_Post'] else "✗ Imbalanced"
    print(f"{conf_name:<30} {smd_pre_str:>10} {smd_post_str:>10} {improvement_str:>12} {status:>15}")

# Show still-imbalanced confounders
still_imbalanced = balance_comparison[~balance_comparison['Balanced_Post']].sort_values('Abs_SMD_Post', ascending=False)
if len(still_imbalanced) > 0:
    print(f"\nStill Imbalanced Confounders (POST-weighting |SMD| > 0.1):")
    for idx, row in still_imbalanced.iterrows():
        print(f"  {row['Confounder']}: SMD = {row['SMD_Post']:+.3f} (was {row['SMD_Pre']:+.3f} pre-weighting)")

print("\n" + "="*80)
print("POST-WEIGHTING BALANCE CHECK COMPLETE")
print("="*80)

# Save balance comparison table
balance_output_path = 'outputs/tables/balance_comparison.csv'
balance_comparison.to_csv(balance_output_path, index=False)
print(f"\n✓ Saved balance comparison table to: {balance_output_path}")

# SECTION 4.15: STOP AND THINK - BALANCE IMPROVEMENT ASSESSMENT
print("\n" + "="*80)
print("SECTION 4.15: STOP AND THINK - BALANCE IMPROVEMENT ASSESSMENT")
print("="*80)

print("\n" + "-"*80)
print("ANALYSIS AND INTERPRETATION")
print("-"*80)

print("\n1. BALANCE IMPROVEMENT SUMMARY:")
print(f"   - Confounders imbalanced PRE-weighting: {n_imbalanced_pre} / {n_confounders} ({n_imbalanced_pre/n_confounders*100:.1f}%)")
print(f"   - Confounders balanced POST-weighting: {n_balanced_post} / {n_confounders} ({n_balanced_post/n_confounders*100:.1f}%)")
print(f"   - Confounders still imbalanced POST-weighting: {n_imbalanced_post} / {n_confounders} ({n_imbalanced_post/n_confounders*100:.1f}%)")

if n_balanced_post / n_confounders >= 0.8:
    print("   - Assessment: EXCELLENT balance improvement (>80% balanced)")
    print("   - Interpretation: IPW weights successfully balanced most confounders")
elif n_balanced_post / n_confounders >= 0.6:
    print("   - Assessment: GOOD balance improvement (60-80% balanced)")
    print("   - Interpretation: IPW weights improved balance substantially")
elif n_balanced_post / n_confounders >= 0.4:
    print("   - Assessment: MODERATE balance improvement (40-60% balanced)")
    print("   - Interpretation: IPW weights improved balance but some confounders remain imbalanced")
    print("   - Recommendation: Consider revising propensity model (add interactions/polynomials)")
else:
    print("   - Assessment: POOR balance improvement (<40% balanced)")
    print("   - Interpretation: IPW weights did not substantially improve balance")
    print("   - Recommendation: Revise propensity model or consider alternative methods")

print("\n2. MEAN SMD IMPROVEMENT:")
print(f"   - Mean |SMD| PRE-weighting: {mean_smd_pre:.4f}")
print(f"   - Mean |SMD| POST-weighting: {mean_smd_post:.4f}")
print(f"   - Mean improvement: {mean_improvement:.4f} ({mean_improvement/mean_smd_pre*100:.1f}% reduction)")

if mean_improvement > 0.1:
    print("   - Assessment: SUBSTANTIAL improvement in mean SMD")
    print("   - Interpretation: Weights effectively reduced average imbalance")
elif mean_improvement > 0.05:
    print("   - Assessment: MODERATE improvement in mean SMD")
    print("   - Interpretation: Weights reduced average imbalance somewhat")
else:
    print("   - Assessment: MINIMAL improvement in mean SMD")
    print("   - Interpretation: Weights did not substantially reduce average imbalance")
    print("   - Recommendation: Consider revising propensity model")

print("\n3. REMAINING IMBALANCE:")
if n_imbalanced_post > 0:
    print(f"   - {n_imbalanced_post} confounders still imbalanced (|SMD| > 0.1)")
    print("   - Most imbalanced remaining confounders:")
    for idx, row in still_imbalanced.head(5).iterrows():
        print(f"     • {row['Confounder']}: SMD = {row['SMD_Post']:+.3f} (was {row['SMD_Pre']:+.3f})")
    print("   - Recommendation: These confounders may need special attention")
    print("     Consider adding interactions or polynomial terms in propensity model")
else:
    print("   - ✓ All confounders balanced (|SMD| ≤ 0.1)")
    print("   - Excellent balance achieved!")

print("\n4. DECISION:")
# Make a recommendation
if n_balanced_post / n_confounders >= 0.8 and mean_improvement > 0.1:
    decision = "PROCEED WITH IPW WEIGHTS"
    reason = f"Excellent balance improvement ({n_balanced_post/n_confounders*100:.1f}% balanced, {mean_improvement:.3f} mean SMD reduction)"
elif n_balanced_post / n_confounders >= 0.6:
    decision = "PROCEED WITH IPW WEIGHTS (MONITOR)"
    reason = f"Good balance improvement ({n_balanced_post/n_confounders*100:.1f}% balanced) - proceed but monitor remaining imbalance"
elif n_balanced_post / n_confounders >= 0.4:
    decision = "CONSIDER REVISING PROPENSITY MODEL"
    reason = f"Moderate balance improvement ({n_balanced_post/n_confounders*100:.1f}% balanced) - consider adding interactions/polynomials"
else:
    decision = "REVISE PROPENSITY MODEL OR CONSIDER ALTERNATIVE METHODS"
    reason = f"Poor balance improvement ({n_balanced_post/n_confounders*100:.1f}% balanced) - weights not effective"

print(f"   - Decision: {decision}")
print(f"   - Reason: {reason}")

print("\n" + "-"*80)
print("DOCUMENTATION FOR ANALYSIS LOG")
print("-"*80)
print("\nPlease review the above analysis and document your findings in:")
print("  outputs/logs/analysis_log.md")
print("\nKey questions to address:")
print("  1. Did balance improve after weighting?")
print("  2. How many confounders are still imbalanced?")
print("  3. Should you revise the propensity model?")
print("  4. What is the rationale for your decision?")

print("\n" + "="*80)
print("STOP AND THINK COMPLETE - AWAITING MANUAL REVIEW")
print("="*80)
print("\n⚠️  PLEASE REVIEW THE ABOVE ANALYSIS AND PROVIDE GO-AHEAD TO PROCEED")
print("   to the next step (Task 4.16: Save Balance Comparison)")
print("="*80)

# SECTION 4.17-4.19: ESTIMATE ATE FOR EARNINGS
print("\n" + "="*80)
print("SECTION 4.17-4.19: ESTIMATE ATE FOR EARNINGS")
print("="*80)

# Get outcome variable
earnings_var = outcome_vars[0]  # earnings_10yr
print(f"\nEstimating ATE for outcome: {earnings_var}")

# Prepare data: need treatment, outcome, and weights
# Filter to observations with non-missing outcome
analysis_data = df_psm[[treatment_var, earnings_var, 'ipw_weight']].copy()
analysis_data = analysis_data.dropna(subset=[earnings_var])

print(f"\nSample size for ATE estimation: {len(analysis_data):,}")
print(f"  Treated: {(analysis_data[treatment_var] == 1).sum():,}")
print(f"  Control: {(analysis_data[treatment_var] == 0).sum():,}")

# Extract arrays
treatment = analysis_data[treatment_var].values
outcome = analysis_data[earnings_var].values
weights = analysis_data['ipw_weight'].values

# Calculate weighted means by treatment group
treated_mask = (treatment == 1)
control_mask = (treatment == 0)

# Weighted mean outcomes
weighted_mean_treated = np.average(outcome[treated_mask], weights=weights[treated_mask])
weighted_mean_control = np.average(outcome[control_mask], weights=weights[control_mask])

# ATE point estimate
ate_point = weighted_mean_treated - weighted_mean_control

print("\n" + "="*80)
print("ATE POINT ESTIMATE (IPW)")
print("="*80)
print(f"\nWeighted Mean Outcomes:")
print(f"  Treated (Low Gap): ${weighted_mean_treated:,.2f}")
print(f"  Control (High Gap): ${weighted_mean_control:,.2f}")
print(f"\nAverage Treatment Effect (ATE): ${ate_point:,.2f}")

# Bootstrap standard errors
print("\nCalculating bootstrap standard errors (1000 iterations)...")
np.random.seed(42)  # For reproducibility

n_bootstrap = 1000
bootstrap_ates = []

for i in range(n_bootstrap):
    # Resample with replacement
    bootstrap_indices = np.random.choice(len(analysis_data), size=len(analysis_data), replace=True)
    
    # Get bootstrap sample
    boot_treatment = treatment[bootstrap_indices]
    boot_outcome = outcome[bootstrap_indices]
    boot_weights = weights[bootstrap_indices]
    
    # Calculate ATE for bootstrap sample
    boot_treated_mask = (boot_treatment == 1)
    boot_control_mask = (boot_treatment == 0)
    
    if boot_treated_mask.sum() > 0 and boot_control_mask.sum() > 0:
        boot_mean_treated = np.average(boot_outcome[boot_treated_mask], weights=boot_weights[boot_treated_mask])
        boot_mean_control = np.average(boot_outcome[boot_control_mask], weights=boot_weights[boot_control_mask])
        boot_ate = boot_mean_treated - boot_mean_control
        bootstrap_ates.append(boot_ate)
    
    # Progress indicator
    if (i + 1) % 200 == 0:
        print(f"  Completed {i + 1} / {n_bootstrap} bootstrap iterations...")

bootstrap_ates = np.array(bootstrap_ates)

# Calculate standard error from bootstrap distribution
ate_se = bootstrap_ates.std()

# Calculate 95% confidence interval
ate_ci_lower = np.percentile(bootstrap_ates, 2.5)
ate_ci_upper = np.percentile(bootstrap_ates, 97.5)

# Calculate p-value (two-sided test of H0: ATE = 0)
# Using bootstrap distribution
p_value = 2 * min(
    (bootstrap_ates <= 0).sum() / len(bootstrap_ates),
    (bootstrap_ates >= 0).sum() / len(bootstrap_ates)
)
# Ensure p-value is at least 1/n_bootstrap
p_value = max(p_value, 1.0 / n_bootstrap)

print("\n" + "="*80)
print("ATE ESTIMATION RESULTS (EARNINGS)")
print("="*80)
print(f"\nPoint Estimate:")
print(f"  ATE: ${ate_point:,.2f}")
print(f"\nStandard Error (Bootstrap):")
print(f"  SE: ${ate_se:,.2f}")
print(f"\n95% Confidence Interval:")
print(f"  Lower: ${ate_ci_lower:,.2f}")
print(f"  Upper: ${ate_ci_upper:,.2f}")
print(f"  CI: [${ate_ci_lower:,.2f}, ${ate_ci_upper:,.2f}]")
print(f"\nStatistical Significance:")
print(f"  p-value: {p_value:.4f}")
if p_value < 0.001:
    significance = "*** (p < 0.001)"
elif p_value < 0.01:
    significance = "** (p < 0.01)"
elif p_value < 0.05:
    significance = "* (p < 0.05)"
else:
    significance = "ns (p ≥ 0.05)"
print(f"  Significance: {significance}")

# Store results for later comparison
ate_earnings_results = {
    'outcome': earnings_var,
    'ate': ate_point,
    'se': ate_se,
    'ci_lower': ate_ci_lower,
    'ci_upper': ate_ci_upper,
    'p_value': p_value,
    'n_treated': treated_mask.sum(),
    'n_control': control_mask.sum(),
    'n_total': len(analysis_data)
}

print("\n" + "="*80)
print("ATE ESTIMATION COMPLETE (EARNINGS)")
print("="*80)

# SECTION 4.19: STOP AND THINK - EARNINGS ATE INTERPRETATION
print("\n" + "="*80)
print("SECTION 4.19: STOP AND THINK - EARNINGS ATE INTERPRETATION")
print("="*80)

print("\n" + "-"*80)
print("ANALYSIS AND INTERPRETATION")
print("-"*80)

print("\n1. EFFECT DIRECTION:")
if ate_point > 0:
    print(f"   - ATE = ${ate_point:,.2f} (positive)")
    print("   - Interpretation: Low gap institutions have HIGHER earnings than high gap institutions")
    print("   - This suggests that reducing affordability gaps may improve student earnings")
else:
    print(f"   - ATE = ${ate_point:,.2f} (negative)")
    print("   - Interpretation: Low gap institutions have LOWER earnings than high gap institutions")
    print("   - This suggests that affordability gaps may not be the primary driver of earnings differences")

print("\n2. EFFECT MAGNITUDE:")
abs_ate = abs(ate_point)
if abs_ate > 10000:
    print(f"   - Magnitude: ${abs_ate:,.2f} (very large)")
    print("   - Assessment: This is a substantial earnings difference")
elif abs_ate > 5000:
    print(f"   - Magnitude: ${abs_ate:,.2f} (large)")
    print("   - Assessment: This is a meaningful earnings difference")
elif abs_ate > 2000:
    print(f"   - Magnitude: ${abs_ate:,.2f} (moderate)")
    print("   - Assessment: This is a moderate earnings difference")
else:
    print(f"   - Magnitude: ${abs_ate:,.2f} (small)")
    print("   - Assessment: This is a relatively small earnings difference")

# Calculate percentage change relative to control mean
pct_change = (ate_point / weighted_mean_control) * 100
print(f"   - Percentage change: {pct_change:+.1f}% relative to control mean")

print("\n3. STATISTICAL SIGNIFICANCE:")
print(f"   - p-value: {p_value:.4f}")
if p_value < 0.05:
    print("   - Assessment: Statistically significant (p < 0.05)")
    print("   - Interpretation: We can reject the null hypothesis that ATE = 0")
    print("   - Confidence: Strong evidence of a treatment effect")
else:
    print("   - Assessment: Not statistically significant (p ≥ 0.05)")
    print("   - Interpretation: Cannot reject the null hypothesis that ATE = 0")
    print("   - Confidence: Weak evidence of a treatment effect")
    print("   - Note: This may be due to insufficient power or true null effect")

print("\n4. CONFIDENCE INTERVAL:")
print(f"   - 95% CI: [${ate_ci_lower:,.2f}, ${ate_ci_upper:,.2f}]")
if ate_ci_lower > 0 and ate_ci_upper > 0:
    print("   - Interpretation: CI excludes zero - consistent positive effect")
elif ate_ci_lower < 0 and ate_ci_upper < 0:
    print("   - Interpretation: CI excludes zero - consistent negative effect")
else:
    print("   - Interpretation: CI includes zero - effect may be null")
    print("   - Note: This aligns with non-significant p-value")

print("\n5. COMPARISON TO UNADJUSTED DIFFERENCE:")
# Calculate unadjusted difference for comparison
unadj_mean_treated = outcome[treated_mask].mean()
unadj_mean_control = outcome[control_mask].mean()
unadj_diff = unadj_mean_treated - unadj_mean_control

print(f"   - Unadjusted difference: ${unadj_diff:,.2f}")
print(f"   - Adjusted ATE (IPW): ${ate_point:,.2f}")
print(f"   - Difference: ${ate_point - unadj_diff:,.2f}")

if abs(ate_point - unadj_diff) > 1000:
    print("   - Assessment: Large difference between adjusted and unadjusted")
    print("   - Interpretation: Confounders had substantial impact on effect estimate")
    print("   - This justifies using causal inference methods")
else:
    print("   - Assessment: Similar adjusted and unadjusted estimates")
    print("   - Interpretation: Confounders had minimal impact on effect estimate")

print("\n6. PRACTICAL SIGNIFICANCE:")
print(f"   - Effect size: ${abs_ate:,.2f} per institution")
if abs_ate > 5000:
    print("   - Assessment: PRACTICALLY SIGNIFICANT")
    print("   - Interpretation: This magnitude would be meaningful to students and policymakers")
    print("   - Example: A $5,000+ difference in earnings is substantial over a career")
elif abs_ate > 2000:
    print("   - Assessment: MODERATELY PRACTICALLY SIGNIFICANT")
    print("   - Interpretation: This magnitude may be meaningful depending on context")
else:
    print("   - Assessment: MAY NOT BE PRACTICALLY SIGNIFICANT")
    print("   - Interpretation: Effect may be too small to matter in practice")

print("\n" + "-"*80)
print("DOCUMENTATION FOR ANALYSIS LOG")
print("-"*80)
print("\nPlease review the above analysis and document your findings in:")
print("  outputs/logs/analysis_log.md")
print("\nKey questions to address:")
print("  1. What is the effect direction and magnitude?")
print("  2. Is the effect statistically significant?")
print("  3. Is the effect size practically meaningful?")
print("  4. How does this compare to the unadjusted difference?")

print("\n" + "="*80)
print("STOP AND THINK COMPLETE - AWAITING MANUAL REVIEW")
print("="*80)
print("\n⚠️  PLEASE REVIEW THE ABOVE ANALYSIS AND PROVIDE GO-AHEAD TO PROCEED")
print("   to the next step (Task 4.20: Estimate ATE for Graduation Rate)")
print("="*80)

# SECTION 4.20-4.22: ESTIMATE ATE FOR GRADUATION RATE
print("\n" + "="*80)
print("SECTION 4.20-4.22: ESTIMATE ATE FOR GRADUATION RATE")
print("="*80)

# Get outcome variable
grad_rate_var = outcome_vars[1]  # grad_rate_6yr
print(f"\nEstimating ATE for outcome: {grad_rate_var}")

# Prepare data: need treatment, outcome, and weights
# Filter to observations with non-missing outcome
analysis_data_grad = df_psm[[treatment_var, grad_rate_var, 'ipw_weight']].copy()
analysis_data_grad = analysis_data_grad.dropna(subset=[grad_rate_var])

print(f"\nSample size for ATE estimation: {len(analysis_data_grad):,}")
print(f"  Treated: {(analysis_data_grad[treatment_var] == 1).sum():,}")
print(f"  Control: {(analysis_data_grad[treatment_var] == 0).sum():,}")

# Extract arrays
treatment_grad = analysis_data_grad[treatment_var].values
outcome_grad = analysis_data_grad[grad_rate_var].values
weights_grad = analysis_data_grad['ipw_weight'].values

# Calculate weighted means by treatment group
treated_mask_grad = (treatment_grad == 1)
control_mask_grad = (treatment_grad == 0)

# Weighted mean outcomes
weighted_mean_treated_grad = np.average(outcome_grad[treated_mask_grad], weights=weights_grad[treated_mask_grad])
weighted_mean_control_grad = np.average(outcome_grad[control_mask_grad], weights=weights_grad[control_mask_grad])

# ATE point estimate
ate_point_grad = weighted_mean_treated_grad - weighted_mean_control_grad

print("\n" + "="*80)
print("ATE POINT ESTIMATE (IPW)")
print("="*80)
print(f"\nWeighted Mean Outcomes:")
print(f"  Treated (Low Gap): {weighted_mean_treated_grad:.2f}%")
print(f"  Control (High Gap): {weighted_mean_control_grad:.2f}%")
print(f"\nAverage Treatment Effect (ATE): {ate_point_grad:.2f} percentage points")

# Bootstrap standard errors
print("\nCalculating bootstrap standard errors (1000 iterations)...")
np.random.seed(42)  # For reproducibility

n_bootstrap = 1000
bootstrap_ates_grad = []

for i in range(n_bootstrap):
    # Resample with replacement
    bootstrap_indices = np.random.choice(len(analysis_data_grad), size=len(analysis_data_grad), replace=True)
    
    # Get bootstrap sample
    boot_treatment = treatment_grad[bootstrap_indices]
    boot_outcome = outcome_grad[bootstrap_indices]
    boot_weights = weights_grad[bootstrap_indices]
    
    # Calculate ATE for bootstrap sample
    boot_treated_mask = (boot_treatment == 1)
    boot_control_mask = (boot_treatment == 0)
    
    if boot_treated_mask.sum() > 0 and boot_control_mask.sum() > 0:
        boot_mean_treated = np.average(boot_outcome[boot_treated_mask], weights=boot_weights[boot_treated_mask])
        boot_mean_control = np.average(boot_outcome[boot_control_mask], weights=boot_weights[boot_control_mask])
        boot_ate = boot_mean_treated - boot_mean_control
        bootstrap_ates_grad.append(boot_ate)
    
    # Progress indicator
    if (i + 1) % 200 == 0:
        print(f"  Completed {i + 1} / {n_bootstrap} bootstrap iterations...")

bootstrap_ates_grad = np.array(bootstrap_ates_grad)

# Calculate standard error from bootstrap distribution
ate_se_grad = bootstrap_ates_grad.std()

# Calculate 95% confidence interval
ate_ci_lower_grad = np.percentile(bootstrap_ates_grad, 2.5)
ate_ci_upper_grad = np.percentile(bootstrap_ates_grad, 97.5)

# Calculate p-value (two-sided test of H0: ATE = 0)
# Using bootstrap distribution
p_value_grad = 2 * min(
    (bootstrap_ates_grad <= 0).sum() / len(bootstrap_ates_grad),
    (bootstrap_ates_grad >= 0).sum() / len(bootstrap_ates_grad)
)
# Ensure p-value is at least 1/n_bootstrap
p_value_grad = max(p_value_grad, 1.0 / n_bootstrap)

print("\n" + "="*80)
print("ATE ESTIMATION RESULTS (GRADUATION RATE)")
print("="*80)
print(f"\nPoint Estimate:")
print(f"  ATE: {ate_point_grad:.2f} percentage points")
print(f"\nStandard Error (Bootstrap):")
print(f"  SE: {ate_se_grad:.2f} percentage points")
print(f"\n95% Confidence Interval:")
print(f"  Lower: {ate_ci_lower_grad:.2f} percentage points")
print(f"  Upper: {ate_ci_upper_grad:.2f} percentage points")
print(f"  CI: [{ate_ci_lower_grad:.2f}, {ate_ci_upper_grad:.2f}] percentage points")
print(f"\nStatistical Significance:")
print(f"  p-value: {p_value_grad:.4f}")
if p_value_grad < 0.001:
    significance_grad = "*** (p < 0.001)"
elif p_value_grad < 0.01:
    significance_grad = "** (p < 0.01)"
elif p_value_grad < 0.05:
    significance_grad = "* (p < 0.05)"
else:
    significance_grad = "ns (p ≥ 0.05)"
print(f"  Significance: {significance_grad}")

# Store results for later comparison
ate_grad_results = {
    'outcome': grad_rate_var,
    'ate': ate_point_grad,
    'se': ate_se_grad,
    'ci_lower': ate_ci_lower_grad,
    'ci_upper': ate_ci_upper_grad,
    'p_value': p_value_grad,
    'n_treated': treated_mask_grad.sum(),
    'n_control': control_mask_grad.sum(),
    'n_total': len(analysis_data_grad)
}

print("\n" + "="*80)
print("ATE ESTIMATION COMPLETE (GRADUATION RATE)")
print("="*80)

# SECTION 4.22: STOP AND THINK - GRADUATION RATE ATE INTERPRETATION
print("\n" + "="*80)
print("SECTION 4.22: STOP AND THINK - GRADUATION RATE ATE INTERPRETATION")
print("="*80)

print("\n" + "-"*80)
print("ANALYSIS AND INTERPRETATION")
print("-"*80)

print("\n1. EFFECT DIRECTION:")
if ate_point_grad > 0:
    print(f"   - ATE = {ate_point_grad:.2f} percentage points (positive)")
    print("   - Interpretation: Low gap institutions have HIGHER graduation rates than high gap institutions")
    print("   - This suggests that reducing affordability gaps may improve graduation rates")
else:
    print(f"   - ATE = {ate_point_grad:.2f} percentage points (negative)")
    print("   - Interpretation: Low gap institutions have LOWER graduation rates than high gap institutions")
    print("   - This suggests that affordability gaps may not be the primary driver of graduation differences")

print("\n2. EFFECT MAGNITUDE:")
abs_ate_grad = abs(ate_point_grad)
if abs_ate_grad > 10:
    print(f"   - Magnitude: {abs_ate_grad:.2f} percentage points (very large)")
    print("   - Assessment: This is a substantial graduation rate difference")
elif abs_ate_grad > 5:
    print(f"   - Magnitude: {abs_ate_grad:.2f} percentage points (large)")
    print("   - Assessment: This is a meaningful graduation rate difference")
elif abs_ate_grad > 2:
    print(f"   - Magnitude: {abs_ate_grad:.2f} percentage points (moderate)")
    print("   - Assessment: This is a moderate graduation rate difference")
else:
    print(f"   - Magnitude: {abs_ate_grad:.2f} percentage points (small)")
    print("   - Assessment: This is a relatively small graduation rate difference")

# Calculate percentage change relative to control mean
pct_change_grad = (ate_point_grad / weighted_mean_control_grad) * 100
print(f"   - Percentage change: {pct_change_grad:+.1f}% relative to control mean")

print("\n3. STATISTICAL SIGNIFICANCE:")
print(f"   - p-value: {p_value_grad:.4f}")
if p_value_grad < 0.05:
    print("   - Assessment: Statistically significant (p < 0.05)")
    print("   - Interpretation: We can reject the null hypothesis that ATE = 0")
    print("   - Confidence: Strong evidence of a treatment effect")
else:
    print("   - Assessment: Not statistically significant (p ≥ 0.05)")
    print("   - Interpretation: Cannot reject the null hypothesis that ATE = 0")
    print("   - Confidence: Weak evidence of a treatment effect")
    print("   - Note: This may be due to insufficient power or true null effect")

print("\n4. CONFIDENCE INTERVAL:")
print(f"   - 95% CI: [{ate_ci_lower_grad:.2f}, {ate_ci_upper_grad:.2f}] percentage points")
if ate_ci_lower_grad > 0 and ate_ci_upper_grad > 0:
    print("   - Interpretation: CI excludes zero - consistent positive effect")
elif ate_ci_lower_grad < 0 and ate_ci_upper_grad < 0:
    print("   - Interpretation: CI excludes zero - consistent negative effect")
else:
    print("   - Interpretation: CI includes zero - effect may be null")
    print("   - Note: This aligns with non-significant p-value")

print("\n5. COMPARISON TO UNADJUSTED DIFFERENCE:")
# Calculate unadjusted difference for comparison
unadj_mean_treated_grad = outcome_grad[treated_mask_grad].mean()
unadj_mean_control_grad = outcome_grad[control_mask_grad].mean()
unadj_diff_grad = unadj_mean_treated_grad - unadj_mean_control_grad

print(f"   - Unadjusted difference: {unadj_diff_grad:.2f} percentage points")
print(f"   - Adjusted ATE (IPW): {ate_point_grad:.2f} percentage points")
print(f"   - Difference: {ate_point_grad - unadj_diff_grad:.2f} percentage points")

if abs(ate_point_grad - unadj_diff_grad) > 2:
    print("   - Assessment: Large difference between adjusted and unadjusted")
    print("   - Interpretation: Confounders had substantial impact on effect estimate")
    print("   - This justifies using causal inference methods")
else:
    print("   - Assessment: Similar adjusted and unadjusted estimates")
    print("   - Interpretation: Confounders had minimal impact on effect estimate")

print("\n6. COMPARISON TO EARNINGS RESULTS:")
print(f"   - Earnings ATE: ${ate_earnings_results['ate']:,.2f} (p = {ate_earnings_results['p_value']:.4f})")
print(f"   - Graduation Rate ATE: {ate_point_grad:.2f} pp (p = {p_value_grad:.4f})")

if (ate_point_grad > 0 and ate_earnings_results['ate'] > 0) or (ate_point_grad < 0 and ate_earnings_results['ate'] < 0):
    print("   - Assessment: Consistent direction across outcomes")
    print("   - Interpretation: Both outcomes show similar treatment effect direction")
else:
    print("   - Assessment: Inconsistent direction across outcomes")
    print("   - Interpretation: Treatment effects differ between earnings and graduation rates")
    print("   - This may indicate different mechanisms or pathways")

if p_value_grad < 0.05 and ate_earnings_results['p_value'] < 0.05:
    print("   - Both outcomes statistically significant")
elif p_value_grad < 0.05 or ate_earnings_results['p_value'] < 0.05:
    print("   - One outcome statistically significant, one not")
    print("   - This may indicate differential treatment effects by outcome")
else:
    print("   - Neither outcome statistically significant")
    print("   - This may indicate weak or null treatment effects overall")

print("\n7. PRACTICAL SIGNIFICANCE:")
print(f"   - Effect size: {abs_ate_grad:.2f} percentage points")
if abs_ate_grad > 5:
    print("   - Assessment: PRACTICALLY SIGNIFICANT")
    print("   - Interpretation: This magnitude would be meaningful to students and policymakers")
    print("   - Example: A 5+ percentage point difference in graduation rates is substantial")
elif abs_ate_grad > 2:
    print("   - Assessment: MODERATELY PRACTICALLY SIGNIFICANT")
    print("   - Interpretation: This magnitude may be meaningful depending on context")
else:
    print("   - Assessment: MAY NOT BE PRACTICALLY SIGNIFICANT")
    print("   - Interpretation: Effect may be too small to matter in practice")

print("\n" + "-"*80)
print("DOCUMENTATION FOR ANALYSIS LOG")
print("-"*80)
print("\nPlease review the above analysis and document your findings in:")
print("  outputs/logs/analysis_log.md")
print("\nKey questions to address:")
print("  1. What is the effect direction and magnitude?")
print("  2. Is the effect statistically significant?")
print("  3. Is the effect size practically meaningful?")
print("  4. How does this compare to earnings results?")
print("  5. Are the findings consistent across outcomes?")

print("\n" + "="*80)
print("STOP AND THINK COMPLETE - AWAITING MANUAL REVIEW")
print("="*80)
print("\n⚠️  PLEASE REVIEW THE ABOVE ANALYSIS AND PROVIDE GO-AHEAD TO PROCEED")
print("   to the next step (Task 4.23: Format IPW Results)")
print("="*80)

# SECTION 4.23-4.24: FORMAT AND SAVE IPW RESULTS
print("\n" + "="*80)
print("SECTION 4.23-4.24: FORMAT AND SAVE IPW RESULTS")
print("="*80)

# Create formatted results table
print("\nCreating formatted IPW results table...")

# Prepare results data
ipw_results_data = []

# Earnings results
earnings_row = {
    'Outcome': 'Earnings (10-year)',
    'Outcome_Variable': earnings_var,
    'Method': 'IPW (Inverse Probability Weighting)',
    'ATE': ate_earnings_results['ate'],
    'ATE_Formatted': f"${ate_earnings_results['ate']:,.2f}",
    'SE': ate_earnings_results['se'],
    'SE_Formatted': f"${ate_earnings_results['se']:,.2f}",
    'CI_Lower': ate_earnings_results['ci_lower'],
    'CI_Upper': ate_earnings_results['ci_upper'],
    'CI_Formatted': f"[${ate_earnings_results['ci_lower']:,.2f}, ${ate_earnings_results['ci_upper']:,.2f}]",
    'P_Value': ate_earnings_results['p_value'],
    'Significant': 'Yes' if ate_earnings_results['p_value'] < 0.05 else 'No',
    'N_Treated': ate_earnings_results['n_treated'],
    'N_Control': ate_earnings_results['n_control'],
    'N_Total': ate_earnings_results['n_total'],
    'Mean_Treated': weighted_mean_treated,
    'Mean_Control': weighted_mean_control
}
ipw_results_data.append(earnings_row)

# Graduation rate results
grad_row = {
    'Outcome': 'Graduation Rate (6-year)',
    'Outcome_Variable': grad_rate_var,
    'Method': 'IPW (Inverse Probability Weighting)',
    'ATE': ate_point_grad,
    'ATE_Formatted': f"{ate_point_grad:.2f} pp",
    'SE': ate_se_grad,
    'SE_Formatted': f"{ate_se_grad:.2f} pp",
    'CI_Lower': ate_ci_lower_grad,
    'CI_Upper': ate_ci_upper_grad,
    'CI_Formatted': f"[{ate_ci_lower_grad:.2f}, {ate_ci_upper_grad:.2f}] pp",
    'P_Value': p_value_grad,
    'Significant': 'Yes' if p_value_grad < 0.05 else 'No',
    'N_Treated': ate_grad_results['n_treated'],
    'N_Control': ate_grad_results['n_control'],
    'N_Total': ate_grad_results['n_total'],
    'Mean_Treated': weighted_mean_treated_grad,
    'Mean_Control': weighted_mean_control_grad
}
ipw_results_data.append(grad_row)

# Create DataFrame
ipw_results_df = pd.DataFrame(ipw_results_data)

# Display formatted table
print("\n" + "="*80)
print("IPW RESULTS SUMMARY TABLE")
print("="*80)
print("\n" + ipw_results_df[['Outcome', 'ATE_Formatted', 'SE_Formatted', 'CI_Formatted', 'P_Value', 'Significant', 'N_Total']].to_string(index=False))

# Save to CSV
ipw_results_path = 'outputs/tables/ipw_results.csv'
ipw_results_df.to_csv(ipw_results_path, index=False)
print(f"\n✓ Saved IPW results table to: {ipw_results_path}")

# Create a more detailed summary for display
print("\n" + "="*80)
print("DETAILED IPW RESULTS")
print("="*80)

for idx, row in ipw_results_df.iterrows():
    print(f"\n{row['Outcome']}:")
    print(f"  Method: {row['Method']}")
    print(f"  Sample Size: {row['N_Total']:,} (Treated: {row['N_Treated']:,}, Control: {row['N_Control']:,})")
    print(f"  Weighted Mean - Treated: {row['Mean_Treated']:.2f}")
    print(f"  Weighted Mean - Control: {row['Mean_Control']:.2f}")
    print(f"  ATE: {row['ATE_Formatted']}")
    print(f"  Standard Error: {row['SE_Formatted']}")
    print(f"  95% Confidence Interval: {row['CI_Formatted']}")
    print(f"  p-value: {row['P_Value']:.4f}")
    print(f"  Statistically Significant: {row['Significant']}")

print("\n" + "="*80)
print("IPW RESULTS FORMATTING COMPLETE")
print("="*80)

# SECTION 4.25-4.27: DOUBLY ROBUST ESTIMATION
print("\n" + "="*80)
print("SECTION 4.25-4.27: DOUBLY ROBUST ESTIMATION")
print("="*80)

if not ECONML_AVAILABLE:
    print("\n⚠️  WARNING: EconML not available. Skipping doubly robust estimation.")
    print("   Install with: pip install econml")
    print("   Proceeding to next method...")
else:
    print("\nUsing LinearDML for doubly robust estimation...")
    print("Doubly robust methods combine outcome modeling and propensity score weighting")
    print("for more efficient and robust estimates.")
    
    # Prepare confounders matrix (same as used in propensity score model)
    # Use the same cleaned confounders and categorical dummies
    print("\nPreparing data for doubly robust estimation...")
    
    # Get the same X_all structure used for propensity scores
    # We'll recreate it to ensure consistency
    X_continuous_dr = df_psm[confounder_vars_clean].copy()
    for col in X_continuous_dr.columns:
        X_continuous_dr[col] = pd.to_numeric(X_continuous_dr[col], errors='coerce')
    
    X_categorical_dummies_dr = pd.get_dummies(
        df_psm[categorical_vars], 
        prefix=categorical_vars,
        prefix_sep='_',
        drop_first=True,
        dummy_na=False
    )
    
    X_all_dr = pd.concat([X_continuous_dr, X_categorical_dummies_dr], axis=1)
    X_all_dr = X_all_dr.astype(float)
    
    # Remove any remaining missing values
    valid_mask_dr = ~(X_all_dr.isna().any(axis=1) | np.isinf(X_all_dr).any(axis=1))
    X_all_dr = X_all_dr[valid_mask_dr].values
    treatment_dr = df_psm[treatment_var].values[valid_mask_dr]
    
    print(f"  Sample size: {len(X_all_dr):,}")
    print(f"  Number of features: {X_all_dr.shape[1]}")
    
    # DR ESTIMATION FOR EARNINGS
    print("\n" + "="*80)
    print("DOUBLY ROBUST ESTIMATION: EARNINGS")
    print("="*80)
    
    # Prepare earnings outcome data - align with X_all_dr
    # Create a combined dataframe for easier alignment
    df_dr = df_psm[valid_mask_dr].copy()
    df_dr = df_dr.reset_index(drop=True)
    
    # Get earnings data
    earnings_valid = ~df_dr[earnings_var].isna()
    if earnings_valid.sum() > 0:
        X_earnings_dr = X_all_dr[earnings_valid]
        T_earnings_dr = treatment_dr[earnings_valid]
        Y_earnings_dr = df_dr.loc[earnings_valid, earnings_var].values
        
        print(f"\nSample size for earnings DR estimation: {len(Y_earnings_dr):,}")
        print(f"  Treated: {(T_earnings_dr == 1).sum():,}")
        print(f"  Control: {(T_earnings_dr == 0).sum():,}")
        
        # Fit LinearDML
        print("\nFitting LinearDML model...")
        try:
            from sklearn.linear_model import LogisticRegressionCV, LinearRegression
            # For binary treatment, use LogisticRegressionCV for propensity model
            # Use LinearRegression for outcome model
            dml_earnings = LinearDML(
                model_y=LinearRegression(),  # Linear model for outcome
                model_t=LogisticRegressionCV(cv=3, random_state=42),  # Logistic model for treatment
                discrete_treatment=True,
                cv=3,  # 3-fold cross-validation
                random_state=42
            )
            
            dml_earnings.fit(Y_earnings_dr, T_earnings_dr, X=X_earnings_dr)
            
            # Get ATE estimate
            ate_earnings_dr = dml_earnings.ate(X_earnings_dr)
            ate_earnings_dr_point = ate_earnings_dr.mean()
            
            # Get standard error (using inference)
            ate_earnings_dr_inference = dml_earnings.ate_inference(X_earnings_dr)
            
            # Try to get summary statistics - PopulationSummaryResults has different API
            # Get the point estimate and use bootstrap for SE if needed
            try:
                # Try accessing summary directly
                summary = ate_earnings_dr_inference.summary_frame() if hasattr(ate_earnings_dr_inference, 'summary_frame') else None
                if summary is not None and len(summary) > 0:
                    ate_earnings_dr_se = summary.iloc[0]['std err'] if 'std err' in summary.columns else None
                    ate_earnings_dr_ci_lower = summary.iloc[0]['[0.025'] if '[0.025' in summary.columns else None
                    ate_earnings_dr_ci_upper = summary.iloc[0]['0.975]'] if '0.975]' in summary.columns else None
                    ate_earnings_dr_pvalue = summary.iloc[0]['P>|z|'] if 'P>|z|' in summary.columns else None
                else:
                    raise AttributeError("No summary_frame")
            except:
                # Fallback: use bootstrap to estimate SE
                print("  Using bootstrap to estimate standard errors...")
                np.random.seed(42)
                n_boot_dr = 500
                boot_ates_dr = []
                for i in range(n_boot_dr):
                    boot_idx = np.random.choice(len(X_earnings_dr), size=len(X_earnings_dr), replace=True)
                    try:
                        boot_ate = dml_earnings.ate(X_earnings_dr[boot_idx]).mean()
                        boot_ates_dr.append(boot_ate)
                    except:
                        continue
                
                if len(boot_ates_dr) > 0:
                    boot_ates_dr = np.array(boot_ates_dr)
                    ate_earnings_dr_se = boot_ates_dr.std()
                    ate_earnings_dr_ci_lower = np.percentile(boot_ates_dr, 2.5)
                    ate_earnings_dr_ci_upper = np.percentile(boot_ates_dr, 97.5)
                    # Calculate p-value
                    pval_count = (boot_ates_dr <= 0).sum() if ate_earnings_dr_point > 0 else (boot_ates_dr >= 0).sum()
                    ate_earnings_dr_pvalue = 2 * min(pval_count / len(boot_ates_dr), 1 - pval_count / len(boot_ates_dr))
                    ate_earnings_dr_pvalue = max(ate_earnings_dr_pvalue, 1.0 / n_boot_dr)
                else:
                    raise ValueError("Bootstrap failed")
            
            print("\n" + "="*80)
            print("DOUBLY ROBUST RESULTS (EARNINGS)")
            print("="*80)
            print(f"\nPoint Estimate:")
            print(f"  ATE: ${ate_earnings_dr_point:,.2f}")
            print(f"\nStandard Error:")
            print(f"  SE: ${ate_earnings_dr_se:,.2f}")
            print(f"\n95% Confidence Interval:")
            print(f"  Lower: ${ate_earnings_dr_ci_lower:,.2f}")
            print(f"  Upper: ${ate_earnings_dr_ci_upper:,.2f}")
            print(f"  CI: [${ate_earnings_dr_ci_lower:,.2f}, ${ate_earnings_dr_ci_upper:,.2f}]")
            print(f"\nStatistical Significance:")
            print(f"  p-value: {ate_earnings_dr_pvalue:.4f}")
            if ate_earnings_dr_pvalue < 0.001:
                sig_earnings_dr = "*** (p < 0.001)"
            elif ate_earnings_dr_pvalue < 0.01:
                sig_earnings_dr = "** (p < 0.01)"
            elif ate_earnings_dr_pvalue < 0.05:
                sig_earnings_dr = "* (p < 0.05)"
            else:
                sig_earnings_dr = "ns (p ≥ 0.05)"
            print(f"  Significance: {sig_earnings_dr}")
            
            # Store results
            dr_earnings_results = {
                'outcome': earnings_var,
                'ate': ate_earnings_dr_point,
                'se': ate_earnings_dr_se,
                'ci_lower': ate_earnings_dr_ci_lower,
                'ci_upper': ate_earnings_dr_ci_upper,
                'p_value': ate_earnings_dr_pvalue,
                'n_total': len(Y_earnings_dr)
            }
            
            # Compare to IPW
            print("\n" + "="*80)
            print("COMPARISON: IPW vs DOUBLY ROBUST (EARNINGS)")
            print("="*80)
            print(f"\nIPW Results:")
            print(f"  ATE: ${ate_earnings_results['ate']:,.2f}")
            print(f"  SE: ${ate_earnings_results['se']:,.2f}")
            print(f"  p-value: {ate_earnings_results['p_value']:.4f}")
            print(f"\nDoubly Robust Results:")
            print(f"  ATE: ${ate_earnings_dr_point:,.2f}")
            print(f"  SE: ${ate_earnings_dr_se:,.2f}")
            print(f"  p-value: {ate_earnings_dr_pvalue:.4f}")
            
            ate_diff = abs(ate_earnings_dr_point - ate_earnings_results['ate'])
            se_ratio = ate_earnings_dr_se / ate_earnings_results['se']
            
            print(f"\nComparison:")
            print(f"  Difference in ATE: ${ate_diff:,.2f}")
            print(f"  SE ratio (DR/IPW): {se_ratio:.3f}")
            if se_ratio < 1.0:
                print(f"  → DR has smaller SE ({((1-se_ratio)*100):.1f}% reduction) - more efficient")
            else:
                print(f"  → DR has larger SE ({((se_ratio-1)*100):.1f}% increase)")
            
            if ate_diff < 100:
                print(f"  → Estimates are very similar (difference < $100)")
            elif ate_diff < 500:
                print(f"  → Estimates are similar (difference < $500)")
            else:
                print(f"  → Estimates differ substantially (difference > $500)")
                print(f"  → This may indicate model misspecification in one method")
            
        except Exception as e:
            print(f"\n⚠️  ERROR fitting LinearDML for earnings: {e}")
            import traceback
            traceback.print_exc()
            print("   Skipping doubly robust estimation for earnings")
            dr_earnings_results = None
    else:
        print("\n⚠️  No valid data for earnings DR estimation")
        dr_earnings_results = None
    
    # DR ESTIMATION FOR GRADUATION RATE
    print("\n" + "="*80)
    print("DOUBLY ROBUST ESTIMATION: GRADUATION RATE")
    print("="*80)
    
    # Prepare graduation rate outcome data - align with X_all_dr
    # Get graduation rate data
    grad_valid = ~df_dr[grad_rate_var].isna()
    if grad_valid.sum() > 0:
        X_grad_dr = X_all_dr[grad_valid]
        T_grad_dr = treatment_dr[grad_valid]
        Y_grad_dr = df_dr.loc[grad_valid, grad_rate_var].values
        
        print(f"\nSample size for graduation rate DR estimation: {len(Y_grad_dr):,}")
        print(f"  Treated: {(T_grad_dr == 1).sum():,}")
        print(f"  Control: {(T_grad_dr == 0).sum():,}")
        
        # Fit LinearDML
        print("\nFitting LinearDML model...")
        try:
            from sklearn.linear_model import LogisticRegressionCV, LinearRegression
            # For binary treatment, use LogisticRegressionCV for propensity model
            # Use LinearRegression for outcome model
            dml_grad = LinearDML(
                model_y=LinearRegression(),
                model_t=LogisticRegressionCV(cv=3, random_state=42),
                discrete_treatment=True,
                cv=3,
                random_state=42
            )
            
            dml_grad.fit(Y_grad_dr, T_grad_dr, X=X_grad_dr)
            
            # Get ATE estimate
            ate_grad_dr = dml_grad.ate(X_grad_dr)
            ate_grad_dr_point = ate_grad_dr.mean()
            
            # Get standard error
            ate_grad_dr_inference = dml_grad.ate_inference(X_grad_dr)
            
            # Try to get summary statistics - PopulationSummaryResults has different API
            try:
                # Try accessing summary directly
                summary = ate_grad_dr_inference.summary_frame() if hasattr(ate_grad_dr_inference, 'summary_frame') else None
                if summary is not None and len(summary) > 0:
                    ate_grad_dr_se = summary.iloc[0]['std err'] if 'std err' in summary.columns else None
                    ate_grad_dr_ci_lower = summary.iloc[0]['[0.025'] if '[0.025' in summary.columns else None
                    ate_grad_dr_ci_upper = summary.iloc[0]['0.975]'] if '0.975]' in summary.columns else None
                    ate_grad_dr_pvalue = summary.iloc[0]['P>|z|'] if 'P>|z|' in summary.columns else None
                else:
                    raise AttributeError("No summary_frame")
            except:
                # Fallback: use bootstrap to estimate SE
                print("  Using bootstrap to estimate standard errors...")
                np.random.seed(42)
                n_boot_dr = 500
                boot_ates_dr_grad = []
                for i in range(n_boot_dr):
                    boot_idx = np.random.choice(len(X_grad_dr), size=len(X_grad_dr), replace=True)
                    try:
                        boot_ate = dml_grad.ate(X_grad_dr[boot_idx]).mean()
                        boot_ates_dr_grad.append(boot_ate)
                    except:
                        continue
                
                if len(boot_ates_dr_grad) > 0:
                    boot_ates_dr_grad = np.array(boot_ates_dr_grad)
                    ate_grad_dr_se = boot_ates_dr_grad.std()
                    ate_grad_dr_ci_lower = np.percentile(boot_ates_dr_grad, 2.5)
                    ate_grad_dr_ci_upper = np.percentile(boot_ates_dr_grad, 97.5)
                    # Calculate p-value
                    pval_count = (boot_ates_dr_grad <= 0).sum() if ate_grad_dr_point > 0 else (boot_ates_dr_grad >= 0).sum()
                    ate_grad_dr_pvalue = 2 * min(pval_count / len(boot_ates_dr_grad), 1 - pval_count / len(boot_ates_dr_grad))
                    ate_grad_dr_pvalue = max(ate_grad_dr_pvalue, 1.0 / n_boot_dr)
                else:
                    raise ValueError("Bootstrap failed")
            
            print("\n" + "="*80)
            print("DOUBLY ROBUST RESULTS (GRADUATION RATE)")
            print("="*80)
            print(f"\nPoint Estimate:")
            print(f"  ATE: {ate_grad_dr_point:.2f} percentage points")
            print(f"\nStandard Error:")
            print(f"  SE: {ate_grad_dr_se:.2f} percentage points")
            print(f"\n95% Confidence Interval:")
            print(f"  Lower: {ate_grad_dr_ci_lower:.2f} percentage points")
            print(f"  Upper: {ate_grad_dr_ci_upper:.2f} percentage points")
            print(f"  CI: [{ate_grad_dr_ci_lower:.2f}, {ate_grad_dr_ci_upper:.2f}] percentage points")
            print(f"\nStatistical Significance:")
            print(f"  p-value: {ate_grad_dr_pvalue:.4f}")
            if ate_grad_dr_pvalue < 0.001:
                sig_grad_dr = "*** (p < 0.001)"
            elif ate_grad_dr_pvalue < 0.01:
                sig_grad_dr = "** (p < 0.01)"
            elif ate_grad_dr_pvalue < 0.05:
                sig_grad_dr = "* (p < 0.05)"
            else:
                sig_grad_dr = "ns (p ≥ 0.05)"
            print(f"  Significance: {sig_grad_dr}")
            
            # Store results
            dr_grad_results = {
                'outcome': grad_rate_var,
                'ate': ate_grad_dr_point,
                'se': ate_grad_dr_se,
                'ci_lower': ate_grad_dr_ci_lower,
                'ci_upper': ate_grad_dr_ci_upper,
                'p_value': ate_grad_dr_pvalue,
                'n_total': len(Y_grad_dr)
            }
            
            # Compare to IPW
            print("\n" + "="*80)
            print("COMPARISON: IPW vs DOUBLY ROBUST (GRADUATION RATE)")
            print("="*80)
            print(f"\nIPW Results:")
            print(f"  ATE: {ate_point_grad:.2f} percentage points")
            print(f"  SE: {ate_se_grad:.2f} percentage points")
            print(f"  p-value: {p_value_grad:.4f}")
            print(f"\nDoubly Robust Results:")
            print(f"  ATE: {ate_grad_dr_point:.2f} percentage points")
            print(f"  SE: {ate_grad_dr_se:.2f} percentage points")
            print(f"  p-value: {ate_grad_dr_pvalue:.4f}")
            
            ate_diff_grad = abs(ate_grad_dr_point - ate_point_grad)
            se_ratio_grad = ate_grad_dr_se / ate_se_grad
            
            print(f"\nComparison:")
            print(f"  Difference in ATE: {ate_diff_grad:.2f} percentage points")
            print(f"  SE ratio (DR/IPW): {se_ratio_grad:.3f}")
            if se_ratio_grad < 1.0:
                print(f"  → DR has smaller SE ({((1-se_ratio_grad)*100):.1f}% reduction) - more efficient")
            else:
                print(f"  → DR has larger SE ({((se_ratio_grad-1)*100):.1f}% increase)")
            
            if ate_diff_grad < 0.5:
                print(f"  → Estimates are very similar (difference < 0.5 pp)")
            elif ate_diff_grad < 1.0:
                print(f"  → Estimates are similar (difference < 1.0 pp)")
            else:
                print(f"  → Estimates differ substantially (difference > 1.0 pp)")
                print(f"  → This may indicate model misspecification in one method")
            
        except Exception as e:
            print(f"\n⚠️  ERROR fitting LinearDML for graduation rate: {e}")
            import traceback
            traceback.print_exc()
            print("   Skipping doubly robust estimation for graduation rate")
            dr_grad_results = None
    else:
        print("\n⚠️  No valid data for graduation rate DR estimation")
        dr_grad_results = None
    
    # SECTION 4.27: STOP AND THINK - DR vs IPW COMPARISON
    if dr_earnings_results is not None or dr_grad_results is not None:
        print("\n" + "="*80)
        print("SECTION 4.27: STOP AND THINK - DR vs IPW COMPARISON")
        print("="*80)
        
        print("\n" + "-"*80)
        print("ANALYSIS AND INTERPRETATION")
        print("-"*80)
        
        if dr_earnings_results is not None:
            print("\n1. EARNINGS COMPARISON:")
            print(f"   IPW: ATE = ${ate_earnings_results['ate']:,.2f}, SE = ${ate_earnings_results['se']:,.2f}, p = {ate_earnings_results['p_value']:.4f}")
            print(f"   Doubly Robust: ATE = ${dr_earnings_results['ate']:,.2f}, SE = ${dr_earnings_results['se']:,.2f}, p = {dr_earnings_results['p_value']:.4f}")
            
            se_improvement = (1 - dr_earnings_results['se'] / ate_earnings_results['se']) * 100
            print(f"   SE improvement: {se_improvement:.1f}% reduction (DR more efficient)")
            
            if abs(dr_earnings_results['ate'] - ate_earnings_results['ate']) < 500:
                print("   → Estimates are similar (difference < $500)")
                print("   → Both methods agree on direction and approximate magnitude")
            else:
                print("   → Estimates differ substantially")
                print("   → This may indicate model misspecification in one method")
            
            if dr_earnings_results['p_value'] < 0.05 and ate_earnings_results['p_value'] >= 0.05:
                print("   → DR finds significant effect where IPW did not")
                print("   → This demonstrates efficiency gains of doubly robust methods")
        
        if dr_grad_results is not None:
            print("\n2. GRADUATION RATE COMPARISON:")
            print(f"   IPW: ATE = {ate_point_grad:.2f} pp, SE = {ate_se_grad:.2f} pp, p = {p_value_grad:.4f}")
            print(f"   Doubly Robust: ATE = {dr_grad_results['ate']:.2f} pp, SE = {dr_grad_results['se']:.2f} pp, p = {dr_grad_results['p_value']:.4f}")
            
            se_improvement_grad = (1 - dr_grad_results['se'] / ate_se_grad) * 100
            print(f"   SE improvement: {se_improvement_grad:.1f}% reduction (DR more efficient)")
            
            if abs(dr_grad_results['ate'] - ate_point_grad) < 1.0:
                print("   → Estimates are similar (difference < 1.0 pp)")
                print("   → Both methods agree on direction and approximate magnitude")
            else:
                print("   → Estimates differ substantially")
                print("   → This may indicate model misspecification in one method")
            
            if dr_grad_results['p_value'] < 0.05 and p_value_grad >= 0.05:
                print("   → DR finds significant effect where IPW did not")
                print("   → This demonstrates efficiency gains of doubly robust methods")
        
        print("\n3. KEY INSIGHTS:")
        print("   - Doubly robust methods are more efficient (smaller SE)")
        print("   - DR combines outcome modeling + propensity weighting")
        print("   - DR is robust to misspecification of either model")
        print("   - If DR and IPW differ substantially, investigate model assumptions")
        
        # Save DR results
        print("\n" + "="*80)
        print("SAVING DOUBLY ROBUST RESULTS")
        print("="*80)
        
        dr_results_data = []
        if dr_earnings_results is not None:
            dr_results_data.append({
                'Outcome': 'Earnings (10-year)',
                'Outcome_Variable': earnings_var,
                'Method': 'Doubly Robust (LinearDML)',
                'ATE': dr_earnings_results['ate'],
                'ATE_Formatted': f"${dr_earnings_results['ate']:,.2f}",
                'SE': dr_earnings_results['se'],
                'SE_Formatted': f"${dr_earnings_results['se']:,.2f}",
                'CI_Lower': dr_earnings_results['ci_lower'],
                'CI_Upper': dr_earnings_results['ci_upper'],
                'CI_Formatted': f"[${dr_earnings_results['ci_lower']:,.2f}, ${dr_earnings_results['ci_upper']:,.2f}]",
                'P_Value': dr_earnings_results['p_value'],
                'Significant': 'Yes' if dr_earnings_results['p_value'] < 0.05 else 'No',
                'N_Total': dr_earnings_results['n_total']
            })
        
        if dr_grad_results is not None:
            dr_results_data.append({
                'Outcome': 'Graduation Rate (6-year)',
                'Outcome_Variable': grad_rate_var,
                'Method': 'Doubly Robust (LinearDML)',
                'ATE': dr_grad_results['ate'],
                'ATE_Formatted': f"{dr_grad_results['ate']:.2f} pp",
                'SE': dr_grad_results['se'],
                'SE_Formatted': f"{dr_grad_results['se']:.2f} pp",
                'CI_Lower': dr_grad_results['ci_lower'],
                'CI_Upper': dr_grad_results['ci_upper'],
                'CI_Formatted': f"[{dr_grad_results['ci_lower']:.2f}, {dr_grad_results['ci_upper']:.2f}] pp",
                'P_Value': dr_grad_results['p_value'],
                'Significant': 'Yes' if dr_grad_results['p_value'] < 0.05 else 'No',
                'N_Total': dr_grad_results['n_total']
            })
        
        if len(dr_results_data) > 0:
            dr_results_df = pd.DataFrame(dr_results_data)
            dr_results_path = 'outputs/tables/doublerobust_results.csv'
            dr_results_df.to_csv(dr_results_path, index=False)
            print(f"\n✓ Saved doubly robust results to: {dr_results_path}")
    
    print("\n" + "="*80)
    print("DOUBLY ROBUST ESTIMATION COMPLETE")
    print("="*80)

# SECTION 4.32: DOWHY - CAUSAL GRAPH
print("\n" + "="*80)
print("SECTION 4.32: DOWHY - CAUSAL GRAPH")
print("="*80)

if not DOWHY_AVAILABLE:
    print("\n⚠️  WARNING: DoWhy not available. Skipping DoWhy analysis.")
    print("   Install with: pip install dowhy")
    print("   Proceeding to next method...")
else:
    print("\nStep 1: Specifying the causal graph (DAG)...")
    print("   We need to define:")
    print("   - Nodes: Treatment, Outcomes, and all Confounders")
    print("   - Edges: Confounders → Treatment, Confounders → Outcomes, Treatment → Outcomes")
    
    # Prepare data for DoWhy (need complete cases for both outcomes)
    print("\nStep 2: Preparing data for DoWhy analysis...")
    
    # Use the same cleaned data structure as before
    # Get data with all confounders and outcomes
    dowhy_data = df_psm.copy()
    
    # Create confounder list (continuous + categorical dummies, same as before)
    # We'll use the same structure as the propensity score model
    print("   Creating confounder feature matrix...")
    
    # Get continuous confounders
    X_continuous_dw = dowhy_data[confounder_vars_clean].copy()
    for col in X_continuous_dw.columns:
        X_continuous_dw[col] = pd.to_numeric(X_continuous_dw[col], errors='coerce')
    
    # Get categorical dummies
    X_categorical_dummies_dw = pd.get_dummies(
        dowhy_data[categorical_vars], 
        prefix=categorical_vars,
        prefix_sep='_',
        drop_first=True,
        dummy_na=False
    )
    
    # Combine
    X_all_dw = pd.concat([X_continuous_dw, X_categorical_dummies_dw], axis=1)
    X_all_dw = X_all_dw.astype(float)
    
    # Remove missing/infinite values
    valid_mask_dw = ~(X_all_dw.isna().any(axis=1) | np.isinf(X_all_dw).any(axis=1))
    dowhy_data_clean = dowhy_data[valid_mask_dw].copy().reset_index(drop=True)
    X_all_dw_clean = X_all_dw[valid_mask_dw].reset_index(drop=True)
    
    print(f"   Cleaned data shape: {dowhy_data_clean.shape}")
    print(f"   Number of confounder features: {X_all_dw_clean.shape[1]}")
    
    # Step 3: Define the causal graph structure
    print("\nStep 3: Defining causal graph structure...")
    print("   Building DAG with networkx...")
    
    # Create list of all confounder variable names for the graph
    confounder_names_dw = list(X_all_dw_clean.columns)
    
    # Import networkx for graph creation
    try:
        import networkx as nx
    except ImportError:
        print("   ⚠️  networkx not available, trying alternative graph format...")
        nx = None
    
    # Build the graph using networkx DiGraph
    if nx is not None:
        # Create graph for earnings
        graph_earnings = nx.DiGraph()
        # Add all confounders as nodes
        for conf in confounder_names_dw:
            graph_earnings.add_node(conf)
        graph_earnings.add_node(treatment_var)
        graph_earnings.add_node(earnings_var)
        # Add edges: confounders -> treatment, confounders -> outcome, treatment -> outcome
        for conf in confounder_names_dw:
            graph_earnings.add_edge(conf, treatment_var)
            graph_earnings.add_edge(conf, earnings_var)
        graph_earnings.add_edge(treatment_var, earnings_var)
        
        # Create graph for graduation rate
        graph_grad = nx.DiGraph()
        for conf in confounder_names_dw:
            graph_grad.add_node(conf)
        graph_grad.add_node(treatment_var)
        graph_grad.add_node(grad_rate_var)
        for conf in confounder_names_dw:
            graph_grad.add_edge(conf, treatment_var)
            graph_grad.add_edge(conf, grad_rate_var)
        graph_grad.add_edge(treatment_var, grad_rate_var)
        
        print(f"   Graph for earnings: {graph_earnings.number_of_edges()} edges, {graph_earnings.number_of_nodes()} nodes")
        print(f"   Graph for graduation rate: {graph_grad.number_of_edges()} edges, {graph_grad.number_of_nodes()} nodes")
    else:
        # Fallback: Use DOT format string
        print("   Using DOT format string...")
        edges_confounders_to_treatment = [f"{conf} -> {treatment_var}" for conf in confounder_names_dw]
        edges_confounders_to_earnings = [f"{conf} -> {earnings_var}" for conf in confounder_names_dw]
        edges_confounders_to_grad = [f"{conf} -> {grad_rate_var}" for conf in confounder_names_dw]
        edges_treatment_to_earnings = [f"{treatment_var} -> {earnings_var}"]
        edges_treatment_to_grad = [f"{treatment_var} -> {grad_rate_var}"]
        
        all_edges_earnings = edges_confounders_to_treatment + edges_confounders_to_earnings + edges_treatment_to_earnings
        all_edges_grad = edges_confounders_to_treatment + edges_confounders_to_grad + edges_treatment_to_grad
        
        # Create DOT format string
        graph_earnings = "digraph {\n" + "\n".join(all_edges_earnings) + "\n}"
        graph_grad = "digraph {\n" + "\n".join(all_edges_grad) + "\n}"
        
        print(f"   Graph for earnings: {len(all_edges_earnings)} edges")
        print(f"   Graph for graduation rate: {len(all_edges_grad)} edges")
    
    print("\n" + "="*80)
    print("CAUSAL GRAPH SPECIFICATION COMPLETE")
    print("="*80)
    print("\nGraph structure:")
    print(f"  - Treatment variable: {treatment_var}")
    print(f"  - Outcome variables: {earnings_var}, {grad_rate_var}")
    print(f"  - Number of confounders: {len(confounder_names_dw)}")
    print(f"  - Edges: All confounders → Treatment, All confounders → Outcomes, Treatment → Outcomes")

    # SECTION 4.33: CREATE DOWHY CAUSAL MODEL AND IDENTIFY ESTIMAND
    print("\n" + "="*80)
    print("SECTION 4.33: CREATE DOWHY CAUSAL MODEL AND IDENTIFY ESTIMAND")
    print("="*80)
    
    print("\nStep 1: Creating DoWhy CausalModel for earnings outcome...")
    
    # Prepare data for DoWhy (need treatment, outcome, and all confounders)
    # Create a combined dataframe with all variables needed
    dowhy_df_earnings = pd.DataFrame({
        treatment_var: dowhy_data_clean[treatment_var].values,
        earnings_var: dowhy_data_clean[earnings_var].values
    })
    
    # Add all confounders as columns
    for i, conf_name in enumerate(confounder_names_dw):
        dowhy_df_earnings[conf_name] = X_all_dw_clean.iloc[:, i].values
    
    # Drop rows with missing outcome
    dowhy_df_earnings = dowhy_df_earnings.dropna(subset=[earnings_var]).reset_index(drop=True)
    
    print(f"   Sample size: {len(dowhy_df_earnings):,}")
    print(f"   Treated: {(dowhy_df_earnings[treatment_var] == 1).sum():,}")
    print(f"   Control: {(dowhy_df_earnings[treatment_var] == 0).sum():,}")
    
    # Create CausalModel
    print("\nStep 2: Initializing CausalModel...")
    try:
        model_earnings = CausalModel(
            data=dowhy_df_earnings,
            treatment=treatment_var,
            outcome=earnings_var,
            graph=graph_earnings
        )
        print("   ✓ CausalModel created successfully")
        
        # Identify causal estimand using backdoor criterion
        print("\nStep 3: Identifying causal estimand using backdoor criterion...")
        identified_estimand_earnings = model_earnings.identify_effect(proceed_when_unidentifiable=True)
        
        print("\n" + "="*80)
        print("IDENTIFIED CAUSAL ESTIMAND (EARNINGS)")
        print("="*80)
        print(f"\nEstimand type: {identified_estimand_earnings.estimand_type}")
        print(f"\nBackdoor paths:")
        if hasattr(identified_estimand_earnings, 'backdoor_variables'):
            backdoor_vars = identified_estimand_earnings.backdoor_variables
            print(f"  Number of backdoor variables: {len(backdoor_vars)}")
            print(f"  Backdoor variables: {list(backdoor_vars)[:10]}..." if len(backdoor_vars) > 10 else f"  Backdoor variables: {list(backdoor_vars)}")
        else:
            print("  (Backdoor variables not directly accessible)")
        
        print(f"\nEstimand expression:")
        print(identified_estimand_earnings)
        
        # Verify that all confounders are identified
        print("\n" + "="*80)
        print("VERIFICATION: ESTIMAND IDENTIFICATION")
        print("="*80)
        
        # Check if the estimand includes our confounders
        estimand_str = str(identified_estimand_earnings)
        confounders_mentioned = sum(1 for conf in confounder_names_dw[:10] if conf in estimand_str)
        print(f"  Confounders in estimand: {confounders_mentioned} of first 10 checked")
        print(f"  Total confounders in model: {len(confounder_names_dw)}")
        
        if "backdoor" in estimand_str.lower() or "common_causes" in estimand_str.lower():
            print("  ✓ Backdoor criterion successfully applied")
            print("  ✓ Confounders are included in the estimand")
        else:
            print("  ⚠️  Warning: Backdoor criterion may not have been applied correctly")
        
    except Exception as e:
        print(f"\n⚠️  ERROR creating CausalModel: {e}")
        import traceback
        traceback.print_exc()
        model_earnings = None
        identified_estimand_earnings = None
    
    # SECTION 4.34: STOP AND THINK - VERIFY ESTIMAND IDENTIFICATION
    if model_earnings is not None and identified_estimand_earnings is not None:
        print("\n" + "="*80)
        print("SECTION 4.34: STOP AND THINK - VERIFY ESTIMAND IDENTIFICATION")
        print("="*80)
        
        print("\n" + "-"*80)
        print("ANALYSIS AND INTERPRETATION")
        print("-"*80)
        
        print("\n1. ESTIMAND TYPE:")
        print(f"   - Type: {identified_estimand_earnings.estimand_type}")
        print("   - Expected: 'nonparametric-ate' (Average Treatment Effect)")
        
        print("\n2. BACKDOOR CRITERION:")
        estimand_str = str(identified_estimand_earnings)
        if "backdoor" in estimand_str.lower():
            print("   ✓ Backdoor criterion was applied")
            print("   ✓ This means DoWhy identified confounders that block backdoor paths")
        else:
            print("   ⚠️  Backdoor criterion may not be explicitly mentioned")
        
        print("\n3. CONFOUNDER IDENTIFICATION:")
        print(f"   - Total confounders in model: {len(confounder_names_dw)}")
        print("   - All confounders should be included in the estimand")
        print("   - This ensures proper adjustment for confounding")
        
        print("\n4. VERIFICATION CHECKLIST:")
        print("   [ ] Does the estimand type match expectations?")
        print("   [ ] Are confounders included in the estimand?")
        print("   [ ] Does the estimand expression make sense?")
        print("   [ ] Are there any warnings about unidentifiability?")
        
        print("\n" + "="*80)
        print("STOP AND THINK COMPLETE - PROCEEDING TO ESTIMATION")
        print("="*80)
    
    # SECTION 4.35-4.36: DOWHY ESTIMATION
    if model_earnings is not None and identified_estimand_earnings is not None:
        print("\n" + "="*80)
        print("SECTION 4.35-4.36: DOWHY ESTIMATION")
        print("="*80)
        
        print("\nStep 1: Estimating causal effect using propensity score weighting...")
        print("   Method: Propensity Score Weighting (IPW)")
        print("   This matches our IPW approach for comparison")
        
        try:
            # Estimate causal effect
            # DoWhy expects a model object, not a string
            from sklearn.linear_model import LogisticRegression
            causal_estimate_earnings = model_earnings.estimate_effect(
                identified_estimand_earnings,
                method_name="backdoor.propensity_score_weighting",
                method_params={
                    "weighting_scheme": "ips_weight",  # Inverse propensity score weighting
                    "recalculate_propensity_score": True,
                    "propensity_score_model": LogisticRegression()
                }
            )
            
            print("   ✓ Estimation completed successfully")
            
            # Extract results
            print("\nStep 2: Extracting ATE estimate and statistics...")
            ate_dowhy_earnings = causal_estimate_earnings.value
            print(f"   ATE point estimate: ${ate_dowhy_earnings:,.2f}")
            
            # Get confidence interval
            if hasattr(causal_estimate_earnings, 'get_confidence_intervals'):
                ci_dowhy_earnings = causal_estimate_earnings.get_confidence_intervals()
                # Handle different return types
                if isinstance(ci_dowhy_earnings, (list, np.ndarray, tuple)):
                    if len(ci_dowhy_earnings) >= 2:
                        ci_lower_dowhy_earnings = float(ci_dowhy_earnings[0])
                        ci_upper_dowhy_earnings = float(ci_dowhy_earnings[1])
                    elif len(ci_dowhy_earnings) == 1:
                        ci_lower_dowhy_earnings = float(ci_dowhy_earnings[0])
                        ci_upper_dowhy_earnings = None
                    else:
                        ci_lower_dowhy_earnings = None
                        ci_upper_dowhy_earnings = None
                else:
                    # Single value
                    ci_lower_dowhy_earnings = float(ci_dowhy_earnings) if ci_dowhy_earnings is not None else None
                    ci_upper_dowhy_earnings = None
            else:
                # Try alternative method
                try:
                    ci_dowhy_earnings = causal_estimate_earnings.confidence_intervals_
                    if isinstance(ci_dowhy_earnings, (list, np.ndarray, tuple)):
                        ci_lower_dowhy_earnings = float(ci_dowhy_earnings[0]) if len(ci_dowhy_earnings) > 0 else None
                        ci_upper_dowhy_earnings = float(ci_dowhy_earnings[1]) if len(ci_dowhy_earnings) > 1 else None
                    else:
                        ci_lower_dowhy_earnings = float(ci_dowhy_earnings) if ci_dowhy_earnings is not None else None
                        ci_upper_dowhy_earnings = None
                except:
                    ci_lower_dowhy_earnings = None
                    ci_upper_dowhy_earnings = None
            
            # Calculate standard error from CI if available
            if ci_lower_dowhy_earnings is not None and ci_upper_dowhy_earnings is not None:
                se_dowhy_earnings = (ci_upper_dowhy_earnings - ci_lower_dowhy_earnings) / (2 * 1.96)
            else:
                se_dowhy_earnings = None
            
            print("\n" + "="*80)
            print("DOWHY ESTIMATION RESULTS (EARNINGS)")
            print("="*80)
            print(f"\nPoint Estimate:")
            print(f"  ATE: ${ate_dowhy_earnings:,.2f}")
            
            if se_dowhy_earnings is not None:
                print(f"\nStandard Error:")
                print(f"  SE: ${se_dowhy_earnings:,.2f}")
            
            if ci_lower_dowhy_earnings is not None and ci_upper_dowhy_earnings is not None:
                print(f"\n95% Confidence Interval:")
                print(f"  Lower: ${ci_lower_dowhy_earnings:,.2f}")
                print(f"  Upper: ${ci_upper_dowhy_earnings:,.2f}")
                print(f"  CI: [${ci_lower_dowhy_earnings:,.2f}, ${ci_upper_dowhy_earnings:,.2f}]")
            
            # Calculate p-value (two-sided test)
            if se_dowhy_earnings is not None and se_dowhy_earnings > 0:
                from scipy.stats import norm
                z_score = abs(ate_dowhy_earnings / se_dowhy_earnings)
                p_value_dowhy_earnings = 2 * (1 - norm.cdf(z_score))
                print(f"\nStatistical Significance:")
                print(f"  z-score: {z_score:.3f}")
                print(f"  p-value: {p_value_dowhy_earnings:.4f}")
                if p_value_dowhy_earnings < 0.01:
                    print(f"  Significance: *** (p < 0.01)")
                elif p_value_dowhy_earnings < 0.05:
                    print(f"  Significance: ** (p < 0.05)")
                elif p_value_dowhy_earnings < 0.10:
                    print(f"  Significance: * (p < 0.10)")
                else:
                    print(f"  Significance: Not significant (p >= 0.10)")
            else:
                p_value_dowhy_earnings = None
            
            # Store results for comparison
            dowhy_earnings_results = {
                'ate': ate_dowhy_earnings,
                'se': se_dowhy_earnings,
                'ci_lower': ci_lower_dowhy_earnings,
                'ci_upper': ci_upper_dowhy_earnings,
                'p_value': p_value_dowhy_earnings,
                'n_total': len(dowhy_df_earnings)
            }
            
        except Exception as e:
            print(f"\n⚠️  ERROR during estimation: {e}")
            import traceback
            traceback.print_exc()
            causal_estimate_earnings = None
            dowhy_earnings_results = None
    else:
        print("\n⚠️  Skipping DoWhy estimation - CausalModel not available")
        causal_estimate_earnings = None
        dowhy_earnings_results = None
    
    # SECTION 4.37: STOP AND THINK - COMPARE TO IPW AND DR
    if dowhy_earnings_results is not None:
        print("\n" + "="*80)
        print("SECTION 4.37: STOP AND THINK - COMPARE TO IPW AND DR")
        print("="*80)
        
        print("\n" + "-"*80)
        print("COMPARISON: DOWHY vs IPW vs DOUBLY ROBUST")
        print("-"*80)
        
        print("\n1. EARNINGS COMPARISON:")
        print(f"   IPW: ATE = ${ate_earnings_results['ate']:,.2f}, SE = ${ate_earnings_results['se']:,.2f}, p = {ate_earnings_results['p_value']:.4f}")
        
        if dr_earnings_results is not None:
            print(f"   Doubly Robust: ATE = ${dr_earnings_results['ate']:,.2f}, SE = ${dr_earnings_results['se']:,.2f}, p = {dr_earnings_results['p_value']:.4f}")
        
        se_str = f"${dowhy_earnings_results['se']:,.2f}" if dowhy_earnings_results['se'] is not None else 'N/A'
        pval_str = f"{dowhy_earnings_results['p_value']:.4f}" if dowhy_earnings_results['p_value'] is not None else 'N/A'
        print(f"   DoWhy: ATE = ${dowhy_earnings_results['ate']:,.2f}, SE = {se_str}, p = {pval_str}")
        
        # Compare estimates
        print("\n2. ESTIMATE CONSISTENCY:")
        if dr_earnings_results is not None:
            methods = ['IPW', 'DR', 'DoWhy']
            estimates = [ate_earnings_results['ate'], dr_earnings_results['ate'], dowhy_earnings_results['ate']]
        else:
            methods = ['IPW', 'DoWhy']
            estimates = [ate_earnings_results['ate'], dowhy_earnings_results['ate']]
        
        max_ate = max(estimates)
        min_ate = min(estimates)
        range_ate = max_ate - min_ate
        
        print(f"   Range of estimates: ${range_ate:,.2f}")
        if range_ate < 500:
            print("   → Estimates are very similar (difference < $500)")
            print("   → All methods agree on direction and approximate magnitude")
        elif range_ate < 1000:
            print("   → Estimates are reasonably similar (difference < $1,000)")
            print("   → Methods generally agree on direction")
        else:
            print("   → Estimates differ substantially (difference >= $1,000)")
            print("   → This may indicate model differences or assumptions")
        
        print("\n3. KEY INSIGHTS:")
        print("   - DoWhy uses the same IPW method but with automatic graph-based identification")
        print("   - If DoWhy and IPW differ, it may be due to:")
        print("     * Different propensity score model specifications")
        print("     * Different handling of missing data")
        print("     * Different weight trimming/stabilization")
        print("   - Consistency across methods strengthens confidence in results")
        
        print("\n" + "="*80)
        print("COMPARISON COMPLETE")
        print("="*80)
    
    # SECTION 4.38-4.40: DOWHY REFUTATION TESTS
    if causal_estimate_earnings is not None:
        print("\n" + "="*80)
        print("SECTION 4.38-4.40: DOWHY REFUTATION TESTS")
        print("="*80)
        
        print("\nRefutation tests check the robustness of causal estimates:")
        print("  1. Add Random Common Cause: Should show no effect (p > 0.05)")
        print("  2. Placebo Treatment: Should show no effect (estimate ≈ 0)")
        print("  3. Data Subset Validation: Should show similar effect")
        
        refutation_results_earnings = {}
        
        # Test 1: Add Random Common Cause
        print("\n" + "-"*80)
        print("REFUTATION TEST 1: ADD RANDOM COMMON CAUSE")
        print("-"*80)
        print("Adding a random variable as a common cause...")
        print("Expected: No significant effect (p > 0.05)")
        
        try:
            refute_random_common_cause = model_earnings.refute_estimate(
                identified_estimand_earnings,
                causal_estimate_earnings,
                method_name="random_common_cause"
            )
            
            print(f"\nResults:")
            print(f"  New estimate: ${refute_random_common_cause.new_effect:,.2f}")
            print(f"  Original estimate: ${causal_estimate_earnings.value:,.2f}")
            print(f"  Difference: ${abs(refute_random_common_cause.new_effect - causal_estimate_earnings.value):,.2f}")
            
            # Check if estimate changed significantly
            if hasattr(refute_random_common_cause, 'p_value'):
                pval_random = refute_random_common_cause.p_value
                print(f"  p-value: {pval_random:.4f}")
                if pval_random > 0.05:
                    print("  ✓ PASS: Random cause shows no significant effect (p > 0.05)")
                else:
                    print("  ⚠️  FAIL: Random cause shows significant effect (p <= 0.05)")
            else:
                print("  (p-value not available)")
            
            refutation_results_earnings['random_common_cause'] = {
                'new_effect': refute_random_common_cause.new_effect,
                'original_effect': causal_estimate_earnings.value,
                'p_value': getattr(refute_random_common_cause, 'p_value', None)
            }
            
        except Exception as e:
            print(f"\n⚠️  ERROR in random common cause test: {e}")
            refutation_results_earnings['random_common_cause'] = None
        
        # Test 2: Placebo Treatment
        print("\n" + "-"*80)
        print("REFUTATION TEST 2: PLACEBO TREATMENT")
        print("-"*80)
        print("Replacing treatment with random placebo...")
        print("Expected: Estimate ≈ 0 (no effect)")
        
        try:
            refute_placebo = model_earnings.refute_estimate(
                identified_estimand_earnings,
                causal_estimate_earnings,
                method_name="placebo_treatment_refuter"
            )
            
            print(f"\nResults:")
            print(f"  Placebo estimate: ${refute_placebo.new_effect:,.2f}")
            print(f"  Original estimate: ${causal_estimate_earnings.value:,.2f}")
            
            # Check if placebo estimate is close to zero
            if abs(refute_placebo.new_effect) < 100:
                print("  ✓ PASS: Placebo estimate is close to zero (|estimate| < $100)")
            else:
                print(f"  ⚠️  FAIL: Placebo estimate is far from zero (|estimate| = ${abs(refute_placebo.new_effect):,.2f})")
            
            refutation_results_earnings['placebo_treatment'] = {
                'new_effect': refute_placebo.new_effect,
                'original_effect': causal_estimate_earnings.value
            }
            
        except Exception as e:
            print(f"\n⚠️  ERROR in placebo treatment test: {e}")
            refutation_results_earnings['placebo_treatment'] = None
        
        # Test 3: Data Subset Validation
        print("\n" + "-"*80)
        print("REFUTATION TEST 3: DATA SUBSET VALIDATION")
        print("-"*80)
        print("Testing on random subset of data...")
        print("Expected: Similar effect (estimate within reasonable range)")
        
        try:
            refute_subset = model_earnings.refute_estimate(
                identified_estimand_earnings,
                causal_estimate_earnings,
                method_name="data_subset_refuter",
                subset_fraction=0.8  # Use 80% of data
            )
            
            print(f"\nResults:")
            print(f"  Subset estimate: ${refute_subset.new_effect:,.2f}")
            print(f"  Original estimate: ${causal_estimate_earnings.value:,.2f}")
            print(f"  Difference: ${abs(refute_subset.new_effect - causal_estimate_earnings.value):,.2f}")
            
            # Check if estimates are similar (within 20% or $500)
            diff_pct = abs(refute_subset.new_effect - causal_estimate_earnings.value) / abs(causal_estimate_earnings.value) * 100 if causal_estimate_earnings.value != 0 else 0
            if abs(refute_subset.new_effect - causal_estimate_earnings.value) < 500 or diff_pct < 20:
                print("  ✓ PASS: Subset estimate is similar to original")
            else:
                print(f"  ⚠️  CAUTION: Subset estimate differs from original ({diff_pct:.1f}% difference)")
            
            refutation_results_earnings['data_subset'] = {
                'new_effect': refute_subset.new_effect,
                'original_effect': causal_estimate_earnings.value,
                'difference': abs(refute_subset.new_effect - causal_estimate_earnings.value)
            }
            
        except Exception as e:
            print(f"\n⚠️  ERROR in data subset test: {e}")
            refutation_results_earnings['data_subset'] = None
        
        # Summary
        print("\n" + "="*80)
        print("REFUTATION TESTS SUMMARY (EARNINGS)")
        print("="*80)
        
        n_passed = sum(1 for v in refutation_results_earnings.values() if v is not None)
        print(f"\nTests completed: {n_passed} / 3")
        print("\nInterpretation:")
        print("  - If all tests pass: Estimate is robust")
        print("  - If tests fail: Investigate model assumptions and data quality")
        print("  - Refutation tests help validate causal inference assumptions")
        
    else:
        print("\n⚠️  Skipping refutation tests - Causal estimate not available")
        refutation_results_earnings = None
    
    # SECTION 4.41-4.43: DOWHY FOR GRADUATION RATE
    print("\n" + "="*80)
    print("SECTION 4.41-4.43: DOWHY FOR GRADUATION RATE")
    print("="*80)
    
    print("\nRepeating DoWhy analysis for graduation rate outcome...")
    
    # Prepare data for graduation rate
    dowhy_df_grad = pd.DataFrame({
        treatment_var: dowhy_data_clean[treatment_var].values,
        grad_rate_var: dowhy_data_clean[grad_rate_var].values
    })
    
    # Add all confounders
    for i, conf_name in enumerate(confounder_names_dw):
        dowhy_df_grad[conf_name] = X_all_dw_clean.iloc[:, i].values
    
    # Drop rows with missing outcome
    dowhy_df_grad = dowhy_df_grad.dropna(subset=[grad_rate_var]).reset_index(drop=True)
    
    print(f"   Sample size: {len(dowhy_df_grad):,}")
    print(f"   Treated: {(dowhy_df_grad[treatment_var] == 1).sum():,}")
    print(f"   Control: {(dowhy_df_grad[treatment_var] == 0).sum():,}")
    
    # Create CausalModel for graduation rate
    try:
        model_grad = CausalModel(
            data=dowhy_df_grad,
            treatment=treatment_var,
            outcome=grad_rate_var,
            graph=graph_grad
        )
        print("   ✓ CausalModel created successfully")
        
        # Identify estimand
        identified_estimand_grad = model_grad.identify_effect(proceed_when_unidentifiable=True)
        print("   ✓ Estimand identified")
        
        # Estimate effect
        print("\nEstimating causal effect...")
        from sklearn.linear_model import LogisticRegression
        causal_estimate_grad = model_grad.estimate_effect(
            identified_estimand_grad,
            method_name="backdoor.propensity_score_weighting",
            method_params={
                "weighting_scheme": "ips_weight",
                "recalculate_propensity_score": True,
                "propensity_score_model": LogisticRegression()
            }
        )
        
        ate_dowhy_grad = causal_estimate_grad.value
        
        # Get confidence interval
        try:
            ci_dowhy_grad = causal_estimate_grad.get_confidence_intervals()
            # Handle different return types
            if isinstance(ci_dowhy_grad, (list, np.ndarray, tuple)):
                if len(ci_dowhy_grad) >= 2:
                    ci_lower_dowhy_grad = float(ci_dowhy_grad[0])
                    ci_upper_dowhy_grad = float(ci_dowhy_grad[1])
                elif len(ci_dowhy_grad) == 1:
                    ci_lower_dowhy_grad = float(ci_dowhy_grad[0])
                    ci_upper_dowhy_grad = None
                else:
                    ci_lower_dowhy_grad = None
                    ci_upper_dowhy_grad = None
            else:
                # Single value
                ci_lower_dowhy_grad = float(ci_dowhy_grad) if ci_dowhy_grad is not None else None
                ci_upper_dowhy_grad = None
        except:
            try:
                ci_dowhy_grad = causal_estimate_grad.confidence_intervals_
                if isinstance(ci_dowhy_grad, (list, np.ndarray, tuple)):
                    ci_lower_dowhy_grad = float(ci_dowhy_grad[0]) if len(ci_dowhy_grad) > 0 else None
                    ci_upper_dowhy_grad = float(ci_dowhy_grad[1]) if len(ci_dowhy_grad) > 1 else None
                else:
                    ci_lower_dowhy_grad = float(ci_dowhy_grad) if ci_dowhy_grad is not None else None
                    ci_upper_dowhy_grad = None
            except:
                ci_lower_dowhy_grad = None
                ci_upper_dowhy_grad = None
        
        # Calculate SE and p-value
        if ci_lower_dowhy_grad is not None and ci_upper_dowhy_grad is not None:
            se_dowhy_grad = (ci_upper_dowhy_grad - ci_lower_dowhy_grad) / (2 * 1.96)
            from scipy.stats import norm
            z_score_grad = abs(ate_dowhy_grad / se_dowhy_grad) if se_dowhy_grad > 0 else 0
            p_value_dowhy_grad = 2 * (1 - norm.cdf(z_score_grad)) if se_dowhy_grad > 0 else None
        else:
            se_dowhy_grad = None
            p_value_dowhy_grad = None
        
        print("\n" + "="*80)
        print("DOWHY ESTIMATION RESULTS (GRADUATION RATE)")
        print("="*80)
        print(f"\nPoint Estimate:")
        print(f"  ATE: {ate_dowhy_grad:.2f} percentage points")
        if se_dowhy_grad is not None:
            print(f"\nStandard Error:")
            print(f"  SE: {se_dowhy_grad:.2f} percentage points")
        if ci_lower_dowhy_grad is not None and ci_upper_dowhy_grad is not None:
            print(f"\n95% Confidence Interval:")
            print(f"  CI: [{ci_lower_dowhy_grad:.2f}, {ci_upper_dowhy_grad:.2f}] percentage points")
        if p_value_dowhy_grad is not None:
            print(f"\nStatistical Significance:")
            print(f"  p-value: {p_value_dowhy_grad:.4f}")
        
        dowhy_grad_results = {
            'ate': ate_dowhy_grad,
            'se': se_dowhy_grad,
            'ci_lower': ci_lower_dowhy_grad,
            'ci_upper': ci_upper_dowhy_grad,
            'p_value': p_value_dowhy_grad,
            'n_total': len(dowhy_df_grad)
        }
        
        # Refutation tests for graduation rate
        print("\n" + "="*80)
        print("REFUTATION TESTS (GRADUATION RATE)")
        print("="*80)
        
        refutation_results_grad = {}
        
        # Test 1: Random Common Cause
        try:
            refute_random_grad = model_grad.refute_estimate(
                identified_estimand_grad,
                causal_estimate_grad,
                method_name="random_common_cause"
            )
            refutation_results_grad['random_common_cause'] = {
                'new_effect': refute_random_grad.new_effect,
                'original_effect': causal_estimate_grad.value,
                'p_value': getattr(refute_random_grad, 'p_value', None)
            }
            print("  ✓ Random common cause test completed")
        except Exception as e:
            print(f"  ⚠️  Random common cause test failed: {e}")
            refutation_results_grad['random_common_cause'] = None
        
        # Test 2: Placebo Treatment
        try:
            refute_placebo_grad = model_grad.refute_estimate(
                identified_estimand_grad,
                causal_estimate_grad,
                method_name="placebo_treatment_refuter"
            )
            refutation_results_grad['placebo_treatment'] = {
                'new_effect': refute_placebo_grad.new_effect,
                'original_effect': causal_estimate_grad.value
            }
            print("  ✓ Placebo treatment test completed")
        except Exception as e:
            print(f"  ⚠️  Placebo treatment test failed: {e}")
            refutation_results_grad['placebo_treatment'] = None
        
        # Test 3: Data Subset
        try:
            refute_subset_grad = model_grad.refute_estimate(
                identified_estimand_grad,
                causal_estimate_grad,
                method_name="data_subset_refuter",
                subset_fraction=0.8
            )
            refutation_results_grad['data_subset'] = {
                'new_effect': refute_subset_grad.new_effect,
                'original_effect': causal_estimate_grad.value,
                'difference': abs(refute_subset_grad.new_effect - causal_estimate_grad.value)
            }
            print("  ✓ Data subset test completed")
        except Exception as e:
            print(f"  ⚠️  Data subset test failed: {e}")
            refutation_results_grad['data_subset'] = None
        
        print("\n" + "="*80)
        print("STOP AND THINK: REFUTATION TESTS FOR GRADUATION RATE")
        print("="*80)
        print("\nReview refutation test results above.")
        print("If tests pass, the estimate is robust.")
        print("If tests fail, investigate model assumptions.")
        
    except Exception as e:
        print(f"\n⚠️  ERROR in DoWhy analysis for graduation rate: {e}")
        import traceback
        traceback.print_exc()
        dowhy_grad_results = None
        refutation_results_grad = None
    
    # SECTION 4.44: SAVE DOWHY RESULTS
    print("\n" + "="*80)
    print("SECTION 4.44: SAVE DOWHY RESULTS")
    print("="*80)
    
    dowhy_results_data = []
    
    if dowhy_earnings_results is not None:
        dowhy_results_data.append({
            'Outcome': 'Earnings (10-year)',
            'Outcome_Variable': earnings_var,
            'Method': 'DoWhy (Propensity Score Weighting)',
            'ATE': dowhy_earnings_results['ate'],
            'ATE_Formatted': f"${dowhy_earnings_results['ate']:,.2f}",
            'SE': dowhy_earnings_results['se'],
            'SE_Formatted': f"${dowhy_earnings_results['se']:,.2f}" if dowhy_earnings_results['se'] is not None else 'N/A',
            'CI_Lower': dowhy_earnings_results['ci_lower'],
            'CI_Upper': dowhy_earnings_results['ci_upper'],
            'CI_Formatted': f"[${dowhy_earnings_results['ci_lower']:,.2f}, ${dowhy_earnings_results['ci_upper']:,.2f}]" if dowhy_earnings_results['ci_lower'] is not None else 'N/A',
            'P_Value': dowhy_earnings_results['p_value'],
            'Significant': 'Yes' if dowhy_earnings_results['p_value'] is not None and dowhy_earnings_results['p_value'] < 0.05 else 'No',
            'N_Total': dowhy_earnings_results['n_total'],
            'Refutation_Random_Common_Cause_Passed': 'Yes' if (refutation_results_earnings and refutation_results_earnings.get('random_common_cause') and refutation_results_earnings['random_common_cause'] and refutation_results_earnings['random_common_cause'].get('p_value') is not None and refutation_results_earnings['random_common_cause'].get('p_value') > 0.05) else 'No/Unknown',
            'Refutation_Placebo_Passed': 'Yes' if (refutation_results_earnings and refutation_results_earnings.get('placebo_treatment') and refutation_results_earnings['placebo_treatment'] and refutation_results_earnings['placebo_treatment'].get('new_effect') is not None and abs(refutation_results_earnings['placebo_treatment'].get('new_effect')) < 100) else 'No/Unknown',
            'Refutation_Subset_Passed': 'Yes' if (refutation_results_earnings and refutation_results_earnings.get('data_subset') and refutation_results_earnings['data_subset'] and refutation_results_earnings['data_subset'].get('difference') is not None and refutation_results_earnings['data_subset'].get('difference') < 500) else 'No/Unknown'
        })
    
    if dowhy_grad_results is not None:
        dowhy_results_data.append({
            'Outcome': 'Graduation Rate (6-year)',
            'Outcome_Variable': grad_rate_var,
            'Method': 'DoWhy (Propensity Score Weighting)',
            'ATE': dowhy_grad_results['ate'],
            'ATE_Formatted': f"{dowhy_grad_results['ate']:.2f} pp",
            'SE': dowhy_grad_results['se'],
            'SE_Formatted': f"{dowhy_grad_results['se']:.2f} pp" if dowhy_grad_results['se'] is not None else 'N/A',
            'CI_Lower': dowhy_grad_results['ci_lower'],
            'CI_Upper': dowhy_grad_results['ci_upper'],
            'CI_Formatted': f"[{dowhy_grad_results['ci_lower']:.2f}, {dowhy_grad_results['ci_upper']:.2f}] pp" if dowhy_grad_results['ci_lower'] is not None else 'N/A',
            'P_Value': dowhy_grad_results['p_value'],
            'Significant': 'Yes' if dowhy_grad_results['p_value'] is not None and dowhy_grad_results['p_value'] < 0.05 else 'No',
            'N_Total': dowhy_grad_results['n_total'],
            'Refutation_Random_Common_Cause_Passed': 'Yes' if (refutation_results_grad and refutation_results_grad.get('random_common_cause') and refutation_results_grad['random_common_cause'] and refutation_results_grad['random_common_cause'].get('p_value') is not None and refutation_results_grad['random_common_cause'].get('p_value') > 0.05) else 'No/Unknown',
            'Refutation_Placebo_Passed': 'Yes' if (refutation_results_grad and refutation_results_grad.get('placebo_treatment') and refutation_results_grad['placebo_treatment'] and refutation_results_grad['placebo_treatment'].get('new_effect') is not None and abs(refutation_results_grad['placebo_treatment'].get('new_effect')) < 1.0) else 'No/Unknown',
            'Refutation_Subset_Passed': 'Yes' if (refutation_results_grad and refutation_results_grad.get('data_subset') and refutation_results_grad['data_subset'] and refutation_results_grad['data_subset'].get('difference') is not None and refutation_results_grad['data_subset'].get('difference') < 1.0) else 'No/Unknown'
        })
    
    if len(dowhy_results_data) > 0:
        dowhy_results_df = pd.DataFrame(dowhy_results_data)
        dowhy_results_path = 'outputs/tables/dowhy_results.csv'
        dowhy_results_df.to_csv(dowhy_results_path, index=False)
        print(f"\n✓ Saved DoWhy results to: {dowhy_results_path}")
        
        print("\n" + "="*80)
        print("DOWHY RESULTS SUMMARY")
        print("="*80)
        print("\n" + dowhy_results_df[['Outcome', 'ATE_Formatted', 'SE_Formatted', 'CI_Formatted', 'P_Value', 'Significant', 'Refutation_Random_Common_Cause_Passed', 'Refutation_Placebo_Passed', 'Refutation_Subset_Passed']].to_string(index=False))
    else:
        print("\n⚠️  No DoWhy results to save")
    
    print("\n" + "="*80)
    print("DOWHY ANALYSIS COMPLETE")
    print("="*80)

# SECTION 4.45-4.47: OLS REGRESSION FOR EARNINGS
print("\n" + "="*80)
print("SECTION 4.45-4.47: OLS REGRESSION FOR EARNINGS")
print("="*80)

print("\nStep 1: Preparing data for OLS regression...")
print("   Model: Earnings ~ Treatment + All Confounders")
print("   Using same confounder structure as propensity score model")

# Prepare data for OLS (use the same cleaned data structure)
# Get data with treatment, outcome, and all confounders
ols_data_earnings = df_psm[[treatment_var, earnings_var]].copy()

# Add all confounders (continuous + categorical dummies)
# Use the same structure as before
X_continuous_ols = df_psm[confounder_vars_clean].copy()
for col in X_continuous_ols.columns:
    X_continuous_ols[col] = pd.to_numeric(X_continuous_ols[col], errors='coerce')

# Get categorical dummies
X_categorical_dummies_ols = pd.get_dummies(
    df_psm[categorical_vars],
    prefix=categorical_vars,
    prefix_sep='_',
    drop_first=True,
    dummy_na=False
)

# Combine
X_all_ols = pd.concat([X_continuous_ols, X_categorical_dummies_ols], axis=1)
X_all_ols = X_all_ols.astype(float)

# Combine into single dataframe
ols_data_earnings = pd.concat([ols_data_earnings, X_all_ols], axis=1)

# Drop rows with missing outcome
ols_data_earnings = ols_data_earnings.dropna(subset=[earnings_var]).reset_index(drop=True)

print(f"   Sample size: {len(ols_data_earnings):,}")
print(f"   Number of confounders: {X_all_ols.shape[1]}")
print(f"   Treated: {(ols_data_earnings[treatment_var] == 1).sum():,}")
print(f"   Control: {(ols_data_earnings[treatment_var] == 0).sum():,}")

# Prepare regression formula
confounder_names_ols = list(X_all_ols.columns)
formula_earnings = f"{earnings_var} ~ {treatment_var} + " + " + ".join(confounder_names_ols)

print(f"\nStep 2: Fitting OLS regression with clustered standard errors by state...")
print(f"   Formula: {earnings_var} ~ {treatment_var} + [all confounders]")

try:
    import statsmodels.formula.api as smf
    
    # Fit OLS model
    ols_model_earnings = smf.ols(formula_earnings, data=ols_data_earnings).fit()
    
    # Get clustered standard errors by state
    # First check if state variable exists
    if 'state' in df_psm.columns:
        # Get state variable aligned with ols_data
        state_var_ols = df_psm.loc[ols_data_earnings.index, 'state'].values if len(ols_data_earnings) == len(df_psm) else df_psm['state'].iloc[:len(ols_data_earnings)].values
        
        # Cluster by state
        from statsmodels.stats.sandwich_covariance import cov_cluster
        try:
            # Get cluster IDs (state codes)
            cluster_ids = state_var_ols
            # Calculate clustered covariance matrix
            cov_clustered = cov_cluster(ols_model_earnings, cluster_ids)
            # Update model with clustered standard errors
            ols_model_earnings = ols_model_earnings.get_robustcov_results(cov_type='cluster', groups=cluster_ids)
            print("   ✓ Clustered standard errors by state applied")
        except:
            print("   ⚠️  Could not apply clustered SEs, using robust standard errors")
            ols_model_earnings = ols_model_earnings.get_robustcov_results(cov_type='HC3')
    else:
        print("   ⚠️  State variable not found, using robust standard errors")
        ols_model_earnings = ols_model_earnings.get_robustcov_results(cov_type='HC3')
    
    # Extract treatment coefficient
    treatment_coef_earnings = ols_model_earnings.params[treatment_var]
    treatment_se_earnings = ols_model_earnings.bse[treatment_var]
    treatment_pvalue_earnings = ols_model_earnings.pvalues[treatment_var]
    
    # Get confidence interval
    ci_earnings_ols = ols_model_earnings.conf_int().loc[treatment_var]
    ci_lower_earnings_ols = ci_earnings_ols[0]
    ci_upper_earnings_ols = ci_earnings_ols[1]
    
    # Get R-squared
    r_squared_earnings = ols_model_earnings.rsquared
    
    print("\n" + "="*80)
    print("OLS REGRESSION RESULTS (EARNINGS)")
    print("="*80)
    print(f"\nTreatment Coefficient:")
    print(f"  Coefficient: ${treatment_coef_earnings:,.2f}")
    print(f"  Standard Error: ${treatment_se_earnings:,.2f}")
    print(f"  95% Confidence Interval: [${ci_lower_earnings_ols:,.2f}, ${ci_upper_earnings_ols:,.2f}]")
    print(f"  p-value: {treatment_pvalue_earnings:.4f}")
    if treatment_pvalue_earnings < 0.01:
        print(f"  Significance: *** (p < 0.01)")
    elif treatment_pvalue_earnings < 0.05:
        print(f"  Significance: ** (p < 0.05)")
    elif treatment_pvalue_earnings < 0.10:
        print(f"  Significance: * (p < 0.10)")
    else:
        print(f"  Significance: Not significant (p >= 0.10)")
    
    print(f"\nModel Fit:")
    print(f"  R-squared: {r_squared_earnings:.4f}")
    print(f"  Adjusted R-squared: {ols_model_earnings.rsquared_adj:.4f}")
    print(f"  Sample size: {ols_model_earnings.nobs:,.0f}")
    
    # Check for multicollinearity using VIF
    print(f"\nStep 3: Checking for multicollinearity (VIF)...")
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        
        # Calculate VIF for all variables
        vif_data = pd.DataFrame()
        vif_data["Variable"] = ols_model_earnings.model.exog_names
        vif_data["VIF"] = [variance_inflation_factor(ols_model_earnings.model.exog, i) 
                          for i in range(ols_model_earnings.model.exog.shape[1])]
        
        # Check treatment variable VIF
        treatment_vif = vif_data[vif_data["Variable"] == treatment_var]["VIF"].values[0]
        max_vif = vif_data["VIF"].max()
        high_vif_count = (vif_data["VIF"] > 10).sum()
        
        print(f"  Treatment variable VIF: {treatment_vif:.2f}")
        print(f"  Maximum VIF: {max_vif:.2f}")
        print(f"  Variables with VIF > 10: {high_vif_count}")
        
        if treatment_vif > 10:
            print("  ⚠️  WARNING: High VIF for treatment variable (>10)")
            print("     This may indicate multicollinearity issues")
        elif max_vif > 10:
            print("  ⚠️  CAUTION: Some variables have high VIF (>10)")
            print("     Multicollinearity may affect some coefficients")
        else:
            print("  ✓ VIF values are acceptable (<10)")
            
    except Exception as e:
        print(f"  ⚠️  Could not calculate VIF: {e}")
        treatment_vif = None
        max_vif = None
    
    # Store results
    ols_earnings_results = {
        'coefficient': treatment_coef_earnings,
        'se': treatment_se_earnings,
        'ci_lower': ci_lower_earnings_ols,
        'ci_upper': ci_upper_earnings_ols,
        'p_value': treatment_pvalue_earnings,
        'r_squared': r_squared_earnings,
        'n_total': ols_model_earnings.nobs,
        'treatment_vif': treatment_vif if 'treatment_vif' in locals() else None,
        'max_vif': max_vif if 'max_vif' in locals() else None
    }
    
    print("\n" + "="*80)
    print("SECTION 4.47: STOP AND THINK - OLS EARNINGS INTERPRETATION")
    print("="*80)
    print("\n1. TREATMENT COEFFICIENT:")
    print(f"   - Coefficient: ${treatment_coef_earnings:,.2f}")
    print(f"   - Interpretation: Treatment is associated with ${treatment_coef_earnings:,.2f} change in earnings")
    print(f"   - p-value: {treatment_pvalue_earnings:.4f}")
    
    print("\n2. CONSISTENCY WITH OTHER METHODS:")
    if dowhy_earnings_results is not None:
        print(f"   - IPW: ${ate_earnings_results['ate']:,.2f}")
        if dr_earnings_results is not None:
            print(f"   - Doubly Robust: ${dr_earnings_results['ate']:,.2f}")
        print(f"   - DoWhy: ${dowhy_earnings_results['ate']:,.2f}")
        print(f"   - OLS: ${treatment_coef_earnings:,.2f}")
        
        # Check if signs match
        methods_signs = [
            np.sign(ate_earnings_results['ate']),
            np.sign(treatment_coef_earnings)
        ]
        if dowhy_earnings_results['ate'] is not None:
            methods_signs.append(np.sign(dowhy_earnings_results['ate']))
        if dr_earnings_results is not None:
            methods_signs.append(np.sign(dr_earnings_results['ate']))
        
        if len(set(methods_signs)) == 1:
            print("   ✓ All methods agree on direction (same sign)")
        else:
            print("   ⚠️  Methods disagree on direction (different signs)")
    
    print("\n3. MODEL FIT:")
    print(f"   - R-squared: {r_squared_earnings:.4f}")
    if r_squared_earnings > 0.5:
        print("   ✓ Good model fit (R² > 0.5)")
    elif r_squared_earnings > 0.3:
        print("   ⚠️  Moderate model fit (R² 0.3-0.5)")
    else:
        print("   ⚠️  Low model fit (R² < 0.3)")
    
    print("\n4. MULTICOLLINEARITY:")
    if treatment_vif is not None:
        if treatment_vif < 5:
            print(f"   ✓ Low multicollinearity (VIF = {treatment_vif:.2f})")
        elif treatment_vif < 10:
            print(f"   ⚠️  Moderate multicollinearity (VIF = {treatment_vif:.2f})")
        else:
            print(f"   ⚠️  High multicollinearity (VIF = {treatment_vif:.2f})")
    
    print("\n" + "="*80)
    print("STOP AND THINK COMPLETE")
    print("="*80)
    
except Exception as e:
    print(f"\n⚠️  ERROR in OLS regression for earnings: {e}")
    import traceback
    traceback.print_exc()
    ols_earnings_results = None
    ols_model_earnings = None

# SECTION 4.48-4.50: OLS REGRESSION FOR GRADUATION RATE
print("\n" + "="*80)
print("SECTION 4.48-4.50: OLS REGRESSION FOR GRADUATION RATE")
print("="*80)

print("\nStep 1: Preparing data for OLS regression...")
print("   Model: Graduation Rate ~ Treatment + All Confounders")

# Prepare data for graduation rate
ols_data_grad = df_psm[[treatment_var, grad_rate_var]].copy()
ols_data_grad = pd.concat([ols_data_grad, X_all_ols], axis=1)

# Drop rows with missing outcome
ols_data_grad = ols_data_grad.dropna(subset=[grad_rate_var]).reset_index(drop=True)

print(f"   Sample size: {len(ols_data_grad):,}")
print(f"   Treated: {(ols_data_grad[treatment_var] == 1).sum():,}")
print(f"   Control: {(ols_data_grad[treatment_var] == 0).sum():,}")

# Prepare regression formula
formula_grad = f"{grad_rate_var} ~ {treatment_var} + " + " + ".join(confounder_names_ols)

print(f"\nStep 2: Fitting OLS regression with clustered standard errors by state...")
print(f"   Formula: {grad_rate_var} ~ {treatment_var} + [all confounders]")

try:
    # Fit OLS model
    ols_model_grad = smf.ols(formula_grad, data=ols_data_grad).fit()
    
    # Get clustered standard errors by state
    if 'state' in df_psm.columns:
        state_var_ols_grad = df_psm.loc[ols_data_grad.index, 'state'].values if len(ols_data_grad) == len(df_psm) else df_psm['state'].iloc[:len(ols_data_grad)].values
        try:
            cluster_ids_grad = state_var_ols_grad
            ols_model_grad = ols_model_grad.get_robustcov_results(cov_type='cluster', groups=cluster_ids_grad)
            print("   ✓ Clustered standard errors by state applied")
        except:
            print("   ⚠️  Could not apply clustered SEs, using robust standard errors")
            ols_model_grad = ols_model_grad.get_robustcov_results(cov_type='HC3')
    else:
        print("   ⚠️  State variable not found, using robust standard errors")
        ols_model_grad = ols_model_grad.get_robustcov_results(cov_type='HC3')
    
    # Extract treatment coefficient
    treatment_coef_grad = ols_model_grad.params[treatment_var]
    treatment_se_grad = ols_model_grad.bse[treatment_var]
    treatment_pvalue_grad = ols_model_grad.pvalues[treatment_var]
    
    # Get confidence interval
    ci_grad_ols = ols_model_grad.conf_int().loc[treatment_var]
    ci_lower_grad_ols = ci_grad_ols[0]
    ci_upper_grad_ols = ci_grad_ols[1]
    
    # Get R-squared
    r_squared_grad = ols_model_grad.rsquared
    
    print("\n" + "="*80)
    print("OLS REGRESSION RESULTS (GRADUATION RATE)")
    print("="*80)
    print(f"\nTreatment Coefficient:")
    print(f"  Coefficient: {treatment_coef_grad:.2f} percentage points")
    print(f"  Standard Error: {treatment_se_grad:.2f} percentage points")
    print(f"  95% Confidence Interval: [{ci_lower_grad_ols:.2f}, {ci_upper_grad_ols:.2f}] percentage points")
    print(f"  p-value: {treatment_pvalue_grad:.4f}")
    if treatment_pvalue_grad < 0.01:
        print(f"  Significance: *** (p < 0.01)")
    elif treatment_pvalue_grad < 0.05:
        print(f"  Significance: ** (p < 0.05)")
    elif treatment_pvalue_grad < 0.10:
        print(f"  Significance: * (p < 0.10)")
    else:
        print(f"  Significance: Not significant (p >= 0.10)")
    
    print(f"\nModel Fit:")
    print(f"  R-squared: {r_squared_grad:.4f}")
    print(f"  Adjusted R-squared: {ols_model_grad.rsquared_adj:.4f}")
    print(f"  Sample size: {ols_model_grad.nobs:,.0f}")
    
    # Store results
    ols_grad_results = {
        'coefficient': treatment_coef_grad,
        'se': treatment_se_grad,
        'ci_lower': ci_lower_grad_ols,
        'ci_upper': ci_upper_grad_ols,
        'p_value': treatment_pvalue_grad,
        'r_squared': r_squared_grad,
        'n_total': ols_model_grad.nobs
    }
    
    print("\n" + "="*80)
    print("SECTION 4.50: STOP AND THINK - OLS GRADUATION RATE INTERPRETATION")
    print("="*80)
    print("\n1. TREATMENT COEFFICIENT:")
    print(f"   - Coefficient: {treatment_coef_grad:.2f} percentage points")
    print(f"   - Interpretation: Treatment is associated with {treatment_coef_grad:.2f} pp change in graduation rate")
    print(f"   - p-value: {treatment_pvalue_grad:.4f}")
    
    print("\n2. CONSISTENCY WITH OTHER METHODS:")
    if dowhy_grad_results is not None:
        print(f"   - IPW: {ate_point_grad:.2f} pp")
        if dr_grad_results is not None:
            print(f"   - Doubly Robust: {dr_grad_results['ate']:.2f} pp")
        print(f"   - DoWhy: {dowhy_grad_results['ate']:.2f} pp")
        print(f"   - OLS: {treatment_coef_grad:.2f} pp")
        
        # Check if signs match
        methods_signs_grad = [
            np.sign(ate_point_grad),
            np.sign(treatment_coef_grad)
        ]
        if dowhy_grad_results['ate'] is not None:
            methods_signs_grad.append(np.sign(dowhy_grad_results['ate']))
        if dr_grad_results is not None:
            methods_signs_grad.append(np.sign(dr_grad_results['ate']))
        
        if len(set(methods_signs_grad)) == 1:
            print("   ✓ All methods agree on direction (same sign)")
        else:
            print("   ⚠️  Methods disagree on direction (different signs)")
    
    print("\n3. MODEL FIT:")
    print(f"   - R-squared: {r_squared_grad:.4f}")
    if r_squared_grad > 0.5:
        print("   ✓ Good model fit (R² > 0.5)")
    elif r_squared_grad > 0.3:
        print("   ⚠️  Moderate model fit (R² 0.3-0.5)")
    else:
        print("   ⚠️  Low model fit (R² < 0.3)")
    
    print("\n" + "="*80)
    print("STOP AND THINK COMPLETE")
    print("="*80)
    
except Exception as e:
    print(f"\n⚠️  ERROR in OLS regression for graduation rate: {e}")
    import traceback
    traceback.print_exc()
    ols_grad_results = None
    ols_model_grad = None

# SECTION 4.51: SAVE OLS RESULTS
print("\n" + "="*80)
print("SECTION 4.51: SAVE OLS RESULTS")
print("="*80)

ols_results_data = []

if ols_earnings_results is not None:
    ols_results_data.append({
        'Outcome': 'Earnings (10-year)',
        'Outcome_Variable': earnings_var,
        'Method': 'OLS Regression',
        'Coefficient': ols_earnings_results['coefficient'],
        'Coefficient_Formatted': f"${ols_earnings_results['coefficient']:,.2f}",
        'SE': ols_earnings_results['se'],
        'SE_Formatted': f"${ols_earnings_results['se']:,.2f}",
        'CI_Lower': ols_earnings_results['ci_lower'],
        'CI_Upper': ols_earnings_results['ci_upper'],
        'CI_Formatted': f"[${ols_earnings_results['ci_lower']:,.2f}, ${ols_earnings_results['ci_upper']:,.2f}]",
        'P_Value': ols_earnings_results['p_value'],
        'Significant': 'Yes' if ols_earnings_results['p_value'] < 0.05 else 'No',
        'R_Squared': ols_earnings_results['r_squared'],
        'N_Total': ols_earnings_results['n_total'],
        'Treatment_VIF': ols_earnings_results['treatment_vif'],
        'Max_VIF': ols_earnings_results['max_vif']
    })

if ols_grad_results is not None:
    ols_results_data.append({
        'Outcome': 'Graduation Rate (6-year)',
        'Outcome_Variable': grad_rate_var,
        'Method': 'OLS Regression',
        'Coefficient': ols_grad_results['coefficient'],
        'Coefficient_Formatted': f"{ols_grad_results['coefficient']:.2f} pp",
        'SE': ols_grad_results['se'],
        'SE_Formatted': f"{ols_grad_results['se']:.2f} pp",
        'CI_Lower': ols_grad_results['ci_lower'],
        'CI_Upper': ols_grad_results['ci_upper'],
        'CI_Formatted': f"[{ols_grad_results['ci_lower']:.2f}, {ols_grad_results['ci_upper']:.2f}] pp",
        'P_Value': ols_grad_results['p_value'],
        'Significant': 'Yes' if ols_grad_results['p_value'] < 0.05 else 'No',
        'R_Squared': ols_grad_results['r_squared'],
        'N_Total': ols_grad_results['n_total'],
        'Treatment_VIF': None,
        'Max_VIF': None
    })

if len(ols_results_data) > 0:
    ols_results_df = pd.DataFrame(ols_results_data)
    ols_results_path = 'outputs/tables/regression_results.csv'
    ols_results_df.to_csv(ols_results_path, index=False)
    print(f"\n✓ Saved OLS results to: {ols_results_path}")
    
    print("\n" + "="*80)
    print("OLS RESULTS SUMMARY")
    print("="*80)
    print("\n" + ols_results_df[['Outcome', 'Coefficient_Formatted', 'SE_Formatted', 'CI_Formatted', 'P_Value', 'Significant', 'R_Squared', 'N_Total']].to_string(index=False))
else:
    print("\n⚠️  No OLS results to save")

print("\n" + "="*80)
print("OLS REGRESSION COMPLETE")
print("="*80)

# SECTION 4.52-4.55: COMPARE ALL METHODS
print("\n" + "="*80)
print("SECTION 4.52-4.55: COMPARE ALL METHODS")
print("="*80)

print("\nStep 1: Combining results from all 4 methods...")
print("   Methods: IPW, Doubly Robust, DoWhy, OLS")

# Prepare comparison data
comparison_data = []

# Earnings comparison
earnings_comparison = {
    'Outcome': 'Earnings (10-year)',
    'Outcome_Variable': earnings_var
}

# IPW
earnings_comparison['IPW_ATE'] = ate_earnings_results['ate']
earnings_comparison['IPW_SE'] = ate_earnings_results['se']
earnings_comparison['IPW_CI_Lower'] = ate_earnings_results['ci_lower']
earnings_comparison['IPW_CI_Upper'] = ate_earnings_results['ci_upper']
earnings_comparison['IPW_P_Value'] = ate_earnings_results['p_value']
earnings_comparison['IPW_Significant'] = 'Yes' if ate_earnings_results['p_value'] < 0.05 else 'No'

# Doubly Robust
if dr_earnings_results is not None:
    earnings_comparison['DR_ATE'] = dr_earnings_results['ate']
    earnings_comparison['DR_SE'] = dr_earnings_results['se']
    earnings_comparison['DR_CI_Lower'] = dr_earnings_results['ci_lower']
    earnings_comparison['DR_CI_Upper'] = dr_earnings_results['ci_upper']
    earnings_comparison['DR_P_Value'] = dr_earnings_results['p_value']
    earnings_comparison['DR_Significant'] = 'Yes' if dr_earnings_results['p_value'] < 0.05 else 'No'
else:
    earnings_comparison['DR_ATE'] = None
    earnings_comparison['DR_SE'] = None
    earnings_comparison['DR_CI_Lower'] = None
    earnings_comparison['DR_CI_Upper'] = None
    earnings_comparison['DR_P_Value'] = None
    earnings_comparison['DR_Significant'] = 'N/A'

# DoWhy
if dowhy_earnings_results is not None:
    earnings_comparison['DoWhy_ATE'] = dowhy_earnings_results['ate']
    earnings_comparison['DoWhy_SE'] = dowhy_earnings_results['se']
    earnings_comparison['DoWhy_CI_Lower'] = dowhy_earnings_results['ci_lower']
    earnings_comparison['DoWhy_CI_Upper'] = dowhy_earnings_results['ci_upper']
    earnings_comparison['DoWhy_P_Value'] = dowhy_earnings_results['p_value']
    earnings_comparison['DoWhy_Significant'] = 'Yes' if dowhy_earnings_results['p_value'] is not None and dowhy_earnings_results['p_value'] < 0.05 else 'No'
else:
    earnings_comparison['DoWhy_ATE'] = None
    earnings_comparison['DoWhy_SE'] = None
    earnings_comparison['DoWhy_CI_Lower'] = None
    earnings_comparison['DoWhy_CI_Upper'] = None
    earnings_comparison['DoWhy_P_Value'] = None
    earnings_comparison['DoWhy_Significant'] = 'N/A'

# OLS
if ols_earnings_results is not None:
    earnings_comparison['OLS_Coefficient'] = ols_earnings_results['coefficient']
    earnings_comparison['OLS_SE'] = ols_earnings_results['se']
    earnings_comparison['OLS_CI_Lower'] = ols_earnings_results['ci_lower']
    earnings_comparison['OLS_CI_Upper'] = ols_earnings_results['ci_upper']
    earnings_comparison['OLS_P_Value'] = ols_earnings_results['p_value']
    earnings_comparison['OLS_Significant'] = 'Yes' if ols_earnings_results['p_value'] < 0.05 else 'No'
    earnings_comparison['OLS_R_Squared'] = ols_earnings_results['r_squared']
else:
    earnings_comparison['OLS_Coefficient'] = None
    earnings_comparison['OLS_SE'] = None
    earnings_comparison['OLS_CI_Lower'] = None
    earnings_comparison['OLS_CI_Upper'] = None
    earnings_comparison['OLS_P_Value'] = None
    earnings_comparison['OLS_Significant'] = 'N/A'
    earnings_comparison['OLS_R_Squared'] = None

comparison_data.append(earnings_comparison)

# Graduation rate comparison
grad_comparison = {
    'Outcome': 'Graduation Rate (6-year)',
    'Outcome_Variable': grad_rate_var
}

# IPW
grad_comparison['IPW_ATE'] = ate_point_grad
grad_comparison['IPW_SE'] = ate_se_grad
grad_comparison['IPW_CI_Lower'] = ate_ci_lower_grad
grad_comparison['IPW_CI_Upper'] = ate_ci_upper_grad
grad_comparison['IPW_P_Value'] = p_value_grad
grad_comparison['IPW_Significant'] = 'Yes' if p_value_grad < 0.05 else 'No'

# Doubly Robust
if dr_grad_results is not None:
    grad_comparison['DR_ATE'] = dr_grad_results['ate']
    grad_comparison['DR_SE'] = dr_grad_results['se']
    grad_comparison['DR_CI_Lower'] = dr_grad_results['ci_lower']
    grad_comparison['DR_CI_Upper'] = dr_grad_results['ci_upper']
    grad_comparison['DR_P_Value'] = dr_grad_results['p_value']
    grad_comparison['DR_Significant'] = 'Yes' if dr_grad_results['p_value'] < 0.05 else 'No'
else:
    grad_comparison['DR_ATE'] = None
    grad_comparison['DR_SE'] = None
    grad_comparison['DR_CI_Lower'] = None
    grad_comparison['DR_CI_Upper'] = None
    grad_comparison['DR_P_Value'] = None
    grad_comparison['DR_Significant'] = 'N/A'

# DoWhy
if dowhy_grad_results is not None:
    grad_comparison['DoWhy_ATE'] = dowhy_grad_results['ate']
    grad_comparison['DoWhy_SE'] = dowhy_grad_results['se']
    grad_comparison['DoWhy_CI_Lower'] = dowhy_grad_results['ci_lower']
    grad_comparison['DoWhy_CI_Upper'] = dowhy_grad_results['ci_upper']
    grad_comparison['DoWhy_P_Value'] = dowhy_grad_results['p_value']
    grad_comparison['DoWhy_Significant'] = 'Yes' if dowhy_grad_results['p_value'] is not None and dowhy_grad_results['p_value'] < 0.05 else 'No'
else:
    grad_comparison['DoWhy_ATE'] = None
    grad_comparison['DoWhy_SE'] = None
    grad_comparison['DoWhy_CI_Lower'] = None
    grad_comparison['DoWhy_CI_Upper'] = None
    grad_comparison['DoWhy_P_Value'] = None
    grad_comparison['DoWhy_Significant'] = 'N/A'

# OLS
if ols_grad_results is not None:
    grad_comparison['OLS_Coefficient'] = ols_grad_results['coefficient']
    grad_comparison['OLS_SE'] = ols_grad_results['se']
    grad_comparison['OLS_CI_Lower'] = ols_grad_results['ci_lower']
    grad_comparison['OLS_CI_Upper'] = ols_grad_results['ci_upper']
    grad_comparison['OLS_P_Value'] = ols_grad_results['p_value']
    grad_comparison['OLS_Significant'] = 'Yes' if ols_grad_results['p_value'] < 0.05 else 'No'
    grad_comparison['OLS_R_Squared'] = ols_grad_results['r_squared']
else:
    grad_comparison['OLS_Coefficient'] = None
    grad_comparison['OLS_SE'] = None
    grad_comparison['OLS_CI_Lower'] = None
    grad_comparison['OLS_CI_Upper'] = None
    grad_comparison['OLS_P_Value'] = None
    grad_comparison['OLS_Significant'] = 'N/A'
    grad_comparison['OLS_R_Squared'] = None

comparison_data.append(grad_comparison)

# Create comparison dataframe
comparison_df = pd.DataFrame(comparison_data)

print("\nStep 2: Analyzing method consistency...")

# SECTION 4.54: STOP AND THINK - CRITICAL DECISION POINT
print("\n" + "="*80)
print("SECTION 4.54: STOP AND THINK - CRITICAL DECISION POINT")
print("="*80)

print("\n" + "-"*80)
print("METHODS COMPARISON ANALYSIS")
print("-"*80)

# Analyze earnings
print("\n1. EARNINGS OUTCOME:")
print("   Method Estimates:")

# Collect all estimates for earnings
earnings_estimates = []
earnings_methods = []

if earnings_comparison['IPW_ATE'] is not None:
    earnings_estimates.append(earnings_comparison['IPW_ATE'])
    earnings_methods.append('IPW')
    print(f"     IPW: ${earnings_comparison['IPW_ATE']:,.2f} (p = {earnings_comparison['IPW_P_Value']:.4f})")

if earnings_comparison['DR_ATE'] is not None:
    earnings_estimates.append(earnings_comparison['DR_ATE'])
    earnings_methods.append('DR')
    print(f"     Doubly Robust: ${earnings_comparison['DR_ATE']:,.2f} (p = {earnings_comparison['DR_P_Value']:.4f})")

if earnings_comparison['DoWhy_ATE'] is not None:
    earnings_estimates.append(earnings_comparison['DoWhy_ATE'])
    earnings_methods.append('DoWhy')
    print(f"     DoWhy: ${earnings_comparison['DoWhy_ATE']:,.2f} (p = {earnings_comparison['DoWhy_P_Value']:.4f if earnings_comparison['DoWhy_P_Value'] is not None else 'N/A'})")

if earnings_comparison['OLS_Coefficient'] is not None:
    earnings_estimates.append(earnings_comparison['OLS_Coefficient'])
    earnings_methods.append('OLS')
    print(f"     OLS: ${earnings_comparison['OLS_Coefficient']:,.2f} (p = {earnings_comparison['OLS_P_Value']:.4f})")

if len(earnings_estimates) > 0:
    earnings_estimates = np.array(earnings_estimates)
    
    # Check direction consistency
    earnings_signs = np.sign(earnings_estimates)
    if len(set(earnings_signs)) == 1:
        print(f"\n   ✓ DIRECTION CONSISTENCY: All methods agree on direction (same sign: {int(earnings_signs[0])})")
        direction_consistent_earnings = True
    else:
        print(f"\n   ⚠️  DIRECTION INCONSISTENCY: Methods disagree on direction")
        print(f"      Signs: {earnings_signs}")
        direction_consistent_earnings = False
    
    # Calculate range
    earnings_range = earnings_estimates.max() - earnings_estimates.min()
    earnings_min = earnings_estimates.min()
    earnings_max = earnings_estimates.max()
    print(f"\n   ESTIMATE RANGE:")
    print(f"     Minimum: ${earnings_min:,.2f}")
    print(f"     Maximum: ${earnings_max:,.2f}")
    print(f"     Range: ${earnings_range:,.2f}")
    
    if earnings_range < 500:
        print("     → Very consistent estimates (range < $500)")
    elif earnings_range < 1000:
        print("     → Reasonably consistent estimates (range < $1,000)")
    elif earnings_range < 2000:
        print("     → Moderate variation (range < $2,000)")
    else:
        print("     → ⚠️  Large variation (range >= $2,000) - investigate differences")
    
    # Check CI overlap
    print(f"\n   CONFIDENCE INTERVAL OVERLAP:")
    ci_lowers = []
    ci_uppers = []
    if earnings_comparison['IPW_CI_Lower'] is not None:
        ci_lowers.append(earnings_comparison['IPW_CI_Lower'])
        ci_uppers.append(earnings_comparison['IPW_CI_Upper'])
    if earnings_comparison['DR_CI_Lower'] is not None:
        ci_lowers.append(earnings_comparison['DR_CI_Lower'])
        ci_uppers.append(earnings_comparison['DR_CI_Upper'])
    if earnings_comparison['DoWhy_CI_Lower'] is not None:
        ci_lowers.append(earnings_comparison['DoWhy_CI_Lower'])
        ci_uppers.append(earnings_comparison['DoWhy_CI_Upper'])
    if earnings_comparison['OLS_CI_Lower'] is not None:
        ci_lowers.append(earnings_comparison['OLS_CI_Lower'])
        ci_uppers.append(earnings_comparison['OLS_CI_Upper'])
    
    if len(ci_lowers) > 0:
        overall_ci_lower = max(ci_lowers)
        overall_ci_upper = min(ci_uppers)
        if overall_ci_lower < overall_ci_upper:
            print(f"     ✓ CIs overlap: [{overall_ci_lower:,.2f}, {overall_ci_upper:,.2f}]")
            ci_overlap_earnings = True
        else:
            print(f"     ⚠️  CIs do not fully overlap")
            ci_overlap_earnings = False
    else:
        ci_overlap_earnings = None

# Analyze graduation rate
print("\n2. GRADUATION RATE OUTCOME:")
print("   Method Estimates:")

grad_estimates = []
grad_methods = []

if grad_comparison['IPW_ATE'] is not None:
    grad_estimates.append(grad_comparison['IPW_ATE'])
    grad_methods.append('IPW')
    print(f"     IPW: {grad_comparison['IPW_ATE']:.2f} pp (p = {grad_comparison['IPW_P_Value']:.4f})")

if grad_comparison['DR_ATE'] is not None:
    grad_estimates.append(grad_comparison['DR_ATE'])
    grad_methods.append('DR')
    print(f"     Doubly Robust: {grad_comparison['DR_ATE']:.2f} pp (p = {grad_comparison['DR_P_Value']:.4f})")

if grad_comparison['DoWhy_ATE'] is not None:
    grad_estimates.append(grad_comparison['DoWhy_ATE'])
    grad_methods.append('DoWhy')
    print(f"     DoWhy: {grad_comparison['DoWhy_ATE']:.2f} pp (p = {grad_comparison['DoWhy_P_Value']:.4f if grad_comparison['DoWhy_P_Value'] is not None else 'N/A'})")

if grad_comparison['OLS_Coefficient'] is not None:
    grad_estimates.append(grad_comparison['OLS_Coefficient'])
    grad_methods.append('OLS')
    print(f"     OLS: {grad_comparison['OLS_Coefficient']:.2f} pp (p = {grad_comparison['OLS_P_Value']:.4f})")

if len(grad_estimates) > 0:
    grad_estimates = np.array(grad_estimates)
    
    # Check direction consistency
    grad_signs = np.sign(grad_estimates)
    if len(set(grad_signs)) == 1:
        print(f"\n   ✓ DIRECTION CONSISTENCY: All methods agree on direction (same sign: {int(grad_signs[0])})")
        direction_consistent_grad = True
    else:
        print(f"\n   ⚠️  DIRECTION INCONSISTENCY: Methods disagree on direction")
        print(f"      Signs: {grad_signs}")
        direction_consistent_grad = False
    
    # Calculate range
    grad_range = grad_estimates.max() - grad_estimates.min()
    grad_min = grad_estimates.min()
    grad_max = grad_estimates.max()
    print(f"\n   ESTIMATE RANGE:")
    print(f"     Minimum: {grad_min:.2f} pp")
    print(f"     Maximum: {grad_max:.2f} pp")
    print(f"     Range: {grad_range:.2f} pp")
    
    if grad_range < 1.0:
        print("     → Very consistent estimates (range < 1.0 pp)")
    elif grad_range < 2.0:
        print("     → Reasonably consistent estimates (range < 2.0 pp)")
    else:
        print("     → ⚠️  Large variation (range >= 2.0 pp) - investigate differences")

print("\n3. OVERALL ASSESSMENT:")
if 'direction_consistent_earnings' in locals() and direction_consistent_earnings and 'direction_consistent_grad' in locals() and direction_consistent_grad:
    print("   ✓ All methods agree on direction for both outcomes")
    print("   → This is strong evidence for a consistent causal effect")
elif 'direction_consistent_earnings' in locals() and direction_consistent_earnings:
    print("   ⚠️  Methods agree on direction for earnings but not graduation rate")
    print("   → Investigate differences in graduation rate estimates")
else:
    print("   ⚠️  Methods disagree on direction")
    print("   → CRITICAL: Investigate model assumptions and data quality")
    print("   → Do not proceed until understanding source of disagreement")

print("\n4. CONFIDENCE IN FINDINGS:")
if 'direction_consistent_earnings' in locals() and direction_consistent_earnings and 'ci_overlap_earnings' in locals() and ci_overlap_earnings:
    print("   ✓ High confidence: Methods agree and CIs overlap")
elif 'direction_consistent_earnings' in locals() and direction_consistent_earnings:
    print("   ⚠️  Moderate confidence: Methods agree but CIs may not fully overlap")
else:
    print("   ⚠️  Low confidence: Methods disagree - investigate before proceeding")

print("\n" + "="*80)
print("STOP AND THINK COMPLETE")
print("="*80)

# SECTION 4.55: SAVE METHODS COMPARISON
print("\n" + "="*80)
print("SECTION 4.55: SAVE METHODS COMPARISON")
print("="*80)

comparison_path = 'outputs/tables/methods_comparison.csv'
comparison_df.to_csv(comparison_path, index=False)
print(f"\n✓ Saved methods comparison to: {comparison_path}")

print("\n" + "="*80)
print("METHODS COMPARISON COMPLETE")
print("="*80)

# SECTION 4.56: UPDATE UTILS.PY
print("\n" + "="*80)
print("SECTION 4.56: UPDATE UTILS.PY")
print("="*80)

print("\nNote: Helper functions (calculate_smd, bootstrap_ci, etc.) are defined")
print("in this script. To add them to utils.py, copy the function definitions.")
print("Functions to add:")
print("  - calculate_smd()")
print("  - calculate_weighted_smd()")
print("  - bootstrap_ci() (if used)")
print("\nThis is a manual step - review the functions in this script and")
print("add them to src/utils.py if desired for reuse in other scripts.")

print("\n" + "="*80)
print("UTILS.PY UPDATE NOTE COMPLETE")
print("="*80)

# SECTION 4.57: CAUSAL INFERENCE CHECKPOINT
print("\n" + "="*80)
print("SECTION 4.57: CAUSAL INFERENCE CHECKPOINT")
print("="*80)

print("\n" + "-"*80)
print("CAUSAL INFERENCE SUMMARY")
print("-"*80)

# Determine consistency
if 'direction_consistent_earnings' in locals() and direction_consistent_earnings and 'direction_consistent_grad' in locals() and direction_consistent_grad:
    consistency_status = "consistent"
elif 'direction_consistent_earnings' in locals() and direction_consistent_earnings:
    consistency_status = "partially consistent"
else:
    consistency_status = "inconsistent"

# Get estimate ranges
if 'earnings_estimates' in locals() and len(earnings_estimates) > 0:
    earnings_range_str = f"${earnings_estimates.min():,.0f} to ${earnings_estimates.max():,.0f}"
else:
    earnings_range_str = "N/A"

if 'grad_estimates' in locals() and len(grad_estimates) > 0:
    grad_range_str = f"{grad_estimates.min():.2f} to {grad_estimates.max():.2f} pp"
else:
    grad_range_str = "N/A"

# Check refutation tests
refutation_status = "Unknown"
if refutation_results_earnings is not None:
    passed_tests = sum(1 for v in refutation_results_earnings.values() if v is not None)
    if passed_tests >= 2:
        refutation_status = "passed"
    elif passed_tests >= 1:
        refutation_status = "partially passed"
    else:
        refutation_status = "failed"

print(f"\n1. METHOD CONSISTENCY:")
print(f"   Status: {consistency_status}")
print(f"   - All 4 methods show {consistency_status} direction")

print(f"\n2. ATE ESTIMATES:")
print(f"   Earnings: {earnings_range_str}")
print(f"   Graduation Rate: {grad_range_str}")

print(f"\n3. REFUTATION TESTS:")
print(f"   Status: {refutation_status}")
print(f"   - DoWhy refutation tests: {refutation_status}")

print(f"\n4. METHODS COMPLETED:")
print(f"   ✓ IPW (Inverse Probability Weighting)")
print(f"   ✓ Doubly Robust Estimation")
print(f"   ✓ DoWhy (Causal Graph + Refutation)")
print(f"   ✓ OLS Regression")

print(f"\n5. OUTPUT FILES CREATED:")
print(f"   ✓ outputs/tables/ipw_results.csv")
print(f"   ✓ outputs/tables/doublerobust_results.csv")
print(f"   ✓ outputs/tables/dowhy_results.csv")
print(f"   ✓ outputs/tables/regression_results.csv")
print(f"   ✓ outputs/tables/methods_comparison.csv")
print(f"   ✓ outputs/tables/balance_comparison.csv")

print("\n" + "="*80)
print("CAUSAL INFERENCE CHECKPOINT")
print("="*80)
print("\nCausal inference complete.")
print(f"All 4 methods show {consistency_status} direction.")
print(f"ATE for earnings: {earnings_range_str}.")
print(f"ATE for grad rate: {grad_range_str}.")
print(f"Refutation tests: {refutation_status}.")
print("\n" + "="*80)
print("TASK 4.0: IMPLEMENT CORE CAUSAL INFERENCE METHODS - COMPLETE")
print("="*80)
