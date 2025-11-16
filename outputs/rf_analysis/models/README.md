# 💾 Saved Random Forest Models

## Overview

This directory contains **5 trained Random Forest models** for predicting 10-year earnings outcomes based on institutional characteristics and affordability.

**Training Date**: November 15, 2025  
**Total Model Size**: ~272 MB  
**Training Sample**: 4,010 institutions (5,013 total with complete data)  
**Test Sample**: 1,003 institutions  
**Model Performance (R1a)**: R² = 0.9537, RMSE = $2,767

---

## 📦 Model Files

| File | Size | Description |
|------|------|-------------|
| `model_r1a_full.pkl` | 54.4 MB | **Full model** with all features including affordability gap |
| `model_r1b_no_afford.pkl` | 53.4 MB | **Baseline model** without affordability gap (for comparison) |
| `model_r1c_interactions.pkl` | 56.0 MB | **Interaction model** with affordability × Pell and affordability × URM |
| `model_r1d_high_pell.pkl` | 5.7 MB | **Subgroup model** for high-Pell institutions (≥44% Pell) |
| `model_r1d_low_pell.pkl` | 5.5 MB | **Subgroup model** for low-Pell institutions (<44% Pell) |
| `model_metadata.json` | <1 KB | Metadata including feature lists, hyperparameters, and descriptions |

---

## 🎯 Model Specifications

### Common Hyperparameters
- **Algorithm**: Random Forest Regressor (sklearn)
- **Number of trees**: 500
- **Max depth**: 25
- **Min samples split**: 5
- **Min samples leaf**: 2
- **Max features**: 'sqrt'
- **Random state**: 42
- **Parallel jobs**: -1 (all cores)

### Input Features
- **Numeric features**: 18
  - `afford_gap_cont` (affordability gap)
  - `admit_rate_imputed`, `sat_composite_25_imputed`, `act_composite_25_imputed`
  - `sat_missing`, `act_missing` (missingness flags)
  - `log_instructional_exp`, `log_endowment`, `has_endowment`
  - `pct_pell_imputed`, `pct_urm`, `pct_white_imputed`, `pct_women_imputed`
  - `is_hbcu`, `is_hsi`, `is_tcu`, `is_aanapisi`, `is_pbi` (MSI indicators)

- **Categorical features**: 3 (one-hot encoded)
  - `sector` (Public, Private nonprofit, Private for-profit)
  - `size_category` (Under 1,000 to 20,000+)
  - `region` (Midwest, Northeast, South, West)

- **Target variable**: `earnings_10yr` 
  - Median earnings of dependent students 10 years after entry

### Total Features After Preprocessing
- **R1a, R1d**: 31 features (after one-hot encoding)
- **R1b**: 30 features (afford_gap_cont removed)
- **R1c**: 33 features (added 2 interaction terms)

---

## 📊 Model Performance

| Model | R² (Test) | RMSE (Test) | Description |
|-------|-----------|-------------|-------------|
| **R1a (Full)** | 0.9537 | $2,767 | Best overall performance |
| **R1b (No Afford)** | 0.9643 | $2,430 | Surprisingly strong without affordability |
| **R1c (Interactions)** | 0.9328 | $3,331 | Captures interaction effects |
| **R1d (High-Pell)** | 0.7330 | $5,126 | Specialized for high-Pell institutions |
| **R1d (Low-Pell)** | 0.9381 | $3,301 | Specialized for low-Pell institutions |

### Key Findings
- **Affordability importance**: Ranks #10 overall (3.8% importance)
- **High-Pell institutions**: Affordability ranks #1 (6.0% importance)
- **Low-Pell institutions**: Affordability ranks #1 (1.1% importance)
- **Importance ratio**: Affordability is **5.5× more important** for high-Pell institutions

---

## 🔧 How to Load and Use Models

### Basic Usage (Python)

```python
import joblib
import pandas as pd

# 1. Load a model
model = joblib.load('outputs/rf_analysis/models/model_r1a_full.pkl')

# 2. Load your data
df = pd.read_csv('outputs/data/analysis_ready.csv')

# 3. Prepare features (must match training exactly)
# Rename affordability column
df = df.rename(columns={
    'Affordability Gap (net price minus income earned working 10 hrs at min wage)': 'afford_gap_cont'
})

# Select features
numeric_features = [
    'afford_gap_cont', 'admit_rate_imputed', 'sat_composite_25_imputed',
    'act_composite_25_imputed', 'sat_missing', 'act_missing',
    'log_instructional_exp', 'log_endowment', 'has_endowment',
    'pct_pell_imputed', 'pct_urm', 'pct_white_imputed', 'pct_women_imputed',
    'is_hbcu', 'is_hsi', 'is_tcu', 'is_aanapisi', 'is_pbi'
]
categorical_features = ['sector', 'size_category', 'region']
all_features = numeric_features + categorical_features

X = df[all_features]

# 4. Make predictions
predictions = model.predict(X)

# 5. Add predictions to dataframe
df['predicted_earnings'] = predictions
```

