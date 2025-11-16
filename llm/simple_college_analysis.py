#!/usr/bin/env python3
"""
Simple College Comparison Tool
Analyzes college data without external dependencies
"""

import csv
import sys

def load_college_data(csv_path):
    """Load college data from CSV file"""
    colleges = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                colleges.append(row)
        return colleges
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def safe_float(value):
    """Safely convert string to float"""
    try:
        if value and value.strip() and value != '.':
            return float(value)
    except (ValueError, AttributeError):
        pass
    return None

def analyze_colleges(colleges):
    """Analyze college data and extract key metrics"""
    if not colleges:
        return None
    
    analysis = []
    
    for college in colleges:
        # Extract key metrics
        name = college.get('Institution Name_college', 'Unknown')
        state = college.get('State of Institution', 'Unknown')
        
        # Graduation rate
        grad_rate = safe_float(college.get('Bachelor\'s Degree Graduation Rate Bachelor Degree Within 6 Years - Total'))
        
        # Net price
        net_price = safe_float(college.get('Average Net Price After Grants, 2020-21'))
        
        # Earnings
        earnings = safe_float(college.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry'))
        
        # Gap
        gap = safe_float(college.get('Affordability Gap (net price minus income earned working 10 hrs at min wage)'))
        
        # Only include colleges with at least some data
        if any([grad_rate, net_price, earnings, gap]):
            analysis.append({
                'name': name,
                'state': state,
                'graduation_rate': grad_rate,
                'net_price': net_price,
                'earnings': earnings,
                'gap': gap
            })
    
    return analysis

def get_top_colleges(colleges, metric, n=10, reverse=True):
    """Get top N colleges by a specific metric"""
    # Filter out colleges without the metric
    filtered = [c for c in colleges if c[metric] is not None]
    
    # Sort by metric
    sorted_colleges = sorted(filtered, key=lambda x: x[metric], reverse=reverse)
    
    return sorted_colleges[:n]

def format_currency(value):
    """Format value as currency"""
    if value is None:
        return "N/A"
    return f"${value:,.0f}"

def format_percentage(value):
    """Format value as percentage"""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"

def main():
    print("=== COLLEGE COMPARISON ANALYSIS ===\n")
    
    # Load data
    csv_path = '../fronted/data/merged_clean.csv'
    raw_data = load_college_data(csv_path)
    
    if not raw_data:
        print("Failed to load data")
        return
    
    # Analyze data
    colleges = analyze_colleges(raw_data)
    
    if not colleges:
        print("No valid college data found")
        return
    
    print(f"Loaded data for {len(colleges)} colleges\n")
    
    # Top colleges by graduation rate
    print("1. TOP 10 COLLEGES BY GRADUATION RATE")
    print("=" * 60)
    top_grad = get_top_colleges(colleges, 'graduation_rate', 10, True)
    for i, college in enumerate(top_grad, 1):
        print(f"{i:2d}. {college['name']} ({college['state']})")
        print(f"    Graduation Rate: {format_percentage(college['graduation_rate'])}")
        print(f"    Net Price: {format_currency(college['net_price'])}")
        print(f"    Earnings: {format_currency(college['earnings'])}")
        print()
    
    # Lowest net price colleges
    print("2. TOP 10 COLLEGES WITH LOWEST NET PRICE")
    print("=" * 60)
    low_price = get_top_colleges(colleges, 'net_price', 10, False)
    for i, college in enumerate(low_price, 1):
        print(f"{i:2d}. {college['name']} ({college['state']})")
        print(f"    Net Price: {format_currency(college['net_price'])}")
        print(f"    Graduation Rate: {format_percentage(college['graduation_rate'])}")
        print(f"    Earnings: {format_currency(college['earnings'])}")
        print()
    
    # Highest earnings colleges
    print("3. TOP 10 COLLEGES BY GRADUATE EARNINGS")
    print("=" * 60)
    high_earnings = get_top_colleges(colleges, 'earnings', 10, True)
    for i, college in enumerate(high_earnings, 1):
        print(f"{i:2d}. {college['name']} ({college['state']})")
        print(f"    Earnings: {format_currency(college['earnings'])}")
        print(f"    Net Price: {format_currency(college['net_price'])}")
        print(f"    Graduation Rate: {format_percentage(college['graduation_rate'])}")
        print()
    
    # Smallest affordability gap
    print("4. TOP 10 COLLEGES WITH SMALLEST AFFORDABILITY GAP")
    print("=" * 60)
    small_gap = get_top_colleges(colleges, 'gap', 10, False)
    for i, college in enumerate(small_gap, 1):
        print(f"{i:2d}. {college['name']} ({college['state']})")
        print(f"    Affordability Gap: {format_currency(college['gap'])}")
        print(f"    Net Price: {format_currency(college['net_price'])}")
        print(f"    Graduation Rate: {format_percentage(college['graduation_rate'])}")
        print()
    
    # Sample comparison
    print("5. COMPARISON OF NOTABLE COLLEGES")
    print("=" * 60)
    notable_colleges = ['Harvard University', 'Stanford University', 'MIT', 'Amherst College', 'Babson College']
    
    for target in notable_colleges:
        matches = [c for c in colleges if target.lower() in c['name'].lower()]
        if matches:
            college = matches[0]  # Take first match
            print(f"{college['name']} ({college['state']})")
            print(f"  Graduation Rate: {format_percentage(college['graduation_rate'])}")
            print(f"  Net Price: {format_currency(college['net_price'])}")
            print(f"  Earnings: {format_currency(college['earnings'])}")
            print(f"  Affordability Gap: {format_currency(college['gap'])}")
            print()
    
    print("=== ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    main()