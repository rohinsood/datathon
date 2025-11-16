"""
Load Saved Models and Make Predictions
=======================================

This script demonstrates how to:
1. Load the trained Random Forest models
2. Load new institution data
3. Make earnings predictions
4. Compare predictions across different models

Usage:
    python src/load_and_predict.py

Author: Data Science Team
Date: November 2025
"""

import pandas as pd
import numpy as np
import joblib
import json
import os

print("="*100)
print("LOADING TRAINED MODELS FOR PREDICTIONS")
print("="*100)

# ============================================================================
# 1. LOAD MODEL METADATA
# ============================================================================
print("\n1. Loading model metadata...")
with open('outputs/rf_analysis/models/model_metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"✓ Models trained on: {metadata['training_date']}")
print(f"✓ Target variable: {metadata['target_variable']}")
print(f"✓ Number of features: {len(metadata['numeric_features']) + len(metadata['categorical_features'])}")
print(f"✓ Median Pell threshold: {metadata['median_pell_threshold']:.1f}%")

# ============================================================================
# 2. LOAD ALL TRAINED MODELS
# ============================================================================
print("\n2. Loading trained models...")

models = {}
model_files = {
    'R1a (Full)': 'outputs/rf_analysis/models/model_r1a_full.pkl',
    'R1b (No Afford)': 'outputs/rf_analysis/models/model_r1b_no_afford.pkl',
    'R1c (Interactions)': 'outputs/rf_analysis/models/model_r1c_interactions.pkl',
    'R1d (High-Pell)': 'outputs/rf_analysis/models/model_r1d_high_pell.pkl',
    'R1d (Low-Pell)': 'outputs/rf_analysis/models/model_r1d_low_pell.pkl'
}

for name, filepath in model_files.items():
    models[name] = joblib.load(filepath)
    file_size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"✓ Loaded: {name:<20} ({file_size_mb:.1f} MB)")

print(f"\n💾 Total models loaded: {len(models)}")

# ============================================================================
# 3. LOAD DATA FOR PREDICTIONS
# ============================================================================
print("\n3. Loading data for predictions...")
df = pd.read_csv('outputs/data/analysis_ready.csv')

# Filter for complete earnings data
df_complete = df[df['earnings_10yr'].notna()].copy()

print(f"✓ Loaded {len(df_complete):,} institutions with complete earnings data")

# Rename affordability gap column for consistency with training
AFFORD_FULL_NAME = 'Affordability Gap (net price minus income earned working 10 hrs at min wage)'
df_complete = df_complete.rename(columns={AFFORD_FULL_NAME: 'afford_gap_cont'})

# Prepare features for R1a model (most comprehensive)
numeric_features = metadata['numeric_features']
categorical_features = metadata['categorical_features']
all_features = numeric_features + categorical_features

# For R1b (no affordability), remove the affordability feature
numeric_features_no_afford = [f for f in numeric_features if f != metadata['affordability_feature']]
all_features_no_afford = numeric_features_no_afford + categorical_features

# For R1c (interactions), add interaction terms
df_complete['afford_x_pell'] = (
    df_complete['afford_gap_cont'] * 
    df_complete['pct_pell_imputed']
)
df_complete['afford_x_urm'] = (
    df_complete['afford_gap_cont'] * 
    df_complete['pct_urm']
)
all_features_interactions = numeric_features + ['afford_x_pell', 'afford_x_urm'] + categorical_features

# ============================================================================
# 4. MAKE PREDICTIONS ON SAMPLE INSTITUTIONS
# ============================================================================
print("\n4. Making predictions on sample institutions...")

# Select a diverse sample of institutions
np.random.seed(42)
sample_indices = np.random.choice(df_complete.index, size=10, replace=False)
df_sample = df_complete.loc[sample_indices].copy()

# Make predictions with each model
predictions = pd.DataFrame()
predictions['Institution'] = df_sample['Institution Name_aff'].values
predictions['Actual_Earnings'] = df_sample['earnings_10yr'].values
predictions['Affordability_Gap'] = df_sample['afford_gap_cont'].values
predictions['Pct_Pell'] = df_sample['pct_pell_imputed'].values

# R1a predictions (Full model)
X_r1a = df_sample[all_features]
predictions['Pred_R1a_Full'] = models['R1a (Full)'].predict(X_r1a)

