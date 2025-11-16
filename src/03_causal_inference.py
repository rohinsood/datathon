# src/03_causal_inference.py
"""
Cleaned & corrected implementation for Task 4.1 - 4.7 (propensity score prep + diagnostics)
Author: (you)
Notes:
 - Robust handling of variable_lists.json (accepts strings or lists)
 - Ensures treatment is binary numeric 0/1
 - Avoids duplicate predictors between confounders and categorical_vars
 - Scales continuous covariates and uses regularized sklearn logistic
 - Logs rows removed and key diagnostics
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

# Drop rows with missing confounders (document)
valid_mask = ~X_all.isna().any(axis=1)
if n_rows_with_missing > 0:
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

# Get coefficient magnitudes (if available)
if model_type == "sklearn" and clf is not None:
    try:
        coefs = clf.coef_.ravel()
        coef_df = pd.Series(index=X_all.columns, data=np.abs(coefs)).sort_values(ascending=False).head(20)
        print_and_log("Top 20 absolute coefficient magnitudes from logistic (sklearn):\n" + coef_df.to_string())
    except Exception as e:
        print_and_log(f"Coefficient extraction failed: {e}")
elif model_type == "statsmodels" and sm_res is not None:
    try:
        # statsmodels coefficients (excluding constant)
        coefs = sm_res.params.iloc[1:].values  # Skip constant term
        coef_df = pd.Series(index=X_all.columns, data=np.abs(coefs)).sort_values(ascending=False).head(20)
        print_and_log("Top 20 absolute coefficient magnitudes from logistic (statsmodels):\n" + coef_df.to_string())
    except Exception as e:
        print_and_log(f"Coefficient extraction from statsmodels failed: {e}")
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

t0 = df[df[treatment_var] == 0]["propensity_score"]
t1 = df[df[treatment_var] == 1]["propensity_score"]

min_control, max_control = t0.min(), t0.max()
min_treated, max_treated = t1.min(), t1.max()
overlap_min = max(min_control, min_treated)
overlap_max = min(max_control, max_treated)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ax_hist = axes[0]
ax_box = axes[1]

# Histogram (density)
ax_hist.hist(t0, bins=40, density=True, alpha=0.6, label="Control (High Gap)")
ax_hist.hist(t1, bins=40, density=True, alpha=0.6, label="Treated (Low Gap)")
ax_hist.axvline(overlap_min, color="k", linestyle="--", label="overlap bounds")
ax_hist.axvline(overlap_max, color="k", linestyle="--")
ax_hist.set_xlabel("Propensity score")
ax_hist.set_ylabel("Density")
ax_hist.legend()
ax_hist.grid(alpha=0.25)

# Box plot
ax_box.boxplot([t0.values, t1.values], labels=["Control (High Gap)", "Treated (Low Gap)"])
ax_box.set_ylabel("Propensity score")
ax_box.grid(axis="y", alpha=0.25)

plt.suptitle("Propensity score distributions by treatment (with overlap bounds)")
plt.tight_layout(rect=[0, 0, 1, 0.95])
fig_file = FIG_PATH / "propensity_score_distribution.png"
plt.savefig(fig_file, dpi=300, bbox_inches="tight")
print_and_log(f"Saved propensity plot to {fig_file}")

# Overlap counts
in_overlap_control = ((t0 >= overlap_min) & (t0 <= overlap_max)).sum()
in_overlap_treated = ((t1 >= overlap_min) & (t1 <= overlap_max)).sum()
print_and_log(f"Overlap region: [{overlap_min:.4f}, {overlap_max:.4f}]")
print_and_log(f"In-overlap counts: control {in_overlap_control}/{len(t0)} ({in_overlap_control/len(t0):.1%}), "
              f"treated {in_overlap_treated}/{len(t1)} ({in_overlap_treated/len(t1):.1%})")

# Final note in log
append_log("Completed steps 4.1 - 4.7: data validated, propensity model fit, diagnostics & plots saved.")

# ============================================================================
# SECTION 4.8: RUN & ANALYZE - COMMON SUPPORT ASSESSMENT
# ============================================================================
print("\n" + "="*80)
print("4.8 RUN & ANALYZE: Common Support Assessment")
print("="*80)

# Detailed overlap analysis
print_and_log("\n" + "="*80)
print_and_log("COMMON SUPPORT DETAILED ANALYSIS")
print_and_log("="*80)

# Calculate overlap statistics
overlap_width = overlap_max - overlap_min
total_range_control = max_control - min_control
total_range_treated = max_treated - min_treated

print_and_log(f"\nPropensity Score Ranges:")
print_and_log(f"  Control (High Gap): [{min_control:.6f}, {max_control:.6f}] (width: {total_range_control:.6f})")
print_and_log(f"  Treated (Low Gap):  [{min_treated:.6f}, {max_treated:.6f}] (width: {total_range_treated:.6f})")
print_and_log(f"  Overlap Region:     [{overlap_min:.6f}, {overlap_max:.6f}] (width: {overlap_width:.6f})")

# Calculate percentage of each group in overlap
pct_control_in_overlap = (in_overlap_control / len(t0)) * 100
pct_treated_in_overlap = (in_overlap_treated / len(t1)) * 100

print_and_log(f"\nOverlap Coverage:")
print_and_log(f"  Control group: {in_overlap_control:,} / {len(t0):,} ({pct_control_in_overlap:.2f}%) in overlap region")
print_and_log(f"  Treated group: {in_overlap_treated:,} / {len(t1):,} ({pct_treated_in_overlap:.2f}%) in overlap region")

# Check for regions with no overlap
no_overlap_low = overlap_min > min(min_control, min_treated)
no_overlap_high = overlap_max < max(max_control, max_treated)

if no_overlap_low:
    gap_low = overlap_min - min(min_control, min_treated)
    print_and_log(f"\n⚠️  No overlap in lower tail: gap of {gap_low:.6f}")
    if min_control < min_treated:
        print_and_log(f"   Control group extends lower (min={min_control:.6f} vs treated min={min_treated:.6f})")
    else:
        print_and_log(f"   Treated group extends lower (min={min_treated:.6f} vs control min={min_control:.6f})")

if no_overlap_high:
    gap_high = max(max_control, max_treated) - overlap_max
    print_and_log(f"\n⚠️  No overlap in upper tail: gap of {gap_high:.6f}")
    if max_control > max_treated:
        print_and_log(f"   Control group extends higher (max={max_control:.6f} vs treated max={max_treated:.6f})")
    else:
        print_and_log(f"   Treated group extends higher (max={max_treated:.6f} vs control max={max_control:.6f})")

if not no_overlap_low and not no_overlap_high:
    print_and_log("\n✓ Complete overlap: both groups fully contained within overlap region")

# Calculate density in overlap region
# Use kernel density estimation or simple histogram to assess density
from scipy import stats

try:
    # Calculate density at overlap boundaries
    kde_control = stats.gaussian_kde(t0.values)
    kde_treated = stats.gaussian_kde(t1.values)
    
    # Sample points in overlap region
    overlap_sample = np.linspace(overlap_min, overlap_max, 100)
    density_control = kde_control(overlap_sample)
    density_treated = kde_treated(overlap_sample)
    
    # Calculate mean density in overlap
    mean_density_control = density_control.mean()
    mean_density_treated = density_treated.mean()
    
    print_and_log(f"\nDensity in Overlap Region (KDE):")
    print_and_log(f"  Mean density - Control: {mean_density_control:.4f}")
    print_and_log(f"  Mean density - Treated: {mean_density_treated:.4f}")
    print_and_log(f"  Density ratio (treated/control): {mean_density_treated/mean_density_control:.4f}")
    
except Exception as e:
    print_and_log(f"\nDensity estimation skipped: {e}")

# Assess overlap quality
overlap_quality = "Good"
overlap_warnings = []

if pct_control_in_overlap < 80:
    overlap_quality = "Poor"
    overlap_warnings.append(f"Only {pct_control_in_overlap:.1f}% of control group in overlap")
elif pct_control_in_overlap < 90:
    overlap_quality = "Moderate"
    overlap_warnings.append(f"{pct_control_in_overlap:.1f}% of control group in overlap")

if pct_treated_in_overlap < 80:
    overlap_quality = "Poor"
    overlap_warnings.append(f"Only {pct_treated_in_overlap:.1f}% of treated group in overlap")
elif pct_treated_in_overlap < 90:
    if overlap_quality == "Good":
        overlap_quality = "Moderate"
    overlap_warnings.append(f"{pct_treated_in_overlap:.1f}% of treated group in overlap")

if overlap_width < 0.1:
    overlap_quality = "Poor"
    overlap_warnings.append(f"Very narrow overlap region (width={overlap_width:.6f})")

if ext_low > len(df) * 0.05 or ext_high > len(df) * 0.05:
    if overlap_quality == "Good":
        overlap_quality = "Moderate"
    overlap_warnings.append(f"High proportion of extreme propensity scores (>5%)")

print_and_log(f"\n" + "="*80)
print_and_log(f"OVERLAP QUALITY ASSESSMENT: {overlap_quality.upper()}")
print_and_log("="*80)

if overlap_warnings:
    print_and_log("\nWarnings:")
    for warning in overlap_warnings:
        print_and_log(f"  ⚠️  {warning}")
else:
    print_and_log("\n✓ No major overlap concerns detected")

# Calculate effective sample size in overlap region
n_effective = in_overlap_control + in_overlap_treated
pct_effective = (n_effective / len(df)) * 100

print_and_log(f"\nEffective Sample Size:")
print_and_log(f"  Total observations in overlap: {n_effective:,} / {len(df):,} ({pct_effective:.2f}%)")
print_and_log(f"  This represents the sample available for causal inference")

# Save overlap analysis summary
overlap_summary = textwrap.dedent(f"""
Common Support Analysis Summary:

1. Overlap Region: [{overlap_min:.6f}, {overlap_max:.6f}] (width: {overlap_width:.6f})
2. Control group in overlap: {pct_control_in_overlap:.2f}%
3. Treated group in overlap: {pct_treated_in_overlap:.2f}%
4. Effective sample size: {n_effective:,} observations ({pct_effective:.2f}% of total)
5. Overlap Quality: {overlap_quality}
6. Warnings: {len(overlap_warnings)} issue(s) identified

Recommendations:
""")

if overlap_quality == "Poor":
    overlap_summary += "- Consider trimming sample to common support region\n"
    overlap_summary += "- May need to exclude observations with extreme propensity scores\n"
    overlap_summary += "- Consider alternative matching methods (e.g., caliper matching)\n"
elif overlap_quality == "Moderate":
    overlap_summary += "- Monitor balance after weighting/matching\n"
    overlap_summary += "- Consider sensitivity analysis\n"
else:
    overlap_summary += "- Good overlap - proceed with IPW or matching\n"

print_and_log(overlap_summary)
append_log(overlap_summary)

print("\n" + "="*80)
print("SECTION 4.8 COMPLETE: Common Support Analysis Done")
print("="*80)

# ============================================================================
# SECTION 4.9: STOP AND THINK - COMMON SUPPORT DECISION
# ============================================================================
print("\n" + "="*80)
print("4.9 STOP AND THINK: Common Support Decision")
print("="*80)

print_and_log("\n" + "="*80)
print_and_log("REVIEWING OVERLAP ASSESSMENT")
print_and_log("="*80)

# Review findings from 4.8
print_and_log(f"\nKey Findings from Overlap Analysis:")
print_and_log(f"  1. Overlap Quality: {overlap_quality}")
print_and_log(f"  2. Control group in overlap: {pct_control_in_overlap:.2f}%")
print_and_log(f"  3. Treated group in overlap: {pct_treated_in_overlap:.2f}%")
print_and_log(f"  4. Extreme propensity scores: {ext_low} (<0.01) + {ext_high} (>0.99) = {ext_low + ext_high} total")
print_and_log(f"  5. Effective sample size: {n_effective:,} observations ({pct_effective:.2f}% of total)")

# Decision logic for trimming
print_and_log("\n" + "="*80)
print_and_log("DECISION: SAMPLE TRIMMING ASSESSMENT")
print_and_log("="*80)

trim_decision = "No trimming needed"
trim_reason = ""
apply_trimming = False
n_out_overlap = 0  # Initialize for documentation

# Decision criteria
if overlap_quality == "Poor":
    trim_decision = "TRIM RECOMMENDED"
    trim_reason = "Poor overlap quality - significant portions of both groups outside overlap region"
    apply_trimming = True
elif overlap_quality == "Moderate":
    # Check if extreme scores are problematic
    pct_extreme = ((ext_low + ext_high) / len(df)) * 100
    if pct_extreme > 5:
        trim_decision = "TRIM RECOMMENDED"
        trim_reason = f"Moderate overlap with high proportion of extreme scores ({pct_extreme:.1f}%)"
        apply_trimming = True
    elif pct_control_in_overlap < 85 or pct_treated_in_overlap < 85:
        trim_decision = "TRIM RECOMMENDED"
        trim_reason = "Moderate overlap - less than 85% of one or both groups in overlap region"
        apply_trimming = True
    else:
        trim_decision = "Optional trimming"
        trim_reason = "Moderate overlap but may be acceptable - monitor balance after weighting"
        apply_trimming = False
else:
    # Good overlap
    pct_extreme = ((ext_low + ext_high) / len(df)) * 100
    if pct_extreme > 10:
        trim_decision = "Optional trimming"
        trim_reason = f"Good overlap but high proportion of extreme scores ({pct_extreme:.1f}%) - consider trimming"
        apply_trimming = False  # Don't force, but suggest
    else:
        trim_decision = "No trimming needed"
        trim_reason = "Good overlap with acceptable proportion of extreme scores"
        apply_trimming = False

print_and_log(f"\nDecision: {trim_decision}")
print_and_log(f"Reason: {trim_reason}")

# If trimming is recommended, implement it
if apply_trimming:
    print_and_log("\n" + "="*80)
    print_and_log("IMPLEMENTING SAMPLE TRIMMING TO COMMON SUPPORT")
    print_and_log("="*80)
    
    n_before_trim = len(df)
    
    # Trim to overlap region
    # Keep observations where propensity score is within overlap bounds
    trim_mask = (df["propensity_score"] >= overlap_min) & (df["propensity_score"] <= overlap_max)
    df_trimmed = df[trim_mask].copy().reset_index(drop=True)
    
    n_after_trim = len(df_trimmed)
    n_removed = n_before_trim - n_after_trim
    pct_removed = (n_removed / n_before_trim) * 100
    
    print_and_log(f"\nTrimming Results:")
    print_and_log(f"  Before trimming: {n_before_trim:,} observations")
    print_and_log(f"  After trimming: {n_after_trim:,} observations")
    print_and_log(f"  Removed: {n_removed:,} observations ({pct_removed:.2f}%)")
    
    # Check treatment group balance after trimming
    t0_trimmed = df_trimmed[df_trimmed[treatment_var] == 0]
    t1_trimmed = df_trimmed[df_trimmed[treatment_var] == 1]
    
    print_and_log(f"\nTreatment Group Balance After Trimming:")
    print_and_log(f"  Control (High Gap): {len(t0_trimmed):,} ({len(t0_trimmed)/n_after_trim*100:.1f}%)")
    print_and_log(f"  Treated (Low Gap): {len(t1_trimmed):,} ({len(t1_trimmed)/n_after_trim*100:.1f}%)")
    
    # Check if we still have adequate sample size
    min_group_size = min(len(t0_trimmed), len(t1_trimmed))
    if min_group_size < 100:
        print_and_log(f"\n⚠️  WARNING: After trimming, smallest group has only {min_group_size} observations")
        print_and_log(f"   This may be too small for reliable causal inference")
        print_and_log(f"   Consider using the untrimmed sample with IPW weights instead")
    elif min_group_size < 200:
        print_and_log(f"\n⚠️  CAUTION: After trimming, smallest group has {min_group_size} observations")
        print_and_log(f"   Sample size is adequate but on the lower end")
    else:
        print_and_log(f"\n✓ After trimming, both groups have adequate sample sizes (≥200)")
    
    # Update df to use trimmed version
    df = df_trimmed.copy()
    print_and_log(f"\n✓ Using trimmed dataset for subsequent analysis")
    
else:
    print_and_log("\n" + "="*80)
    print_and_log("NO TRIMMING APPLIED")
    print_and_log("="*80)
    print_and_log(f"\nUsing full sample ({len(df):,} observations) for analysis")
    print_and_log("Will rely on IPW weights to handle any overlap issues")
    
    # Still document what would be removed if trimming were applied
    trim_mask = (df["propensity_score"] >= overlap_min) & (df["propensity_score"] <= overlap_max)
    n_in_overlap = trim_mask.sum()
    n_out_overlap = len(df) - n_in_overlap
    print_and_log(f"\nNote: {n_out_overlap:,} observations ({n_out_overlap/len(df)*100:.1f}%) are outside overlap region")
    print_and_log("These will receive higher IPW weights, which may increase variance")

# Document decision and rationale
decision_doc = textwrap.dedent(f"""
## Task 4.9: Common Support Decision

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

