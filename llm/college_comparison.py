#!/usr/bin/env python3
"""
College Comparison Tool
Analyzes college data to provide key metrics comparison
"""

import pandas as pd
import numpy as np

def load_and_analyze_colleges(csv_path):
    """Load college data and perform basic analysis"""
    try:
        # Load the data
        df = pd.read_csv(csv_path)
        
        # Key columns for analysis (based on your description)
        key_metrics = {
            'Institution Name_college': 'College Name',
            'State of Institution': 'State', 
            'Bachelor\'s Degree Graduation Rate Bachelor Degree Within 6 Years - Total': 'Graduation Rate (%)',
            'Average Net Price After Grants, 2020-21': 'Net Price ($)',
            'Median Earnings of Students Working and Not Enrolled 10 Years After Entry': 'Earnings ($)',
            'Affordability Gap (net price minus income earned working 10 hrs at min wage)': 'Gap ($)'
        }
        
        # Select and rename columns
        analysis_df = df[list(key_metrics.keys())].copy()
        analysis_df.columns = list(key_metrics.values())
        
        # Clean and convert data types
        analysis_df['Graduation Rate (%)'] = pd.to_numeric(analysis_df['Graduation Rate (%)'], errors='coerce')
        analysis_df['Net Price ($)'] = pd.to_numeric(analysis_df['Net Price ($)'], errors='coerce')
        analysis_df['Earnings ($)'] = pd.to_numeric(analysis_df['Earnings ($)'], errors='coerce')
        analysis_df['Gap ($)'] = pd.to_numeric(analysis_df['Gap ($)'], errors='coerce')
        
        # Remove rows with all NaN values for key metrics
        analysis_df = analysis_df.dropna(subset=['Graduation Rate (%)', 'Net Price ($)', 'Earnings ($)', 'Gap ($)'], how='all')
        
        return analysis_df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def get_top_colleges_by_metric(df, metric, top_n=10, ascending=False):
    """Get top colleges by a specific metric"""
    if df is None or metric not in df.columns:
        return None
    
    return df.nlargest(top_n, metric) if not ascending else df.nsmallest(top_n, metric)

def compare_colleges(df, college_names):
    """Compare specific colleges"""
    if df is None:
        return None
    
    # Filter for specified colleges
    comparison = df[df['College Name'].str.contains('|'.join(college_names), case=False, na=False)]
    return comparison

def generate_summary_stats(df):
    """Generate summary statistics"""
    if df is None:
        return None
    
    numeric_cols = ['Graduation Rate (%)', 'Net Price ($)', 'Earnings ($)', 'Gap ($)']
    summary = df[numeric_cols].describe()
    return summary

def main():
    # Load and analyze the data
    csv_path = '../fronted/data/merged_clean.csv'
    df = load_and_analyze_colleges(csv_path)
    
    if df is None:
        print("Failed to load data")
        return
    
    print("=== COLLEGE COMPARISON ANALYSIS ===\n")
    
    # Summary statistics
    print("1. SUMMARY STATISTICS")
    print("=" * 50)
    summary = generate_summary_stats(df)
    if summary is not None:
        print(summary.round(2))
    print("\n")
    
    # Top colleges by graduation rate
    print("2. TOP 10 COLLEGES BY GRADUATION RATE")
    print("=" * 50)
    top_grad = get_top_colleges_by_metric(df, 'Graduation Rate (%)', 10)
    if top_grad is not None:
        for idx, row in top_grad.iterrows():
            print(f"{row['College Name']} ({row['State']}): {row['Graduation Rate (%)']}%")
    print("\n")
    
    # Colleges with lowest net price
    print("3. TOP 10 COLLEGES WITH LOWEST NET PRICE")
    print("=" * 50)
    low_price = get_top_colleges_by_metric(df, 'Net Price ($)', 10, ascending=True)
    if low_price is not None:
        for idx, row in low_price.iterrows():
            print(f"{row['College Name']} ({row['State']}): ${row['Net Price ($)']:,.0f}")
    print("\n")
    
    # Colleges with highest earnings
    print("4. TOP 10 COLLEGES BY GRADUATE EARNINGS")
    print("=" * 50)
    high_earnings = get_top_colleges_by_metric(df, 'Earnings ($)', 10)
    if high_earnings is not None:
        for idx, row in high_earnings.iterrows():
            earnings = row['Earnings ($)']
            if pd.notna(earnings):
                print(f"{row['College Name']} ({row['State']}): ${earnings:,.0f}")
    print("\n")
    
    # Colleges with smallest affordability gap
    print("5. TOP 10 COLLEGES WITH SMALLEST AFFORDABILITY GAP")
    print("=" * 50)
    small_gap = get_top_colleges_by_metric(df, 'Gap ($)', 10, ascending=True)
    if small_gap is not None:
        for idx, row in small_gap.iterrows():
            gap = row['Gap ($)']
            if pd.notna(gap):
                print(f"{row['College Name']} ({row['State']}): ${gap:,.0f}")
    print("\n")
    
    # Sample comparison of specific colleges mentioned in your data
    print("6. COMPARISON OF SELECTED COLLEGES")
    print("=" * 50)
    sample_colleges = ['Amherst College', 'American International College', 'Babson College', 'Harvard University']
    comparison = compare_colleges(df, sample_colleges)
    if comparison is not None and not comparison.empty:
        print(comparison.to_string(index=False))
    
    print("\n=== ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    main()