# R1b predictions (No Affordability)
X_r1b = df_sample[all_features_no_afford]
predictions['Pred_R1b_NoAfford'] = models['R1b (No Afford)'].predict(X_r1b)

# R1c predictions (Interactions)
X_r1c = df_sample[all_features_interactions]
predictions['Pred_R1c_Interactions'] = models['R1c (Interactions)'].predict(X_r1c)

# Calculate prediction errors
predictions['Error_R1a'] = predictions['Actual_Earnings'] - predictions['Pred_R1a_Full']
predictions['Error_R1b'] = predictions['Actual_Earnings'] - predictions['Pred_R1b_NoAfford']
predictions['Error_R1c'] = predictions['Actual_Earnings'] - predictions['Pred_R1c_Interactions']

print("\n✓ Sample Institution Predictions:")
print("="*100)

# Display results
for idx, row in predictions.iterrows():
    print(f"\n{row['Institution'][:60]}")
    print(f"  Actual Earnings:      ${row['Actual_Earnings']:>6,.0f}")
    print(f"  Affordability Gap:    ${row['Affordability_Gap']:>6,.0f}")
    print(f"  % Pell:               {row['Pct_Pell']:>6.1f}%")
    print(f"  ---")
    print(f"  Pred (R1a Full):      ${row['Pred_R1a_Full']:>6,.0f}  (Error: ${row['Error_R1a']:>6,.0f})")
    print(f"  Pred (R1b NoAfford):  ${row['Pred_R1b_NoAfford']:>6,.0f}  (Error: ${row['Error_R1b']:>6,.0f})")
    print(f"  Pred (R1c Interact):  ${row['Pred_R1c_Interactions']:>6,.0f}  (Error: ${row['Error_R1c']:>6,.0f})")

# ============================================================================
# 5. SUBGROUP MODEL PREDICTIONS
# ============================================================================
print("\n" + "="*100)
print("5. Subgroup Model Predictions (High-Pell vs Low-Pell)")
print("="*100)

median_pell = metadata['median_pell_threshold']

# Split sample into high/low Pell
df_sample_high = df_sample[df_sample['pct_pell_imputed'] >= median_pell].copy()
df_sample_low = df_sample[df_sample['pct_pell_imputed'] < median_pell].copy()

if len(df_sample_high) > 0:
    print(f"\nHigh-Pell Institutions (≥{median_pell:.1f}% Pell): {len(df_sample_high)} in sample")
    X_high = df_sample_high[all_features]
    preds_high = models['R1d (High-Pell)'].predict(X_high)
    
    for i, (idx, row) in enumerate(df_sample_high.iterrows()):
        actual = row['earnings_10yr']
        pred = preds_high[i]
        error = actual - pred
        print(f"  {row['Institution Name_aff'][:50]:<50} | Actual: ${actual:>6,.0f} | Pred: ${pred:>6,.0f} | Error: ${error:>5,.0f}")

if len(df_sample_low) > 0:
    print(f"\nLow-Pell Institutions (<{median_pell:.1f}% Pell): {len(df_sample_low)} in sample")
    X_low = df_sample_low[all_features]
    preds_low = models['R1d (Low-Pell)'].predict(X_low)
    
    for i, (idx, row) in enumerate(df_sample_low.iterrows()):
        actual = row['earnings_10yr']
        pred = preds_low[i]
        error = actual - pred
        print(f"  {row['Institution Name_aff'][:50]:<50} | Actual: ${actual:>6,.0f} | Pred: ${pred:>6,.0f} | Error: ${error:>5,.0f}")

# ============================================================================
# 6. MODEL COMPARISON METRICS
# ============================================================================
print("\n" + "="*100)
print("6. Model Comparison on Full Test Set")
print("="*100)

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Make predictions on entire dataset
X_full = df_complete[all_features]
X_full_no_afford = df_complete[all_features_no_afford]

# Prepare interactions for full dataset
df_complete['afford_x_pell'] = (
    df_complete['Affordability Gap (net price minus income earned working 10 hrs at min wage)'] * 
    df_complete['pct_pell_imputed']
)
df_complete['afford_x_urm'] = (
    df_complete['Affordability Gap (net price minus income earned working 10 hrs at min wage)'] * 
    df_complete['pct_urm']
)
X_full_interactions = df_complete[all_features_interactions]

y_true = df_complete['earnings_10yr']