### Overlap Assessment Summary:
- Overlap Quality: {overlap_quality}
- Control group in overlap: {pct_control_in_overlap:.2f}%
- Treated group in overlap: {pct_treated_in_overlap:.2f}%
- Extreme propensity scores: {ext_low + ext_high} ({((ext_low + ext_high)/len(df)*100):.2f}%)
- Overlap region: [{overlap_min:.6f}, {overlap_max:.6f}]

### Decision:
**{trim_decision}**

**Rationale:** {trim_reason}

### Implementation:
""")

if apply_trimming:
    decision_doc += f"""
- Applied trimming to common support region
- Sample size: {n_before_trim:,} → {n_after_trim:,} (removed {n_removed:,}, {pct_removed:.2f}%)
- Control group: {len(t0_trimmed):,} observations
- Treated group: {len(t1_trimmed):,} observations
- Using trimmed dataset for all subsequent analyses
"""
else:
    decision_doc += f"""
- No trimming applied
- Using full sample: {len(df):,} observations
- Will use IPW weights to handle overlap issues
- {n_out_overlap:,} observations outside overlap region will receive higher weights
"""

decision_doc += f"""

### Interpretation:
"""
if overlap_quality == "Good":
    decision_doc += """
- Good overlap indicates that for most combinations of confounder values, there are
  institutions in both treatment groups. This supports the positivity assumption.