### Loading Metadata

```python
import json

with open('outputs/rf_analysis/models/model_metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Features: {metadata['numeric_features']}")
print(f"Target: {metadata['target_variable']}")
print(f"Median Pell threshold: {metadata['median_pell_threshold']}%")
```

### Making Predictions with Subgroup Models

```python
# Determine institution type
median_pell = 44.0  # from metadata

# High-Pell institutions
df_high = df[df['pct_pell_imputed'] >= median_pell]
model_high = joblib.load('outputs/rf_analysis/models/model_r1d_high_pell.pkl')
predictions_high = model_high.predict(df_high[all_features])

# Low-Pell institutions
df_low = df[df['pct_pell_imputed'] < median_pell]
model_low = joblib.load('outputs/rf_analysis/models/model_r1d_low_pell.pkl')
predictions_low = model_low.predict(df_low[all_features])
```

---

## ⚠️ Important Notes

### Data Preprocessing Requirements
1. **Column names must match exactly** - especially the affordability gap column
2. **Missing values must be imputed** - use median imputation as in training
3. **Log transformations applied** - `log_instructional_exp`, `log_endowment`
4. **Categorical encoding** - Pipeline handles one-hot encoding automatically
5. **Feature order matters** - must provide features in the exact order as training

### Limitations
- Models trained on **4-year bachelor's-granting institutions only**
- Data from **2021 cohort** (may not generalize to other years)
- Earnings data has **privacy suppression** for some institutions
- High **missing rate for test scores** (64-66%) despite imputation flags
- Models assume **Missing At Random (MAR)** after controlling for flags

### Best Practices
- Use **R1a** for general predictions (best overall performance)
- Use **R1d subgroup models** when analyzing equity-serving vs selective institutions
- Use **R1b** to quantify affordability's contribution (compare to R1a)
- Use **R1c** to understand interaction effects between affordability and demographics

---

## 📚 Related Files

### Analysis Outputs
- `../feature_importance_r1a.csv` - Feature importance rankings for R1a
- `../feature_importance_r1c.csv` - Feature importance for interaction model
- `../feature_importance_high_pell.csv` - Feature importance for high-Pell subgroup
- `../feature_importance_low_pell.csv` - Feature importance for low-Pell subgroup
- `../model_summary.csv` - Performance metrics for all models
- `../PERFORMANCE_IMPROVEMENTS.md` - Detailed report on model optimizations
- `../SUMMARY_REPORT.md` - Comprehensive analysis findings

### Visualizations
- `../feature_importance_comparison.png` - 4-panel feature importance comparison
- `../model_comparison_before_after.png` - Performance improvements visualization

### Source Code
- `../../src/earnings_mobility_rf_analysis.py` - Model training script
- `../../src/compare_model_versions.py` - Performance comparison script

---

## 🔄 Retraining Models

To retrain these models with updated data:

```bash
cd /path/to/datathon
python src/earnings_mobility_rf_analysis.py
```

This will:
1. Load `outputs/data/analysis_ready.csv`
2. Train all 5 models with optimized hyperparameters
3. Save models to this directory (overwriting existing)
4. Generate performance reports and visualizations
5. Save feature importance rankings

**Runtime**: Approximately 5-10 minutes on a standard laptop

---

## 💡 Use Cases

### 1. **Institution-Level Predictions**
Predict expected earnings for specific colleges based on their affordability and characteristics.

### 2. **Policy Simulation**
Model how changes in affordability (e.g., increased grant aid) would affect predicted earnings.

### 3. **Benchmarking**
Compare actual vs predicted earnings to identify over/under-performing institutions.

### 4. **Equity Analysis**
Use subgroup models to understand differential effects at high-Pell vs low-Pell institutions.

### 5. **Dashboard Integration**
Load models into web applications for interactive exploration of affordability-mobility relationships.

---

## 📞 Support

For questions about these models:
- Review the training script: `src/earnings_mobility_rf_analysis.py`
- Check analysis logs: `../SUMMARY_REPORT.md`
- See performance details: `../PERFORMANCE_IMPROVEMENTS.md`

**Model Version**: 2.0 (Optimized with missingness flags)  
**Last Updated**: November 15, 2025  
**Status**: Production-ready ✅