# Predictions
y_pred_r1a = models['R1a (Full)'].predict(X_full)
y_pred_r1b = models['R1b (No Afford)'].predict(X_full_no_afford)
y_pred_r1c = models['R1c (Interactions)'].predict(X_full_interactions)

# Calculate metrics
results_comparison = pd.DataFrame({
    'Model': ['R1a (Full)', 'R1b (No Affordability)', 'R1c (Interactions)'],
    'R²': [
        r2_score(y_true, y_pred_r1a),
        r2_score(y_true, y_pred_r1b),
        r2_score(y_true, y_pred_r1c)
    ],
    'RMSE': [
        np.sqrt(mean_squared_error(y_true, y_pred_r1a)),
        np.sqrt(mean_squared_error(y_true, y_pred_r1b)),
        np.sqrt(mean_squared_error(y_true, y_pred_r1c))
    ],
    'MAE': [
        mean_absolute_error(y_true, y_pred_r1a),
        mean_absolute_error(y_true, y_pred_r1b),
        mean_absolute_error(y_true, y_pred_r1c)
    ]
})

print("\n📊 Model Performance Metrics:")
print(results_comparison.to_string(index=False))

print("\n💡 Key Insights:")
r2_diff = results_comparison.loc[0, 'R²'] - results_comparison.loc[1, 'R²']
rmse_diff = results_comparison.loc[1, 'RMSE'] - results_comparison.loc[0, 'RMSE']

print(f"  • R1a (with affordability) has R² = {results_comparison.loc[0, 'R²']:.4f}")
print(f"  • R1b (without affordability) has R² = {results_comparison.loc[1, 'R²']:.4f}")
print(f"  • Affordability adds {r2_diff:+.4f} to R² ({r2_diff/results_comparison.loc[1, 'R²']*100:+.2f}%)")
print(f"  • Affordability reduces RMSE by ${rmse_diff:.2f}")

# ============================================================================
# 7. SAVE PREDICTIONS
# ============================================================================
print("\n" + "="*100)
print("7. Saving Predictions")
print("="*100)

# Save sample predictions
predictions.to_csv('outputs/rf_analysis/sample_predictions.csv', index=False)
print("✓ Saved: outputs/rf_analysis/sample_predictions.csv")

# Save full predictions
df_complete['pred_earnings_r1a'] = y_pred_r1a
df_complete['pred_earnings_r1b'] = y_pred_r1b
df_complete['pred_earnings_r1c'] = y_pred_r1c
df_complete['error_r1a'] = y_true - y_pred_r1a
df_complete['error_r1b'] = y_true - y_pred_r1b
df_complete['error_r1c'] = y_true - y_pred_r1c

# Save key columns
predictions_full = df_complete[[
    'unit_id', 'Institution Name_aff', 'State Abbreviation', 'Sector Name',
    'afford_gap_cont',
    'pct_pell_imputed', 'pct_urm', 'admit_rate_imputed',
    'earnings_10yr', 'pred_earnings_r1a', 'pred_earnings_r1b', 'pred_earnings_r1c',
    'error_r1a', 'error_r1b', 'error_r1c'
]]
# Rename back for readability
predictions_full = predictions_full.rename(columns={'afford_gap_cont': 'affordability_gap'})

predictions_full.to_csv('outputs/rf_analysis/full_predictions.csv', index=False)
print("✓ Saved: outputs/rf_analysis/full_predictions.csv")
print(f"  Total predictions: {len(predictions_full):,} institutions")

print("\n" + "="*100)
print("✓ MODEL LOADING AND PREDICTION COMPLETE")
print("="*100)

print("\n💾 Model Files:")
for name, filepath in model_files.items():
    print(f"  • {filepath}")

print("\n📊 Output Files:")
print("  • outputs/rf_analysis/sample_predictions.csv (10 sample institutions)")
print("  • outputs/rf_analysis/full_predictions.csv (all 5,013 institutions)")

print("\n💡 To use these models in your own code:")
print("""
    import joblib
    import pandas as pd
    
    # Load model
    model = joblib.load('outputs/rf_analysis/models/model_r1a_full.pkl')
    
    # Load your data
    df = pd.read_csv('your_data.csv')
    
    # Prepare features (same as training)
    X = df[numeric_features + categorical_features]
    
    # Make predictions
    predictions = model.predict(X)
""")

