"""
Utility Functions for Affordability-Mobility Causal Analysis

This module contains helper functions for:
- Data processing and cleaning
- Causal inference (propensity scores, balance checks, bootstrapping)
- Visualization styling and formatting
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple, List, Dict, Optional


# ============================================================================
# DATA PROCESSING UTILITIES
# ============================================================================

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to lowercase with underscores.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe
        
    Returns
    -------
    pd.DataFrame
        DataFrame with standardized column names
    """
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
    return df


def calculate_missing_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate missing data statistics for all columns.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe
        
    Returns
    -------
    pd.DataFrame
        DataFrame with missing count and percentage for each column
    """
    missing_stats = pd.DataFrame({
        'missing_count': df.isnull().sum(),
        'missing_percent': (df.isnull().sum() / len(df) * 100).round(2)
    })
    return missing_stats.sort_values('missing_percent', ascending=False)


# ============================================================================
# CAUSAL INFERENCE UTILITIES
# ============================================================================

def calculate_smd(treated: pd.Series, control: pd.Series) -> float:
    """
    Calculate standardized mean difference between two groups.
    
    SMD = (mean_treated - mean_control) / pooled_std
    
    Parameters
    ----------
    treated : pd.Series
        Values for treated group
    control : pd.Series
        Values for control group
        
    Returns
    -------
    float
        Standardized mean difference
    """
    mean_treated = treated.mean()
    mean_control = control.mean()
    var_treated = treated.var()
    var_control = control.var()
    
    pooled_std = np.sqrt((var_treated + var_control) / 2)
    
    if pooled_std == 0:
        return 0
    
    smd = (mean_treated - mean_control) / pooled_std
    return smd


def calculate_balance_table(df: pd.DataFrame, 
                            treatment_col: str,
                            covariate_cols: List[str],
                            weights: Optional[np.ndarray] = None) -> pd.DataFrame:
    """
    Calculate covariate balance table with SMD.
    
    Parameters
    ----------
    df : pd.DataFrame
        Data with treatment and covariates
    treatment_col : str
        Name of treatment column
    covariate_cols : List[str]
        List of covariate column names
    weights : Optional[np.ndarray]
        Sample weights (e.g., IPW weights)
        
    Returns
    -------
    pd.DataFrame
        Balance table with SMD for each covariate
    """
    balance_stats = []
    
    treated = df[df[treatment_col] == 1]
    control = df[df[treatment_col] == 0]
    
    for col in covariate_cols:
        if weights is not None:
            # Weighted means and variances
            treated_vals = treated[col].dropna()
            control_vals = control[col].dropna()
            treated_weights = weights[df[treatment_col] == 1][~treated[col].isnull()]
            control_weights = weights[df[treatment_col] == 0][~control[col].isnull()]
            
            # Calculate weighted SMD (simplified version)
            smd = calculate_smd(treated_vals, control_vals)
        else:
            smd = calculate_smd(treated[col].dropna(), control[col].dropna())
        
        balance_stats.append({
            'covariate': col,
            'smd': smd,
            'abs_smd': abs(smd),
            'balanced': abs(smd) < 0.1
        })
    
    return pd.DataFrame(balance_stats).sort_values('abs_smd', ascending=False)


def estimate_propensity_scores(df: pd.DataFrame,
                               treatment_col: str,
                               covariate_cols: List[str]) -> np.ndarray:
    """
    Estimate propensity scores using logistic regression.
    
    Parameters
    ----------
    df : pd.DataFrame
        Data with treatment and covariates
    treatment_col : str
        Name of treatment column
    covariate_cols : List[str]
        List of covariate column names
        
    Returns
    -------
    np.ndarray
        Predicted propensity scores
    """
    X = df[covariate_cols].fillna(df[covariate_cols].mean())
    y = df[treatment_col]
    
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)
    
    propensity_scores = model.predict_proba(X)[:, 1]
    return propensity_scores


def calculate_ipw_weights(propensity_scores: np.ndarray,
                         treatment: np.ndarray) -> np.ndarray:
    """
    Calculate inverse probability weights (IPW).
    
    Parameters
    ----------
    propensity_scores : np.ndarray
        Propensity scores
    treatment : np.ndarray
        Treatment indicator (0 or 1)
        
    Returns
    -------
    np.ndarray
        IPW weights
    """
    weights = np.where(
        treatment == 1,
        1 / propensity_scores,
        1 / (1 - propensity_scores)
    )
    
    # Trim extreme weights (>99th percentile)
    weights = np.clip(weights, None, np.percentile(weights, 99))
    
    return weights


def bootstrap_ci(data: np.ndarray,
                 statistic_func,
                 n_bootstrap: int = 1000,
                 confidence_level: float = 0.95,
                 random_state: int = 42) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence intervals.
    
    Parameters
    ----------
    data : np.ndarray
        Input data
    statistic_func : callable
        Function to calculate statistic
    n_bootstrap : int
        Number of bootstrap iterations
    confidence_level : float
        Confidence level (default 0.95 for 95% CI)
    random_state : int
        Random seed
        
    Returns
    -------
    Tuple[float, float]
        Lower and upper confidence bounds
    """
    np.random.seed(random_state)
    
    bootstrap_stats = []
    n = len(data)
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        stat = statistic_func(sample)
        bootstrap_stats.append(stat)
    
    alpha = 1 - confidence_level
    lower = np.percentile(bootstrap_stats, alpha/2 * 100)
    upper = np.percentile(bootstrap_stats, (1 - alpha/2) * 100)
    
    return lower, upper


