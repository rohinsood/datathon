"""
Causal Inference Script: Affordability Gap and Economic Mobility Analysis
This script implements multiple causal inference methods (PSM, DR, DoWhy, OLS) to estimate
the causal effect of affordability gaps on student outcomes.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings
warnings.filterwarnings('ignore')

# Causal inference libraries
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.stats.weightstats import DescrStatsW
from scipy import stats
from scipy.stats import bootstrap

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

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 50)

print("="*80)
print("TASK 4.0: IMPLEMENT CORE CAUSAL INFERENCE METHODS")
print("="*80)

# ============================================================================
# SECTION 4.1: SETUP CAUSAL ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("SECTION 4.1: SETUP CAUSAL ANALYSIS")
print("="*80)

# Load analysis-ready dataset
print("\nLoading analysis-ready dataset...")
df = pd.read_csv('outputs/data/analysis_ready.csv')

# Load variable lists
print("Loading variable lists...")
with open('outputs/data/variable_lists.json', 'r') as f:
    variable_lists = json.load(f)

# Extract variable lists
treatment_var = variable_lists['treatment']
outcome_vars = variable_lists['outcomes']
confounder_vars = variable_lists['confounders']
categorical_vars = variable_lists['categorical']

print("\n" + "="*80)
print("VARIABLE DEFINITIONS")
print("="*80)
print(f"\nTreatment Variable: {treatment_var}")
print(f"\nOutcome Variables: {outcome_vars}")
print(f"\nNumber of Confounders: {len(confounder_vars)}")
print(f"Confounders: {confounder_vars}")
print(f"\nCategorical Variables: {categorical_vars}")

# Verify all variables exist in dataset
print("\n" + "="*80)
print("VERIFYING VARIABLES IN DATASET")
print("="*80)

missing_vars = []
for var in [treatment_var] + outcome_vars + confounder_vars:
    if var not in df.columns:
        missing_vars.append(var)
        print(f"  WARNING: {var} not found in dataset!")

missing_categorical = []
for var in categorical_vars:
    if var not in df.columns:
        missing_categorical.append(var)
        print(f"  WARNING: {var} not found in dataset!")

if missing_vars or missing_categorical:
    print(f"\nERROR: {len(missing_vars)} variables missing from dataset!")
    print("Please check variable_lists.json and ensure all variables were created in feature engineering.")
else:
    print("\n✓ All variables found in dataset!")

# Print dataset summary
print("\n" + "="*80)
print("DATASET SUMMARY")
print("="*80)
print(f"\nDataset Shape: {df.shape}")
print(f"Number of observations: {df.shape[0]:,}")
print(f"Number of variables: {df.shape[1]}")

# Check treatment group sizes
print(f"\nTreatment Group Distribution:")
print(df[treatment_var].value_counts().sort_index())
print(f"\nTreatment Group Percentages:")
print(df[treatment_var].value_counts(normalize=True).sort_index() * 100)

# Check for missing values in key variables
print(f"\nMissing Values Check:")
print(f"  Treatment ({treatment_var}): {df[treatment_var].isna().sum()} missing")
for outcome in outcome_vars:
    print(f"  Outcome ({outcome}): {df[outcome].isna().sum()} missing")

print("\n" + "="*80)
print("SETUP COMPLETE - READY FOR CAUSAL ANALYSIS")
print("="*80)

# ============================================================================
# SECTION 4.4: PROPENSITY SCORE MODEL
# ============================================================================
print("\n" + "="*80)
print("SECTION 4.4: PROPENSITY SCORE MODEL")
print("="*80)

# Prepare data for propensity score model
print("\nPreparing data for propensity score estimation...")

# Create a working copy of the data
df_psm = df.copy()

# Extract treatment variable
treatment = df_psm[treatment_var].values

# Prepare confounders: continuous + dummy variables for categorical
print("\nCreating dummy variables for categorical confounders...")

# Get continuous confounders (already numeric)
X_continuous = df_psm[confounder_vars].copy()

# Ensure all continuous confounders are numeric
for col in X_continuous.columns:
    X_continuous[col] = pd.to_numeric(X_continuous[col], errors='coerce')

# Create dummy variables for categorical confounders
X_categorical_dummies = pd.get_dummies(
    df_psm[categorical_vars], 
    prefix=categorical_vars,
    drop_first=True,  # Drop first category to avoid multicollinearity
    dummy_na=False
)

# Combine all confounders
X_all = pd.concat([X_continuous, X_categorical_dummies], axis=1)

# Ensure all columns are numeric (convert any remaining object types)
for col in X_all.columns:
    if X_all[col].dtype == 'object':
        X_all[col] = pd.to_numeric(X_all[col], errors='coerce')

print(f"\nTotal number of confounder features: {X_all.shape[1]}")
print(f"  - Continuous confounders: {len(confounder_vars)}")
print(f"  - Categorical dummy variables: {X_categorical_dummies.shape[1]}")

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
    X_all = X_all[valid_mask].reset_index(drop=True)
    treatment = treatment[valid_mask]
    df_psm = df_psm[valid_mask].reset_index(drop=True)
    print(f"Remaining observations: {len(X_all):,}")
else:
    print("\n✓ No missing or infinite values in confounders")

# Convert to numpy array for statsmodels (ensure float64)
X_all = X_all.astype(float)

# Fit logistic regression model for propensity scores
print("\n" + "="*80)
print("FITTING PROPENSITY SCORE MODEL")
print("="*80)
print("\nModel specification: Treatment ~ All Confounders")
print(f"Sample size: {len(treatment):,}")
print(f"Number of features: {X_all.shape[1]}")

# Fit logistic regression using statsmodels for detailed output
X_with_const = sm.add_constant(X_all)
psm_model = sm.Logit(treatment, X_with_const)
psm_result = psm_model.fit(method='bfgs', maxiter=1000, disp=0)

print("\n" + "="*80)
print("PROPENSITY SCORE MODEL SUMMARY")
print("="*80)
print(psm_result.summary())

# Generate predicted propensity scores
propensity_scores = psm_result.predict(X_with_const)

# Add propensity scores to dataframe
df_psm['propensity_score'] = propensity_scores

print("\n" + "="*80)
print("PROPENSITY SCORE DISTRIBUTION")
print("="*80)
print(f"\nPropensity Score Statistics:")
print(f"  Mean: {propensity_scores.mean():.4f}")
print(f"  Median: {propensity_scores.median():.4f}")
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
    print("\n✓ No extreme propensity scores detected. Good overlap expected.")

print("\n" + "="*80)
print("PROPENSITY SCORE MODEL COMPLETE")
print("="*80)