- The propensity score distributions have substantial overlap, suggesting that
  causal inference methods (IPW, matching) should work well.
"""
elif overlap_quality == "Moderate":
    decision_doc += """
- Moderate overlap suggests some regions of confounder space where treatment
  assignment is highly predictable. This may indicate:
  * Some institutions are very unlikely to have low affordability gaps given their
    characteristics (e.g., highly selective private institutions)
  * Some institutions are very likely to have low gaps (e.g., public institutions
    serving high-Pell populations)
- IPW weights may be large for some observations, increasing variance.
- Consider sensitivity analysis to assess robustness.
"""
else:
    decision_doc += """
- Poor overlap indicates significant violations of the positivity assumption.
- Some combinations of confounder values are only observed in one treatment group.
- This limits the generalizability of causal estimates - we can only estimate
  effects for the subset of institutions in the overlap region.
- Trimming to common support is recommended to avoid extreme weights.
"""

decision_doc += f"""

### Next Steps:
- Proceed to calculate IPW weights (Task 4.10)
- Check post-weighting balance (Task 4.13)
- Monitor weight distribution for extreme values
"""

print_and_log(decision_doc)
append_log(decision_doc)

print("\n" + "="*80)
print("SECTION 4.9 COMPLETE: Common Support Decision Documented")
print("="*80)
print(f"\nDecision: {trim_decision}")
print(f"Sample size for analysis: {len(df):,} observations")
print("="*80)
