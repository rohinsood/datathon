"""
Model Performance Comparison: Before vs After Optimization
===========================================================
Creates visualizations comparing model performance before and after improvements.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Performance data
data = {
    'Model': ['R1a (Full)', 'R1b (No Afford)', 'R1c (Interactions)', 'R1d (High-Pell)', 'R1d (Low-Pell)'],
    'R2_Before': [0.9311, 0.9307, 0.9200, 0.7324, 0.9380],
    'R2_After': [0.9537, 0.9643, 0.9328, 0.7330, 0.9381],
    'RMSE_Before': [3374, 3383, 3636, 5131, 3304],
    'RMSE_After': [2767, 2430, 3331, 5126, 3301],
    'Afford_Rank_Before': [11, np.nan, np.nan, 6, 12],
    'Afford_Rank_After': [10, np.nan, 1, 1, 1],
    'Afford_Importance_Before': [0.025, np.nan, np.nan, 0.061, 0.011],
    'Afford_Importance_After': [0.038, np.nan, 0.031, 0.060, 0.011]
}

df = pd.DataFrame(data)

# Create comprehensive comparison figure
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# 1. R² Comparison
ax1 = fig.add_subplot(gs[0, 0])
x = np.arange(len(df))
width = 0.35
bars1 = ax1.bar(x - width/2, df['R2_Before'], width, label='Before', color='#E74C3C', alpha=0.8)
bars2 = ax1.bar(x + width/2, df['R2_After'], width, label='After', color='#2ECC71', alpha=0.8)
ax1.set_ylabel('R² Score', fontsize=12, fontweight='bold')
ax1.set_title('A. Model R² Comparison\n(Higher = Better)', fontsize=13, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(df['Model'], rotation=15, ha='right', fontsize=10)
ax1.legend(fontsize=11)
ax1.set_ylim([0.65, 1.0])
ax1.axhline(y=0.95, color='gray', linestyle='--', alpha=0.3, linewidth=1)
ax1.grid(axis='y', alpha=0.3)

# Add improvement percentages
for i, (before, after) in enumerate(zip(df['R2_Before'], df['R2_After'])):
    improvement = ((after - before) / before) * 100
    if improvement > 0:
        ax1.text(i, max(before, after) + 0.01, f'+{improvement:.1f}%', 
                ha='center', fontsize=9, fontweight='bold', color='green')

# 2. RMSE Comparison
ax2 = fig.add_subplot(gs[0, 1])
bars1 = ax2.bar(x - width/2, df['RMSE_Before'], width, label='Before', color='#E74C3C', alpha=0.8)
bars2 = ax2.bar(x + width/2, df['RMSE_After'], width, label='After', color='#2ECC71', alpha=0.8)
ax2.set_ylabel('RMSE (dollars)', fontsize=12, fontweight='bold')
ax2.set_title('B. Model RMSE Comparison\n(Lower = Better)', fontsize=13, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(df['Model'], rotation=15, ha='right', fontsize=10)
ax2.legend(fontsize=11)
ax2.grid(axis='y', alpha=0.3)

# Add improvement amounts
for i, (before, after) in enumerate(zip(df['RMSE_Before'], df['RMSE_After'])):
    improvement = before - after
    if improvement > 0:
        ax2.text(i, max(before, after) + 150, f'-${improvement:.0f}', 
                ha='center', fontsize=9, fontweight='bold', color='green')

# 3. RMSE Reduction Bar Chart
ax3 = fig.add_subplot(gs[1, 0])
rmse_reduction = df['RMSE_Before'] - df['RMSE_After']
rmse_pct = ((df['RMSE_Before'] - df['RMSE_After']) / df['RMSE_Before'] * 100)
colors_reduction = ['#2ECC71' if x > 0 else '#E74C3C' for x in rmse_reduction]
bars = ax3.barh(df['Model'], rmse_reduction, color=colors_reduction, alpha=0.8)
ax3.set_xlabel('RMSE Reduction (dollars)', fontsize=12, fontweight='bold')
ax3.set_title('C. Prediction Error Reduction\n(Positive = Improvement)', fontsize=13, fontweight='bold')
ax3.grid(axis='x', alpha=0.3)
ax3.axvline(x=0, color='black', linewidth=1)

# Add values
for i, (val, pct) in enumerate(zip(rmse_reduction, rmse_pct)):
    if val > 0:
        ax3.text(val + 50, i, f'${val:.0f}\n({pct:.1f}%)', 
                va='center', fontsize=9, fontweight='bold')

# 4. R² Improvement Percentage
ax4 = fig.add_subplot(gs[1, 1])
r2_improvement_pct = ((df['R2_After'] - df['R2_Before']) / df['R2_Before'] * 100)
colors_r2 = ['#2ECC71' if x > 0 else '#E74C3C' for x in r2_improvement_pct]
bars = ax4.barh(df['Model'], r2_improvement_pct, color=colors_r2, alpha=0.8)
ax4.set_xlabel('R² Improvement (%)', fontsize=12, fontweight='bold')
ax4.set_title('D. R² Percentage Improvement\n(Positive = Better Fit)', fontsize=13, fontweight='bold')
ax4.grid(axis='x', alpha=0.3)
ax4.axvline(x=0, color='black', linewidth=1)

# Add values
for i, (val, before, after) in enumerate(zip(r2_improvement_pct, df['R2_Before'], df['R2_After'])):
    if val > 0:
        ax4.text(val + 0.05, i, f'+{val:.2f}%\n({before:.3f}→{after:.3f})', 
                va='center', fontsize=8, fontweight='bold')

# 5. Affordability Rank Comparison
ax5 = fig.add_subplot(gs[2, 0])
models_with_afford = df[df['Afford_Rank_Before'].notna()]['Model'].tolist()
# Invert ranks (lower rank = higher importance, so we invert for visualization)
rank_before = [11, 6, 12]  # R1a, High-Pell, Low-Pell
rank_after = [10, 1, 1]
x_afford = np.arange(len(models_with_afford))

# Plot lines
for i in range(len(x_afford)):
    ax5.plot([i, i], [rank_before[i], rank_after[i]], 'k-', linewidth=2, alpha=0.3)
    
ax5.scatter(x_afford, rank_before, s=200, color='#E74C3C', alpha=0.8, label='Before', zorder=3)
ax5.scatter(x_afford, rank_after, s=200, color='#2ECC71', alpha=0.8, label='After', zorder=3)

ax5.set_ylabel('Affordability Gap Rank', fontsize=12, fontweight='bold')
ax5.set_title('E. Affordability Gap Feature Rank\n(Lower Rank = More Important)', fontsize=13, fontweight='bold')
ax5.set_xticks(x_afford)
ax5.set_xticklabels(models_with_afford, fontsize=10)
ax5.legend(fontsize=11)
ax5.invert_yaxis()  # Lower rank at top
ax5.grid(axis='y', alpha=0.3)

# Add rank labels
for i, (before, after) in enumerate(zip(rank_before, rank_after)):
    ax5.text(i - 0.15, before, f'#{int(before)}', ha='center', va='center', fontsize=9, fontweight='bold')
    ax5.text(i + 0.15, after, f'#{int(after)}', ha='center', va='center', fontsize=9, fontweight='bold')

# 6. Affordability Importance Comparison
ax6 = fig.add_subplot(gs[2, 1])
importance_before = [0.025, 0.061, 0.011]  # R1a, High-Pell, Low-Pell
importance_after = [0.038, 0.060, 0.011]
x_afford = np.arange(len(models_with_afford))
width = 0.35

bars1 = ax6.bar(x_afford - width/2, importance_before, width, label='Before', color='#E74C3C', alpha=0.8)
bars2 = ax6.bar(x_afford + width/2, importance_after, width, label='After', color='#2ECC71', alpha=0.8)

ax6.set_ylabel('Feature Importance', fontsize=12, fontweight='bold')
ax6.set_title('F. Affordability Gap Importance Score\n(Higher = More Predictive)', fontsize=13, fontweight='bold')
ax6.set_xticks(x_afford)
ax6.set_xticklabels(models_with_afford, fontsize=10)
ax6.legend(fontsize=11)
ax6.grid(axis='y', alpha=0.3)

# Add percentage labels
for i, (before, after) in enumerate(zip(importance_before, importance_after)):
    ax6.text(i - width/2, before + 0.002, f'{before*100:.1f}%', 
            ha='center', fontsize=8, fontweight='bold')
    ax6.text(i + width/2, after + 0.002, f'{after*100:.1f}%', 
            ha='center', fontsize=8, fontweight='bold')

# Overall title
fig.suptitle('Random Forest Model Performance: Before vs After Optimization\n' + 
             'Improvements: (1) Added Missingness Flags (2) Optimized Hyperparameters (3) Expanded Features',
             fontsize=15, fontweight='bold', y=0.995)

# Add summary text box
summary_text = (
    "KEY IMPROVEMENTS:\n"
    "• R1a R² improved: 0.9311 → 0.9537 (+2.4%)\n"
    "• R1a RMSE reduced: $3,374 → $2,767 (-18%)\n"
    "• Affordability importance: 2.5% → 3.8%\n"
    "• Missingness flags added for test scores\n"
    "• Random Forest tuned: 500 trees, depth 25"
)

fig.text(0.02, 0.02, summary_text, 
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3),
         fontsize=9, verticalalignment='bottom', family='monospace')

plt.tight_layout(rect=[0, 0.05, 1, 0.99])
plt.savefig('outputs/rf_analysis/model_comparison_before_after.png', dpi=300, bbox_inches='tight')
print("✓ Saved: outputs/rf_analysis/model_comparison_before_after.png")
plt.close()

print("\n" + "="*80)
print("📊 COMPARISON COMPLETE")
print("="*80)
print(f"\n✅ Overall R1a Model Improvement:")
print(f"   R² improved: 0.9311 → 0.9537 (+{((0.9537-0.9311)/0.9311)*100:.2f}%)")
print(f"   RMSE reduced: $3,374 → $2,767 (-{((3374-2767)/3374)*100:.1f}%)")
print(f"\n✅ Affordability Gap Story:")
print(f"   Rank improved: #11 → #10")
print(f"   Importance increased: 2.5% → 3.8% (+{((0.038-0.025)/0.025)*100:.0f}%)")
print(f"\n✅ Methodological Improvements:")
print(f"   • Added sat_missing and act_missing flags")
print(f"   • Optimized RF: 200→500 trees, depth 20→25")
print(f"   • Total features: 29 → 31")
print(f"\n💡 Core Finding Unchanged:")
print(f"   Affordability 5.5× more important for high-Pell institutions")
print("="*80)

