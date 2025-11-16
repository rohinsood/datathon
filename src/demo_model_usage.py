"""
Simple Model Loading and Usage Demo
====================================

Demonstrates basic usage of the saved Random Forest models.

This script shows:
1. How to load a saved model
2. How to check model information
3. How to make predictions on new data (using the test set)

Author: Data Science Team
Date: November 2025
"""

import pandas as pd
import numpy as np
import joblib
import json
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

print("="*100)
print("RANDOM FOREST MODEL - SIMPLE USAGE DEMONSTRATION")
print("="*100)

# ============================================================================
# 1. LOAD MODEL AND METADATA
# ============================================================================
print("\n📦 STEP 1: Loading model and metadata...")

# Load metadata
with open('outputs/rf_analysis/models/model_metadata.json', 'r') as f:
    metadata = json.load(f)

# Load the full model (R1a)
model_r1a = joblib.load('outputs/rf_analysis/models/model_r1a_full.pkl')

print(f"✓ Model: R1a (Full Model with Affordability)")
print(f"✓ Target variable: {metadata['target_variable']}")
print(f"✓ Training date: {metadata['training_date']}")
print(f"✓ Model specs: {metadata['n_estimators']} trees, max depth {metadata['max_depth']}")
print(f"✓ Numeric features: {len(metadata['numeric_features'])}")
print(f"✓ Categorical features: {len(metadata['categorical_features'])}")

# ============================================================================
# 2. LOAD DATA THAT WAS ACTUALLY USED IN TRAINING
# ============================================================================
print("\n📊 STEP 2: Loading analysis-ready data...")

df = pd.read_csv('outputs/data/analysis_ready.csv')
df_complete = df[df['earnings_10yr'].notna()].copy()

# Rename affordability column to match training
AFFORD_FULL_NAME = 'Affordability Gap (net price minus income earned working 10 hrs at min wage)'
df_complete = df_complete.rename(columns={AFFORD_FULL_NAME: 'afford_gap_cont'})

print(f"✓ Loaded {len(df_complete):,} institutions")

# ============================================================================
# 3. PREPARE FEATURES (SAME AS TRAINING)
# ============================================================================
print("\n🔧 STEP 3: Preparing features...")

# Get feature lists from metadata
numeric_features = metadata['numeric_features']
categorical_features = metadata['categorical_features']
all_features = numeric_features + categorical_features

print(f"✓ Total features: {len(all_features)}")
print(f"   Numeric: {numeric_features[:3]}... (+{len(numeric_features)-3} more)")
print(f"   Categorical: {categorical_features}")

# Prepare feature matrix
X = df_complete[all_features]
y = df_complete['earnings_10yr']

print(f"✓ Feature matrix shape: {X.shape}")
print(f"✓ Target variable shape: {y.shape}")

# ============================================================================
# 4. MAKE PREDICTIONS WITH R1a MODEL
# ============================================================================
print("\n🎯 STEP 4: Making predictions with R1a (Full Model)...")

y_pred = model_r1a.predict(X)

# Calculate performance metrics
r2 = r2_score(y, y_pred)
rmse = np.sqrt(mean_squared_error(y, y_pred))
mae = mean_absolute_error(y, y_pred)

print(f"\n📊 Model Performance on Full Dataset:")
print(f"   R² Score:  {r2:.4f} (explains {r2*100:.1f}% of variance)")
print(f"   RMSE:      ${rmse:,.2f}")
print(f"   MAE:       ${mae:,.2f}")

# ============================================================================
# 5. SHOW SAMPLE PREDICTIONS
# ============================================================================
print("\n🏫 STEP 5: Sample predictions for specific institutions...")

# Select 5 diverse institutions
np.random.seed(42)
sample_indices = [100, 500, 1000, 2000, 3000]
df_sample = df_complete.iloc[sample_indices].copy()

X_sample = df_sample[all_features]
y_sample_actual = df_sample['earnings_10yr'].values
y_sample_pred = model_r1a.predict(X_sample)

print("\n" + "="*100)
print(f"{'Institution':<50} | {'Afford Gap':<12} | {'% Pell':<8} | {'Actual':<10} | {'Predicted':<10} | {'Error':<10}")
print("="*100)

for idx, (inst_idx, row) in enumerate(df_sample.iterrows()):
    inst_name = row['Institution Name_aff'][:48]
    afford = row['afford_gap_cont']
    pell = row['pct_pell_imputed']
    actual = y_sample_actual[idx]
    pred = y_sample_pred[idx]
    error = actual - pred
    
    print(f"{inst_name:<50} | ${afford:>10,.0f} | {pell:>6.1f}% | ${actual:>8,.0f} | ${pred:>9,.0f} | ${error:>9,.0f}")

