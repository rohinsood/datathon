"""
Earnings Mobility Predictor: Random Forest Regression Analysis (OPTIMIZED)
===========================================================================

This script implements four regression models to assess the importance of 
affordability gap in predicting 10-year earnings outcomes:

R1a: Core Model - Full model with affordability gap
R1b: Baseline Model - Same model without affordability gap
R1c: Interaction Model - Affordability × Pell and × URM interactions
R1d: Subgroup Models - High-Pell vs Low-Pell institutions

IMPROVEMENTS IN THIS VERSION:
-----------------------------
1. Added missingness flags (sat_missing, act_missing) to address imputation bias
2. Optimized RF hyperparameters:
   - Increased n_estimators: 200 → 500 (more trees = better predictions)
   - Increased max_depth: 20 → 25 (capture more complex patterns)
   - Decreased min_samples_split: 10 → 5 (finer splits)
   - Decreased min_samples_leaf: 5 → 2 (more granular leaves)
   - Added max_features='sqrt' (better generalization)
3. Total features: 29 → 31 (added 2 missingness indicators)

Expected Impact: Better R², lower RMSE, more robust feature importance rankings

Author: Data Science Team
Date: November 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import json
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
RANDOM_STATE = 42

print("="*100)
print("EARNINGS MOBILITY PREDICTOR: RANDOM FOREST REGRESSION ANALYSIS")
print("="*100)

# ============================================================================
# 1. LOAD DATA AND PREPARE FEATURES
# ============================================================================
print("\n" + "="*100)
print("STEP 1: DATA LOADING AND FEATURE PREPARATION")
print("="*100)

# Load analysis-ready data
df = pd.read_csv('outputs/data/analysis_ready.csv')
print(f"\nLoaded dataset: {df.shape[0]:,} observations × {df.shape[1]} columns")

# Define target variable
TARGET = 'earnings_10yr'

# Define feature sets based on your specification
AFFORDABILITY_FEATURES = [
    'Affordability Gap (net price minus income earned working 10 hrs at min wage)'  # afford_gap_cont
]

SELECTIVITY_FEATURES = [
    'admit_rate_imputed',           # admit_rate
    'sat_composite_25_imputed',     # avg_SAT
    'act_composite_25_imputed',     # avg_ACT
    'sat_missing',                  # flag: missing SAT scores
    'act_missing',                  # flag: missing ACT scores
]

RESOURCE_FEATURES = [
    'log_instructional_exp',        # instructional_exp_per_FTE (log-transformed)
    'log_endowment',                # endowment_per_student (log-transformed)
    'has_endowment',                # binary indicator
]

DEMOGRAPHIC_FEATURES = [
    'pct_pell_imputed',             # pct_pell
    'pct_urm',                      # pct_urm (Black + Latino)
    'pct_white_imputed',            # pct_white
    'pct_women_imputed',            # pct_female (women)
]

INSTITUTIONAL_FEATURES = [
    'is_hbcu', 'is_hsi', 'is_tcu', 'is_aanapisi', 'is_pbi',  # MSI_status
    'sector',                       # sector (public/private/for-profit)
    'size_category',                # size_enrollment
]

GEOGRAPHY_FEATURES = [
    'region',                       # region (South/Midwest/Northeast/West)
    # Note: 'state' has 51 categories - will use region instead for parsimony
]

# Combine all features
ALL_NUMERIC_FEATURES = (AFFORDABILITY_FEATURES + SELECTIVITY_FEATURES + 
                        RESOURCE_FEATURES + DEMOGRAPHIC_FEATURES + 
                        ['is_hbcu', 'is_hsi', 'is_tcu', 'is_aanapisi', 'is_pbi'])

# Note: SELECTIVITY_FEATURES now includes sat_missing and act_missing flags

ALL_CATEGORICAL_FEATURES = ['sector', 'size_category', 'region']

print(f"\nFeature counts:")
print(f"  Affordability: {len(AFFORDABILITY_FEATURES)}")
print(f"  Selectivity: {len(SELECTIVITY_FEATURES)}")
print(f"  Resources: {len(RESOURCE_FEATURES)}")
print(f"  Demographics: {len(DEMOGRAPHIC_FEATURES)}")
print(f"  Institutional: {len(INSTITUTIONAL_FEATURES)}")
print(f"  Geography: {len(GEOGRAPHY_FEATURES)}")
print(f"  Total numeric: {len(ALL_NUMERIC_FEATURES)}")
print(f"  Total categorical: {len(ALL_CATEGORICAL_FEATURES)}")

# Filter to complete cases for target variable
df_analysis = df[df[TARGET].notna()].copy()
print(f"\nAfter filtering for complete target: {len(df_analysis):,} observations")

# Rename affordability gap for easier reference
df_analysis['afford_gap_cont'] = df_analysis[AFFORDABILITY_FEATURES[0]]

# ============================================================================
# 2. PREPARE TRAIN/TEST SPLIT
# ============================================================================
print("\n" + "="*100)
print("STEP 2: TRAIN/TEST SPLIT")
print("="*100)

# Prepare feature matrix and target
X = df_analysis[ALL_NUMERIC_FEATURES + ALL_CATEGORICAL_FEATURES].copy()
y = df_analysis[TARGET].copy()

# Replace affordability gap column name in X
X = X.rename(columns={AFFORDABILITY_FEATURES[0]: 'afford_gap_cont'})

# Update numeric features list
ALL_NUMERIC_FEATURES_CLEAN = ['afford_gap_cont'] + [f for f in ALL_NUMERIC_FEATURES if f != AFFORDABILITY_FEATURES[0]]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE
)

print(f"Training set: {X_train.shape[0]:,} observations")
print(f"Test set: {X_test.shape[0]:,} observations")
print(f"Test set proportion: {100*X_test.shape[0]/len(df_analysis):.1f}%")

# ============================================================================
# 3. BUILD PREPROCESSING PIPELINE
# ============================================================================
print("\n" + "="*100)
print("STEP 3: BUILD PREPROCESSING PIPELINE")
print("="*100)

# Create preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), ALL_NUMERIC_FEATURES_CLEAN),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ALL_CATEGORICAL_FEATURES)
    ],
    remainder='drop'
)

print("✓ Created ColumnTransformer with StandardScaler + OneHotEncoder")

# ============================================================================
# 4. MODEL R1a: CORE MODEL (FULL MODEL WITH AFFORDABILITY)
# ============================================================================
print("\n" + "="*100)
print("MODEL R1a: CORE MODEL (FULL MODEL WITH AFFORDABILITY)")
print("="*100)

# Create pipeline
model_r1a = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(
        n_estimators=500,          # Increased from 200 for better accuracy
        max_depth=25,              # Increased from 20 for more complex patterns
        min_samples_split=5,       # Decreased from 10 for finer splits
        min_samples_leaf=2,        # Decreased from 5 to capture more patterns
        max_features='sqrt',       # Added for better generalization
        random_state=RANDOM_STATE,
        n_jobs=-1
    ))
])

print("\nTraining R1a model...")
model_r1a.fit(X_train, y_train)

# Predictions
y_train_pred_r1a = model_r1a.predict(X_train)
y_test_pred_r1a = model_r1a.predict(X_test)

# Metrics
r2_train_r1a = r2_score(y_train, y_train_pred_r1a)
r2_test_r1a = r2_score(y_test, y_test_pred_r1a)
rmse_train_r1a = np.sqrt(mean_squared_error(y_train, y_train_pred_r1a))
rmse_test_r1a = np.sqrt(mean_squared_error(y_test, y_test_pred_r1a))
mae_test_r1a = mean_absolute_error(y_test, y_test_pred_r1a)

print(f"\nR1a Performance:")
print(f"  Training R²: {r2_train_r1a:.4f}")
print(f"  Test R²:     {r2_test_r1a:.4f}")
print(f"  Test RMSE:   ${rmse_test_r1a:,.2f}")
print(f"  Test MAE:    ${mae_test_r1a:,.2f}")

# Feature importance from RF (faster than permutation)
print("\nCalculating feature importances from Random Forest...")

# Get feature importances from the trained model
rf_model = model_r1a.named_steps['regressor']
feature_importances = rf_model.feature_importances_

# Get feature names after preprocessing
cat_feature_names = model_r1a.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(ALL_CATEGORICAL_FEATURES)
feature_names_r1a = list(ALL_NUMERIC_FEATURES_CLEAN) + list(cat_feature_names)

# Create importance dataframe
importance_df_r1a = pd.DataFrame({
    'feature': feature_names_r1a,
    'importance': feature_importances
}).sort_values('importance', ascending=False)

print(f"\nTop 10 Most Important Features (R1a):")
for i, row in importance_df_r1a.head(10).iterrows():
    print(f"  {row['feature']:<40s}: {row['importance']:.6f}")

# Find affordability rank
afford_rank_r1a = importance_df_r1a[importance_df_r1a['feature'] == 'afford_gap_cont'].index[0] + 1
print(f"\n📊 AFFORDABILITY GAP RANK: #{afford_rank_r1a} out of {len(importance_df_r1a)} features")

# ============================================================================
# 5. MODEL R1b: BASELINE (NO AFFORDABILITY)
# ============================================================================
print("\n" + "="*100)
print("MODEL R1b: BASELINE (NO AFFORDABILITY)")
print("="*100)

# Features without affordability
features_no_afford = [f for f in ALL_NUMERIC_FEATURES_CLEAN if f != 'afford_gap_cont'] + ALL_CATEGORICAL_FEATURES
X_train_no_afford = X_train[features_no_afford]
X_test_no_afford = X_test[features_no_afford]

# Preprocessor without affordability
numeric_features_no_afford = [f for f in ALL_NUMERIC_FEATURES_CLEAN if f != 'afford_gap_cont']
preprocessor_no_afford = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features_no_afford),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ALL_CATEGORICAL_FEATURES)
    ],
    remainder='drop'
)

# Create pipeline
model_r1b = Pipeline([
    ('preprocessor', preprocessor_no_afford),
    ('regressor', RandomForestRegressor(
        n_estimators=500,          # Increased from 200 for better accuracy
        max_depth=25,              # Increased from 20 for more complex patterns
        min_samples_split=5,       # Decreased from 10 for finer splits
        min_samples_leaf=2,        # Decreased from 5 to capture more patterns
        max_features='sqrt',       # Added for better generalization
        random_state=RANDOM_STATE,
        n_jobs=-1
    ))
])

print("\nTraining R1b model (without affordability)...")
model_r1b.fit(X_train_no_afford, y_train)

# Predictions
y_test_pred_r1b = model_r1b.predict(X_test_no_afford)

# Metrics
r2_test_r1b = r2_score(y_test, y_test_pred_r1b)
rmse_test_r1b = np.sqrt(mean_squared_error(y_test, y_test_pred_r1b))

print(f"\nR1b Performance:")
print(f"  Test R²:     {r2_test_r1b:.4f}")
print(f"  Test RMSE:   ${rmse_test_r1b:,.2f}")

# Compare models
delta_r2 = r2_test_r1a - r2_test_r1b
delta_rmse = rmse_test_r1b - rmse_test_r1a
pct_improvement_r2 = 100 * delta_r2 / r2_test_r1b if r2_test_r1b != 0 else 0

print(f"\n📊 AFFORDABILITY CONTRIBUTION:")
print(f"  ΔR²:   {delta_r2:+.4f} ({pct_improvement_r2:+.2f}% improvement)")
print(f"  ΔRMSE: ${delta_rmse:+,.2f} (positive = affordability reduces error)")

if delta_r2 > 0:
    print(f"\n✓ Adding affordability improves explanatory power by {pct_improvement_r2:.2f}%")
else:
    print(f"\n⚠ Affordability does not improve model performance")

# ============================================================================
# 6. MODEL R1c: INTERACTION MODEL
# ============================================================================
print("\n" + "="*100)
print("MODEL R1c: INTERACTION MODEL (AFFORDABILITY × PELL & × URM)")
print("="*100)

# Create interaction features
print("\nCreating interaction features...")
df_analysis['afford_x_pell'] = df_analysis['afford_gap_cont'] * df_analysis['pct_pell_imputed']
df_analysis['afford_x_urm'] = df_analysis['afford_gap_cont'] * df_analysis['pct_urm']

# Add to feature set
interaction_features = ['afford_x_pell', 'afford_x_urm']
all_features_with_interactions = ALL_NUMERIC_FEATURES_CLEAN + interaction_features + ALL_CATEGORICAL_FEATURES

# Prepare data
X_interact = df_analysis[all_features_with_interactions].copy()
y_interact = df_analysis[TARGET].copy()

# Split
X_train_int, X_test_int, y_train_int, y_test_int = train_test_split(
    X_interact, y_interact, test_size=0.2, random_state=RANDOM_STATE
)

# Preprocessor with interactions
numeric_features_with_int = ALL_NUMERIC_FEATURES_CLEAN + interaction_features
preprocessor_int = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features_with_int),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ALL_CATEGORICAL_FEATURES)
    ],
    remainder='drop'
)

# Create pipeline
model_r1c = Pipeline([
    ('preprocessor', preprocessor_int),
    ('regressor', RandomForestRegressor(
        n_estimators=500,          # Increased from 200 for better accuracy
        max_depth=25,              # Increased from 20 for more complex patterns
        min_samples_split=5,       # Decreased from 10 for finer splits
        min_samples_leaf=2,        # Decreased from 5 to capture more patterns
        max_features='sqrt',       # Added for better generalization
        random_state=RANDOM_STATE,
        n_jobs=-1
    ))
])

print("Training R1c model (with interactions)...")
model_r1c.fit(X_train_int, y_train_int)

# Predictions
y_test_pred_r1c = model_r1c.predict(X_test_int)

# Metrics
r2_test_r1c = r2_score(y_test_int, y_test_pred_r1c)
rmse_test_r1c = np.sqrt(mean_squared_error(y_test_int, y_test_pred_r1c))

print(f"\nR1c Performance:")
print(f"  Test R²:     {r2_test_r1c:.4f}")
print(f"  Test RMSE:   ${rmse_test_r1c:,.2f}")

# Feature importance for interactions
print("\nCalculating feature importances for interaction model...")

# Get feature importances
rf_model_r1c = model_r1c.named_steps['regressor']
feature_importances_r1c = rf_model_r1c.feature_importances_

# Get feature names
cat_feature_names_r1c = model_r1c.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(ALL_CATEGORICAL_FEATURES)
feature_names_r1c = numeric_features_with_int + list(cat_feature_names_r1c)

# Create importance dataframe
importance_df_r1c = pd.DataFrame({
    'feature': feature_names_r1c,
    'importance': feature_importances_r1c
}).sort_values('importance', ascending=False)

print(f"\nInteraction Feature Importance (R1c):")
interaction_features_check = ['afford_gap_cont', 'afford_x_pell', 'afford_x_urm']
for feat in interaction_features_check:
    if feat in importance_df_r1c['feature'].values:
        row = importance_df_r1c[importance_df_r1c['feature'] == feat].iloc[0]
        rank = importance_df_r1c[importance_df_r1c['feature'] == feat].index[0] + 1
        print(f"  #{rank:2d} {feat:<25s}: {row['importance']:.6f}")

# ============================================================================
# 7. MODEL R1d: SUBGROUP MODELS (HIGH-PELL VS LOW-PELL)
# ============================================================================
print("\n" + "="*100)
print("MODEL R1d: SUBGROUP ANALYSIS (HIGH-PELL VS LOW-PELL)")
print("="*100)

# Define subgroups
pell_median = df_analysis['pct_pell_imputed'].median()
print(f"\nMedian Pell %: {pell_median:.1f}%")

df_high_pell = df_analysis[df_analysis['pct_pell_imputed'] >= pell_median].copy()
df_low_pell = df_analysis[df_analysis['pct_pell_imputed'] < pell_median].copy()

print(f"High-Pell institutions: {len(df_high_pell):,}")
print(f"Low-Pell institutions:  {len(df_low_pell):,}")

# Function to train subgroup model
def train_subgroup_model(df_sub, subgroup_name):
    print(f"\n--- {subgroup_name} Model ---")
    
    X_sub = df_sub[ALL_NUMERIC_FEATURES_CLEAN + ALL_CATEGORICAL_FEATURES]
    y_sub = df_sub[TARGET]
    
    # Split
    X_train_sub, X_test_sub, y_train_sub, y_test_sub = train_test_split(
        X_sub, y_sub, test_size=0.2, random_state=RANDOM_STATE
    )
    
    print(f"Training set: {len(X_train_sub):,} | Test set: {len(X_test_sub):,}")
    
    # Create pipeline
    model_sub = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(
            n_estimators=200,
            max_depth=20,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=RANDOM_STATE,
            n_jobs=-1
        ))
    ])
    
    # Train
    model_sub.fit(X_train_sub, y_train_sub)
    
    # Predict
    y_test_pred_sub = model_sub.predict(X_test_sub)
    
    # Metrics
    r2_sub = r2_score(y_test_sub, y_test_pred_sub)
    rmse_sub = np.sqrt(mean_squared_error(y_test_sub, y_test_pred_sub))
    
    print(f"Test R²:   {r2_sub:.4f}")
    print(f"Test RMSE: ${rmse_sub:,.2f}")
    
    # Feature importance
    print("Calculating feature importances...")
    rf_model_sub = model_sub.named_steps['regressor']
    feat_imp_sub = rf_model_sub.feature_importances_
    
    # Feature names
    cat_names_sub = model_sub.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(ALL_CATEGORICAL_FEATURES)
    feat_names_sub = list(ALL_NUMERIC_FEATURES_CLEAN) + list(cat_names_sub)
    
    # Importance dataframe
    imp_df_sub = pd.DataFrame({
        'feature': feat_names_sub,
        'importance': feat_imp_sub
    }).sort_values('importance', ascending=False)
    
    # Find affordability rank
    afford_rank = imp_df_sub[imp_df_sub['feature'] == 'afford_gap_cont'].index[0] + 1
    afford_imp = imp_df_sub[imp_df_sub['feature'] == 'afford_gap_cont'].iloc[0]['importance']
    
    print(f"\n📊 Affordability Gap Rank: #{afford_rank}")
    print(f"   Importance: {afford_imp:.6f}")
    
    print(f"\nTop 5 Features:")
    for i, row in imp_df_sub.head(5).iterrows():
        print(f"  #{i+1:2d} {row['feature']:<30s}: {row['importance']:.6f}")
    
    return {
        'model': model_sub,
        'r2': r2_sub,
        'rmse': rmse_sub,
        'importance_df': imp_df_sub,
        'afford_rank': afford_rank,
        'afford_importance': afford_imp
    }

# Train subgroup models
results_high_pell = train_subgroup_model(df_high_pell, "HIGH-PELL")
results_low_pell = train_subgroup_model(df_low_pell, "LOW-PELL")

# Compare subgroups
print("\n" + "="*100)
print("SUBGROUP COMPARISON")
print("="*100)
print(f"\nAffordability Gap Importance:")
print(f"  High-Pell: Rank #{results_high_pell['afford_rank']:2d} | Importance: {results_high_pell['afford_importance']:.6f}")
print(f"  Low-Pell:  Rank #{results_low_pell['afford_rank']:2d} | Importance: {results_low_pell['afford_importance']:.6f}")

if results_high_pell['afford_rank'] < results_low_pell['afford_rank']:
    print(f"\n✓ Affordability is MORE important for high-Pell institutions")
    print(f"  (Rank {results_high_pell['afford_rank']} vs {results_low_pell['afford_rank']})")
else:
    print(f"\n⚠ Affordability is MORE important for low-Pell institutions")
    print(f"  (Rank {results_low_pell['afford_rank']} vs {results_high_pell['afford_rank']})")

# ============================================================================
# 8. SAVE RESULTS
# ============================================================================
print("\n" + "="*100)
print("SAVING RESULTS")
print("="*100)

# Create output directory
import os
os.makedirs('outputs/rf_analysis', exist_ok=True)

# Save model performance summary
model_summary = pd.DataFrame({
    'Model': ['R1a_Full', 'R1b_No_Afford', 'R1c_Interactions', 'R1d_High_Pell', 'R1d_Low_Pell'],
    'R2_Test': [r2_test_r1a, r2_test_r1b, r2_test_r1c, 
                results_high_pell['r2'], results_low_pell['r2']],
    'RMSE_Test': [rmse_test_r1a, rmse_test_r1b, rmse_test_r1c,
                  results_high_pell['rmse'], results_low_pell['rmse']],
    'Afford_Rank': [afford_rank_r1a, np.nan, np.nan,
                    results_high_pell['afford_rank'], results_low_pell['afford_rank']]
})
model_summary.to_csv('outputs/rf_analysis/model_summary.csv', index=False)
print("✓ Saved: outputs/rf_analysis/model_summary.csv")

# Save feature importance (R1a)
importance_df_r1a.to_csv('outputs/rf_analysis/feature_importance_r1a.csv', index=False)
print("✓ Saved: outputs/rf_analysis/feature_importance_r1a.csv")

# Save feature importance (R1c - with interactions)
importance_df_r1c.to_csv('outputs/rf_analysis/feature_importance_r1c.csv', index=False)
print("✓ Saved: outputs/rf_analysis/feature_importance_r1c.csv")

# Save subgroup importance
results_high_pell['importance_df'].to_csv('outputs/rf_analysis/feature_importance_high_pell.csv', index=False)
results_low_pell['importance_df'].to_csv('outputs/rf_analysis/feature_importance_low_pell.csv', index=False)
print("✓ Saved: outputs/rf_analysis/feature_importance_high_pell.csv")
print("✓ Saved: outputs/rf_analysis/feature_importance_low_pell.csv")

# ============================================================================
# 9. SAVE TRAINED MODELS
# ============================================================================
print("\n" + "="*100)
print("SAVING TRAINED MODELS")
print("="*100)

# Create models directory
os.makedirs('outputs/rf_analysis/models', exist_ok=True)

# Save R1a (Full Model)
joblib.dump(model_r1a, 'outputs/rf_analysis/models/model_r1a_full.pkl')
print("✓ Saved: outputs/rf_analysis/models/model_r1a_full.pkl")

# Save R1b (No Affordability)
joblib.dump(model_r1b, 'outputs/rf_analysis/models/model_r1b_no_afford.pkl')
print("✓ Saved: outputs/rf_analysis/models/model_r1b_no_afford.pkl")

# Save R1c (Interactions)
joblib.dump(model_r1c, 'outputs/rf_analysis/models/model_r1c_interactions.pkl')
print("✓ Saved: outputs/rf_analysis/models/model_r1c_interactions.pkl")

# Save R1d High-Pell subgroup model
joblib.dump(results_high_pell['model'], 'outputs/rf_analysis/models/model_r1d_high_pell.pkl')
print("✓ Saved: outputs/rf_analysis/models/model_r1d_high_pell.pkl")

# Save R1d Low-Pell subgroup model
joblib.dump(results_low_pell['model'], 'outputs/rf_analysis/models/model_r1d_low_pell.pkl')
print("✓ Saved: outputs/rf_analysis/models/model_r1d_low_pell.pkl")

# Save feature lists and metadata for future use
model_metadata = {
    'random_state': RANDOM_STATE,
    'target_variable': TARGET,
    'numeric_features': ALL_NUMERIC_FEATURES_CLEAN,
    'categorical_features': ALL_CATEGORICAL_FEATURES,
    'affordability_feature': 'afford_gap_cont',
    'median_pell_threshold': pell_median,
    'test_set_proportion': 0.2,
    'n_estimators': 500,
    'max_depth': 25,
    'training_date': '2025-11-15',
    'model_descriptions': {
        'R1a': 'Full model with all features including affordability gap',
        'R1b': 'Baseline model without affordability gap',
        'R1c': 'Model with affordability × Pell and affordability × URM interactions',
        'R1d_high': 'Subgroup model for high-Pell institutions (≥median)',
        'R1d_low': 'Subgroup model for low-Pell institutions (<median)'
    }
}

with open('outputs/rf_analysis/models/model_metadata.json', 'w') as f:
    json.dump(model_metadata, f, indent=2)
print("✓ Saved: outputs/rf_analysis/models/model_metadata.json")

print("\n💾 All 5 models saved successfully!")
print(f"   Total model size: ~{(os.path.getsize('outputs/rf_analysis/models/model_r1a_full.pkl') * 5 / 1024 / 1024):.1f} MB")

print("\n" + "="*100)
print("✓ EARNINGS MOBILITY RF ANALYSIS COMPLETE")
print("="*100)

print("\n📊 KEY FINDINGS:")
print(f"1. Full model (R1a) R²: {r2_test_r1a:.4f}")
print(f"2. Affordability adds {pct_improvement_r2:+.2f}% explanatory power")
print(f"3. Affordability ranks #{afford_rank_r1a} in importance")
print(f"4. In high-Pell institutions: Rank #{results_high_pell['afford_rank']}")
print(f"5. In low-Pell institutions: Rank #{results_low_pell['afford_rank']}")

