#!/usr/bin/env python3
"""
DoWhy Causal Analysis: Affordability Gap Effect on 10-Year Earnings

Research Question:
What is the causal effect of being in a low affordability gap institution on 10-year 
earnings, after controlling for selectivity, demographics, resources, and other 
institutional characteristics?

This script uses DoWhy to:
1. Define a causal model with explicit assumptions
2. Identify the causal estimand using the backdoor criterion
3. Estimate the average treatment effect (ATE) 
4. Test robustness with multiple refutation methods
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dowhy import CausalModel
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Configure plotting
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

print("="*80)
print("DoWhy CAUSAL ANALYSIS: AFFORDABILITY GAP → 10-YEAR EARNINGS")
print("="*80)
print()

# ============================================================================
# 1. LOAD DATA
# ============================================================================
print("1. LOADING DATA")
print("-" * 80)

df = pd.read_csv('outputs/data/analysis_ready.csv')
print(f"Initial data shape: {df.shape}")

# Check for treatment and outcome variables
print(f"\nTreatment variable 'treatment' present: {'treatment' in df.columns}")
print(f"Outcome variable 'earnings_10yr' present: {'earnings_10yr' in df.columns}")

if 'treatment' in df.columns:
    print(f"\nTreatment distribution:")
    print(df['treatment'].value_counts())
    print(f"  - Treatment=1 (Low Gap): {(df['treatment']==1).sum()} institutions")
    print(f"  - Treatment=0 (High Gap): {(df['treatment']==0).sum()} institutions")

# ============================================================================
# 2. PREPARE VARIABLES
# ============================================================================
print("\n2. PREPARING VARIABLES FOR CAUSAL MODEL")
print("-" * 80)

# Define treatment (already binary: 1 = low gap, 0 = high gap)
treatment = 'treatment'

# Define outcome
outcome = 'earnings_10yr'

# Define confounders (common causes of both treatment and outcome)
# These are variables that affect both affordability gap AND earnings
confounders = [
    # Selectivity measures
    'admit_rate_imputed',
    'sat_composite_25_imputed',
    'sat_missing',
    
    # Institutional resources
    'log_instructional_exp',
    'log_endowment',
    'has_endowment',
    
    # Student demographics
    'pct_pell_imputed',
    'pct_white_imputed',
    'pct_black_imputed',
    'pct_latino_imputed',
    'pct_asian_imputed',
    'pct_women_imputed',
    'pct_urm',
    
    # Minority-serving institution status
    'is_hbcu',
    'is_hsi',
    'is_tcu',
    'is_aanapisi',
    'is_pbi',
    'is_msi',
]

# Categorical confounders that need to be one-hot encoded
categorical_confounders = ['sector', 'size_category', 'region', 'control']

# Check which variables exist
existing_confounders = [c for c in confounders if c in df.columns]
missing_confounders = [c for c in confounders if c not in df.columns]

print(f"Confounders available: {len(existing_confounders)} of {len(confounders)}")
if missing_confounders:
    print(f"Missing confounders: {missing_confounders}")

existing_categorical = [c for c in categorical_confounders if c in df.columns]
print(f"Categorical confounders: {existing_categorical}")

# ============================================================================
# 3. DATA PREPARATION
# ============================================================================
print("\n3. DATA PREPARATION")
print("-" * 80)

# Create a working dataset with only needed variables
analysis_vars = [treatment, outcome] + existing_confounders + existing_categorical

# Filter to only rows with valid treatment and outcome
df_analysis = df[analysis_vars].copy()
df_analysis = df_analysis.dropna(subset=[treatment, outcome])

print(f"After removing missing treatment/outcome: {df_analysis.shape}")

# One-hot encode categorical variables
for cat_var in existing_categorical:
    if cat_var in df_analysis.columns:
        dummies = pd.get_dummies(df_analysis[cat_var], prefix=cat_var, drop_first=True)
        df_analysis = pd.concat([df_analysis, dummies], axis=1)
        existing_confounders.extend(dummies.columns.tolist())
        df_analysis = df_analysis.drop(cat_var, axis=1)

# Handle any remaining missing values in confounders with median imputation
for col in existing_confounders:
    if col in df_analysis.columns and df_analysis[col].isnull().any():
        median_val = df_analysis[col].median()
        df_analysis[col] = df_analysis[col].fillna(median_val)
        print(f"Imputed {col} with median: {median_val:.2f}")

print(f"\nFinal analysis dataset shape: {df_analysis.shape}")
print(f"Treatment groups:")
print(f"  - Low Gap (Treatment=1): {(df_analysis[treatment]==1).sum()}")
print(f"  - High Gap (Control=0): {(df_analysis[treatment]==0).sum()}")
print(f"\nOutcome (earnings) stats:")
print(df_analysis[outcome].describe())

# ============================================================================
# 4. SPECIFY CAUSAL MODEL
# ============================================================================
print("\n4. SPECIFYING CAUSAL MODEL WITH DoWhy")
print("-" * 80)

print("\nCausal Assumptions:")
print("  - Treatment: Being in a LOW affordability gap institution (1) vs HIGH gap (0)")
print("  - Outcome: Median 10-year earnings of graduates")
print("  - Confounders: All variables that affect BOTH affordability gap AND earnings")
print("  - Key assumption: No unobserved confounding (conditional ignorability)")
print()

print("Causal graph structure (DAG):")
print("  Confounders → Treatment")
print("  Confounders → Outcome")
print("  Treatment → Outcome  ← THIS IS WHAT WE'RE ESTIMATING")
print()
print(f"Common causes (confounders): {len(existing_confounders)} variables")
print(f"  Examples: {', '.join(existing_confounders[:5])}...")
print()

# Create DoWhy CausalModel without explicit graph
# DoWhy will auto-construct the graph from common_causes
model = CausalModel(
    data=df_analysis,
    treatment=treatment,
    outcome=outcome,
    common_causes=existing_confounders
)
print("✓ CausalModel created successfully")
print(f"  - Treatment: {treatment}")
print(f"  - Outcome: {outcome}")
print(f"  - Number of confounders: {len(existing_confounders)}")

# ============================================================================
# 5. IDENTIFY CAUSAL ESTIMAND
# ============================================================================
print("\n5. IDENTIFYING CAUSAL ESTIMAND (BACKDOOR CRITERION)")
print("-" * 80)

try:
    identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
    print(identified_estimand)
    print("\n✓ Causal estimand identified successfully")
    print("\nInterpretation:")
    print("  DoWhy has identified which variables need to be controlled for")
    print("  to block all backdoor paths from treatment to outcome.")
    
except Exception as e:
    print(f"✗ Error identifying estimand: {e}")
    raise

# ============================================================================
# 6. ESTIMATE CAUSAL EFFECT
# ============================================================================
print("\n6. ESTIMATING CAUSAL EFFECT")
print("-" * 80)

# Method 1: Propensity Score Weighting (IPW)
print("\nMethod 1: Propensity Score Weighting (Inverse Probability Weighting)")
print("-" * 40)

try:
    estimate_ipw = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.propensity_score_weighting"
    )
    
    print(estimate_ipw)
    print(f"\n✓ ATE Estimate (IPW): ${estimate_ipw.value:,.2f}")
    print(f"\nInterpretation:")
    if estimate_ipw.value > 0:
        print(f"  Being in a LOW affordability gap institution (vs HIGH gap)")
        print(f"  is associated with ${estimate_ipw.value:,.2f} HIGHER")
        print(f"  10-year median earnings, on average.")
    elif estimate_ipw.value < 0:
        print(f"  Being in a LOW affordability gap institution (vs HIGH gap)")
        print(f"  is associated with ${abs(estimate_ipw.value):,.2f} LOWER")
        print(f"  10-year median earnings, on average.")
    else:
        print(f"  Being in a LOW vs HIGH affordability gap institution")
        print(f"  shows NO meaningful difference in 10-year earnings.")
    
except Exception as e:
    print(f"✗ Error with IPW estimation: {e}")
    estimate_ipw = None

# Method 2: Propensity Score Stratification
print("\n\nMethod 2: Propensity Score Stratification")
print("-" * 40)

try:
    estimate_strat = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.propensity_score_stratification"
    )
    
    print(estimate_strat)
    print(f"\n✓ ATE Estimate (Stratification): ${estimate_strat.value:,.2f}")
    
except Exception as e:
    print(f"✗ Error with stratification: {e}")
    estimate_strat = None

# Method 3: Linear Regression (backdoor adjustment)
print("\n\nMethod 3: Linear Regression (Backdoor Adjustment)")
print("-" * 40)

try:
    estimate_reg = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.linear_regression"
    )
    
    print(estimate_reg)
    print(f"\n✓ ATE Estimate (Regression): ${estimate_reg.value:,.2f}")
    
except Exception as e:
    print(f"✗ Error with regression: {e}")
    estimate_reg = None

# ============================================================================
# 7. COMPARE ESTIMATES
# ============================================================================
print("\n\n7. COMPARING ESTIMATES ACROSS METHODS")
print("-" * 80)

estimates = []
if estimate_ipw is not None:
    estimates.append(('IPW', estimate_ipw.value))
if estimate_strat is not None:
    estimates.append(('Stratification', estimate_strat.value))
if estimate_reg is not None:
    estimates.append(('Regression', estimate_reg.value))

if estimates:
    print("\nAll estimates:")
    for method, est in estimates:
        print(f"  {method:20s}: ${est:>10,.2f}")
    
    values = [est for _, est in estimates]
    print(f"\n  Mean across methods: ${np.mean(values):,.2f}")
    print(f"  Std across methods:  ${np.std(values):,.2f}")
    print(f"  Range: ${min(values):,.2f} to ${max(values):,.2f}")
    
    # Check consistency
    same_sign = all(v > 0 for v in values) or all(v < 0 for v in values) or all(abs(v) < 100 for v in values)
    if same_sign:
        print("\n✓ All methods show CONSISTENT direction → Robust finding")
    else:
        print("\n⚠ Methods show DIFFERENT directions → Results not robust")

# ============================================================================
# 8. REFUTATION TESTS (ROBUSTNESS CHECKS)
# ============================================================================
print("\n\n8. REFUTATION TESTS (ROBUSTNESS CHECKS)")
print("="*80)

# Use IPW estimate as our primary estimate for refutation
primary_estimate = estimate_ipw if estimate_ipw is not None else estimate_reg

if primary_estimate is not None:
    
    # Refutation 1: Random Common Cause
    print("\nRefutation Test 1: Add Random Common Cause")
    print("-" * 40)
    print("Test: Add a randomly generated variable as a confounder")
    print("Expected: Should NOT change the estimate significantly")
    print()
    
    try:
        refute_random = model.refute_estimate(
            identified_estimand,
            primary_estimate,
            method_name="random_common_cause"
        )
        print(refute_random)
        
        original_est = refute_random.estimated_effect
        refuted_est = refute_random.new_effect
        
        print(f"\nOriginal estimate: ${original_est:,.2f}")
        print(f"After adding random cause: ${refuted_est:,.2f}")
        print(f"Change: ${abs(refuted_est - original_est):,.2f}")
        
        if abs(refuted_est - original_est) < abs(original_est) * 0.2:
            print("✓ PASSED: Effect stable with random confounder")
        else:
            print("⚠ FAILED: Effect changed substantially with random confounder")
            print("   This suggests the model may be sensitive to unobserved confounding")
    
    except Exception as e:
        print(f"✗ Error in random common cause refutation: {e}")
    
    # Refutation 2: Placebo Treatment
    print("\n\nRefutation Test 2: Placebo Treatment Refuter")
    print("-" * 40)
    print("Test: Replace treatment with random assignment")
    print("Expected: Effect should disappear (become ~0)")
    print()
    
    try:
        refute_placebo = model.refute_estimate(
            identified_estimand,
            primary_estimate,
            method_name="placebo_treatment_refuter",
            num_simulations=20  # Run 20 placebo trials
        )
        print(refute_placebo)
        
        print(f"\nOriginal estimate: ${primary_estimate.value:,.2f}")
        
        # The placebo should show no effect
        if hasattr(refute_placebo, 'new_effect'):
            print(f"Placebo effect: ${refute_placebo.new_effect:,.2f}")
            
            if abs(refute_placebo.new_effect) < abs(primary_estimate.value) * 0.5:
                print("✓ PASSED: Placebo treatment shows smaller effect")
            else:
                print("⚠ WARNING: Placebo treatment shows similar effect size")
    
    except Exception as e:
        print(f"✗ Error in placebo refutation: {e}")
    
    # Refutation 3: Data Subset Refuter
    print("\n\nRefutation Test 3: Data Subset Refuter")
    print("-" * 40)
    print("Test: Re-estimate on random subsets of data")
    print("Expected: Effect should be similar across subsets")
    print()
    
    try:
        refute_subset = model.refute_estimate(
            identified_estimand,
            primary_estimate,
            method_name="data_subset_refuter",
            subset_fraction=0.8,  # Use 80% of data
            num_simulations=20
        )
        print(refute_subset)
        
        print(f"\nOriginal estimate: ${primary_estimate.value:,.2f}")
        
        if hasattr(refute_subset, 'new_effect'):
            print(f"Mean subset effect: ${refute_subset.new_effect:,.2f}")
            
            pct_diff = abs(refute_subset.new_effect - primary_estimate.value) / abs(primary_estimate.value) * 100
            print(f"Percent difference: {pct_diff:.1f}%")
            
            if pct_diff < 30:
                print("✓ PASSED: Effect stable across data subsets")
            else:
                print("⚠ WARNING: Effect varies substantially across subsets")
    
    except Exception as e:
        print(f"✗ Error in subset refutation: {e}")
    
    # Refutation 4: Add Unobserved Common Cause
    print("\n\nRefutation Test 4: Sensitivity to Unobserved Confounder")
    print("-" * 40)
    print("Test: Simulate effect of unobserved confounder")
    print("Expected: Understand how sensitive results are to hidden confounding")
    print()
    
    try:
        refute_unobserved = model.refute_estimate(
            identified_estimand,
            primary_estimate,
            method_name="add_unobserved_common_cause",
            confounders_effect_on_treatment="binary_flip",  # Moderate effect on treatment
            confounders_effect_on_outcome="linear",  # Linear effect on outcome
            effect_strength_on_treatment=0.1,  # 10% of treated units flipped
            effect_strength_on_outcome=1000  # $1000 effect on outcome
        )
        print(refute_unobserved)
        
        print(f"\nOriginal estimate: ${primary_estimate.value:,.2f}")
        if hasattr(refute_unobserved, 'new_effect'):
            print(f"After adding unobserved confounder: ${refute_unobserved.new_effect:,.2f}")
            print(f"Change: ${abs(refute_unobserved.new_effect - primary_estimate.value):,.2f}")
    
    except Exception as e:
        print(f"✗ Error in unobserved confounder test: {e}")

# ============================================================================
# 9. VISUALIZATIONS
# ============================================================================
print("\n\n9. CREATING VISUALIZATIONS")
print("="*80)

# Visualization 1: Estimate comparison
if estimates and len(estimates) > 1:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    methods = [m for m, _ in estimates]
    values = [v for _, v in estimates]
    
    colors = ['steelblue' if v > 0 else 'coral' for v in values]
    ax.barh(methods, values, color=colors, alpha=0.7)
    ax.axvline(0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel('Average Treatment Effect on 10-Year Earnings ($)', fontsize=12)
    ax.set_title('Causal Effect Estimates Across Methods\nLow Gap vs High Gap Institutions', 
                 fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (method, value) in enumerate(estimates):
        ax.text(value, i, f'  ${value:,.0f}', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('outputs/figures/dowhy_ate_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: outputs/figures/dowhy_ate_comparison.png")
    plt.close()

# Visualization 2: Treatment-Outcome relationship (raw vs adjusted)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Raw comparison
raw_means = df_analysis.groupby(treatment)[outcome].mean()
ax = axes[0]
ax.bar(['High Gap\n(Control)', 'Low Gap\n(Treatment)'], 
       [raw_means[0], raw_means[1]], 
       color=['coral', 'steelblue'], alpha=0.7)
ax.set_ylabel('Mean 10-Year Earnings ($)', fontsize=11)
ax.set_title('Raw Comparison\n(Without Controlling for Confounders)', fontsize=12, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
for i, v in enumerate([raw_means[0], raw_means[1]]):
    ax.text(i, v, f'${v:,.0f}', ha='center', va='bottom', fontsize=10)

# Adjusted comparison (showing the causal effect)
if estimate_ipw is not None:
    ax = axes[1]
    # The ATE is the difference, so we show mean of control + ATE for treatment
    control_mean = raw_means[0]
    adjusted_treatment = control_mean + estimate_ipw.value
    
    ax.bar(['High Gap\n(Control)', 'Low Gap\n(Treatment)'], 
           [control_mean, adjusted_treatment], 
           color=['coral', 'steelblue'], alpha=0.7)
    ax.set_ylabel('Mean 10-Year Earnings ($)', fontsize=11)
    ax.set_title('Causal Effect (IPW-Adjusted)\n(After Controlling for Confounders)', 
                 fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add difference annotation
    ax.annotate('', xy=(1, adjusted_treatment), xytext=(1, control_mean),
                arrowprops=dict(arrowstyle='<->', color='red', lw=2))
    ax.text(1.15, (control_mean + adjusted_treatment)/2, 
            f'ATE:\n${estimate_ipw.value:,.0f}',
            fontsize=10, color='red', fontweight='bold')
    
    for i, v in enumerate([control_mean, adjusted_treatment]):
        ax.text(i, v, f'${v:,.0f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('outputs/figures/dowhy_raw_vs_adjusted.png', dpi=300, bbox_inches='tight')
print("✓ Saved: outputs/figures/dowhy_raw_vs_adjusted.png")
plt.close()

# ============================================================================
# 10. FINAL SYNTHESIS
# ============================================================================
print("\n\n10. FINAL SYNTHESIS AND INTERPRETATION")
print("="*80)

if primary_estimate is not None:
    ate_value = primary_estimate.value
    
    print("\n📊 MAIN FINDING:")
    print("-" * 40)
    
    if abs(ate_value) < 500:
        print(f"The causal effect of affordability gap on 10-year earnings is")
        print(f"NEAR ZERO (${ate_value:,.2f})")
        print()
        print("INTERPRETATION:")
        print("  In this dataset and under our causal assumptions, being in a low")
        print("  affordability gap institution (vs high gap) does NOT have a large")
        print("  average effect on 10-year earnings.")
        print()
        print("IMPLICATIONS:")
        print("  • Affordability may matter more for OTHER outcomes (debt, completion,")
        print("    equity, student wellbeing) than for average earnings")
        print("  • Earnings may be driven more by selectivity, field of study, labor")
        print("    market, and other factors than by net price alone")
        print("  • This doesn't mean affordability doesn't matter - it may matter")
        print("    differently for different subgroups (high-Pell, URM, etc.)")
        
    elif ate_value > 500:
        print(f"Being in a LOW affordability gap institution (vs HIGH gap)")
        print(f"is causally associated with HIGHER 10-year earnings:")
        print(f"  ATE = ${ate_value:,.2f}")
        print()
        print("INTERPRETATION:")
        print("  Students at more affordable institutions earn MORE on average,")
        print("  even after controlling for selectivity, demographics, and resources.")
        print()
        print("IMPLICATIONS:")
        print("  • Lower net prices may enable better academic outcomes, completion,")
        print("    or access to higher-earning majors/careers")
        print("  • Reduced financial stress may improve student success")
        print("  • Making college more affordable could improve economic mobility")
        
    else:  # ate_value < -500
        print(f"Being in a LOW affordability gap institution (vs HIGH gap)")
        print(f"is causally associated with LOWER 10-year earnings:")
        print(f"  ATE = ${ate_value:,.2f}")
        print()
        print("INTERPRETATION:")
        print("  Counterintuitively, students at more affordable institutions earn")
        print("  LESS on average, even after controlling for observed factors.")
        print()
        print("POSSIBLE EXPLANATIONS:")
        print("  • This could indicate unobserved confounding (e.g., student")
        print("    motivation, career choices, location preferences)")
        print("  • Lower prices may be at institutions with fewer networking")
        print("    opportunities or employer connections")
        print("  • Students may optimize for factors other than future earnings")
        print("  • Geographic or industry selection effects")
    
    print("\n")
    print("⚠️  CAUSAL ASSUMPTIONS:")
    print("-" * 40)
    print("This causal interpretation relies on:")
    print("  1. No unobserved confounding (all important factors controlled)")
    print("  2. Correct model specification (linear effects, no interactions)")
    print("  3. Common support (overlap in propensity scores)")
    print("  4. Stable unit treatment value assumption (SUTVA)")
    print()
    print("The refutation tests help check these assumptions, but cannot")
    print("prove they hold. Always interpret causal claims with appropriate caution.")

    print("\n")
    print("📈 NEXT STEPS:")
    print("-" * 40)
    print("  1. Examine heterogeneous effects by subgroup (Pell, URM, MSI)")
    print("  2. Explore non-linear effects (quadratic, splines)")
    print("  3. Test alternative outcomes (graduation, debt, satisfaction)")
    print("  4. Consider instrumental variable approaches if available")
    print("  5. Conduct sensitivity analyses with different confounder sets")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nOutputs saved to outputs/figures/")
print("  - dowhy_ate_comparison.png")
print("  - dowhy_raw_vs_adjusted.png")
print()