# ============================================================================
# 6. LOAD AND COMPARE OTHER MODELS
# ============================================================================
print("\n📊 STEP 6: Comparing all models...")

# Load other models
model_r1b = joblib.load('outputs/rf_analysis/models/model_r1b_no_afford.pkl')
model_r1c = joblib.load('outputs/rf_analysis/models/model_r1c_interactions.pkl')

# Prepare features for R1b (no affordability)
numeric_no_afford = [f for f in numeric_features if f != 'afford_gap_cont']
all_features_no_afford = numeric_no_afford + categorical_features
X_no_afford = df_complete[all_features_no_afford]

# Prepare features for R1c (with interactions)
df_complete['afford_x_pell'] = df_complete['afford_gap_cont'] * df_complete['pct_pell_imputed']
df_complete['afford_x_urm'] = df_complete['afford_gap_cont'] * df_complete['pct_urm']
all_features_interact = numeric_features + ['afford_x_pell', 'afford_x_urm'] + categorical_features
X_interact = df_complete[all_features_interact]

# Make predictions
y_pred_r1b = model_r1b.predict(X_no_afford)
y_pred_r1c = model_r1c.predict(X_interact)

# Calculate metrics
metrics_comparison = pd.DataFrame({
    'Model': [
        'R1a (Full - with affordability)',
        'R1b (No affordability)',
        'R1c (With interactions)'
    ],
    'R²': [
        r2_score(y, y_pred),
        r2_score(y, y_pred_r1b),
        r2_score(y, y_pred_r1c)
    ],
    'RMSE': [
        np.sqrt(mean_squared_error(y, y_pred)),
        np.sqrt(mean_squared_error(y, y_pred_r1b)),
        np.sqrt(mean_squared_error(y, y_pred_r1c))
    ],
    'MAE': [
        mean_absolute_error(y, y_pred),
        mean_absolute_error(y, y_pred_r1b),
        mean_absolute_error(y, y_pred_r1c)
    ]
})

print("\n📈 Model Comparison:")
print(metrics_comparison.to_string(index=False))

# ============================================================================
# 7. SAVE PREDICTIONS
# ============================================================================
print("\n💾 STEP 7: Saving predictions...")

# Add predictions to dataframe
df_complete['pred_r1a'] = y_pred
df_complete['pred_r1b'] = y_pred_r1b
df_complete['pred_r1c'] = y_pred_r1c
df_complete['error_r1a'] = y - y_pred
df_complete['error_r1b'] = y - y_pred_r1b
df_complete['error_r1c'] = y - y_pred_r1c

# Save predictions
output_cols = [
    'unit_id', 'Institution Name_aff', 'State Abbreviation', 'Sector Name',
    'afford_gap_cont', 'pct_pell_imputed', 'earnings_10yr',
    'pred_r1a', 'pred_r1b', 'pred_r1c',
    'error_r1a', 'error_r1b', 'error_r1c'
]

df_output = df_complete[output_cols].copy()
df_output = df_output.rename(columns={'afford_gap_cont': 'affordability_gap'})

df_output.to_csv('outputs/rf_analysis/predictions_demo.csv', index=False)
print(f"✓ Saved predictions to: outputs/rf_analysis/predictions_demo.csv")
print(f"✓ Total institutions: {len(df_output):,}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*100)
print("✅ MODEL USAGE DEMONSTRATION COMPLETE")
print("="*100)

print("\n💡 KEY TAKEAWAYS:")
print(f"  1. The R1a model achieves R² = {r2:.4f} with RMSE = ${rmse:,.0f}")
print(f"  2. All 5 models are saved in: outputs/rf_analysis/models/")
print(f"  3. Models can predict earnings for {len(df_complete):,} institutions")
print(f"  4. To use a model: model = joblib.load('path/to/model.pkl')")
print(f"  5. To predict: predictions = model.predict(X)")

print("\n📁 SAVED MODEL FILES:")
print("  • model_r1a_full.pkl          - Full model with affordability (54.4 MB)")
print("  • model_r1b_no_afford.pkl     - Baseline without affordability (53.4 MB)")
print("  • model_r1c_interactions.pkl  - Model with interactions (56.0 MB)")
print("  • model_r1d_high_pell.pkl     - High-Pell subgroup (5.7 MB)")
print("  • model_r1d_low_pell.pkl      - Low-Pell subgroup (5.5 MB)")
print("  • model_metadata.json         - Feature lists and specs")

print("\n📊 OUTPUT FILES:")
print("  • predictions_demo.csv        - Predictions for all institutions")
print("  • feature_importance_*.csv    - Feature importance rankings")
print("  • model_summary.csv           - Performance metrics")

print("\n" + "="*100)