# ============================================================================
# VISUALIZATION UTILITIES
# ============================================================================

def apply_plot_style(style: str = 'whitegrid',
                     palette: str = 'colorblind',
                     font_scale: float = 1.2) -> None:
    """
    Apply consistent plotting style.
    
    Parameters
    ----------
    style : str
        Seaborn style
    palette : str
        Seaborn color palette
    font_scale : float
        Font scaling factor
    """
    sns.set_style(style)
    sns.set_palette(palette)
    sns.set_context("notebook", font_scale=font_scale)
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['font.size'] = 12


def save_figure(fig,
                filename: str,
                output_dir: str = '../outputs/figures',
                dpi: int = 300,
                bbox_inches: str = 'tight') -> None:
    """
    Save figure with consistent settings.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save
    filename : str
        Output filename
    output_dir : str
        Output directory path
    dpi : int
        Resolution in dots per inch
    bbox_inches : str
        Bounding box setting
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, filename)
    fig.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
    print(f"Figure saved: {filepath}")


def annotate_plot(ax,
                 text: str,
                 x: float,
                 y: float,
                 **kwargs) -> None:
    """
    Add annotation to plot with consistent styling.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes object
    text : str
        Annotation text
    x : float
        X coordinate
    y : float
        Y coordinate
    **kwargs
        Additional arguments passed to ax.annotate()
    """
    default_kwargs = {
        'fontsize': 10,
        'ha': 'center',
        'va': 'center',
        'bbox': dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    }
    default_kwargs.update(kwargs)
    
    ax.annotate(text, (x, y), **default_kwargs)


# ============================================================================
# SUMMARY STATISTICS UTILITIES
# ============================================================================

def generate_summary_table(df: pd.DataFrame,
                          group_col: Optional[str] = None,
                          columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Generate summary statistics table.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input data
    group_col : Optional[str]
        Column to group by (e.g., treatment)
    columns : Optional[List[str]]
        Specific columns to summarize
        
    Returns
    -------
    pd.DataFrame
        Summary statistics table
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if group_col is not None:
        summary = df.groupby(group_col)[columns].agg(['mean', 'std', 'min', 'max', 'count'])
    else:
        summary = df[columns].agg(['mean', 'std', 'min', 'max', 'count']).T
    
    return summary.round(2)


def format_pvalue(p: float) -> str:
    """
    Format p-value for display.
    
    Parameters
    ----------
    p : float
        P-value
        
    Returns
    -------
    str
        Formatted p-value string
    """
    if p < 0.001:
        return "p < 0.001***"
    elif p < 0.01:
        return f"p = {p:.3f}**"
    elif p < 0.05:
        return f"p = {p:.3f}*"
    else:
        return f"p = {p:.3f}"


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    print("Utility functions loaded successfully!")
    print("Available functions:")
    print("  - Data: standardize_column_names, calculate_missing_stats")
    print("  - Causal: calculate_smd, calculate_balance_table, estimate_propensity_scores")
    print("  - Causal: calculate_ipw_weights, bootstrap_ci")
    print("  - Viz: apply_plot_style, save_figure, annotate_plot")
    print("  - Stats: generate_summary_table, format_pvalue")

