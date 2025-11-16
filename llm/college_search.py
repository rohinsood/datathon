#!/usr/bin/env python3
"""
Interactive College Search and Comparison Tool
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

def search_colleges(colleges, search_term):
    """Search for colleges by name"""
    matches = []
    search_lower = search_term.lower()
    
    for college in colleges:
        name = college.get('Institution Name_college', '').lower()
        if search_lower in name:
            matches.append(college)
    
    return matches

def display_college_info(college):
    """Display detailed information about a college"""
    name = college.get('Institution Name_college', 'Unknown')
    state = college.get('State of Institution', 'Unknown')
    
    print(f"\n{'='*60}")
    print(f"COLLEGE: {name}")
    print(f"STATE: {state}")
    print(f"{'='*60}")
    
    # Key metrics
    metrics = [
        ('Graduation Rate (6 years)', 'Bachelor\'s Degree Graduation Rate Bachelor Degree Within 6 Years - Total', '%'),
        ('Net Price (2020-21)', 'Average Net Price After Grants, 2020-21', '$'),
        ('Graduate Earnings (10 years)', 'Median Earnings of Students Working and Not Enrolled 10 Years After Entry', '$'),
        ('Affordability Gap', 'Affordability Gap (net price minus income earned working 10 hrs at min wage)', '$'),
        ('Admission Rate', 'Total Percent of Applicants Admitted', '%'),
        ('Student-Faculty Ratio', 'Student-to-Faculty Ratio', ':1'),
        ('Total Enrollment', 'Total Enrollment', ''),
        ('In-State Tuition', 'Average In-State Tuition for First-Time, Full-Time Undergraduates', '$'),
        ('Out-of-State Tuition', 'Out-of-State Average Tuition for First-Time, Full-Time Undergraduates', '$'),
    ]
    
    for display_name, column_name, unit in metrics:
        value = safe_float(college.get(column_name))
        if value is not None:
            if unit == '$':
                print(f"{display_name:<30}: ${value:,.0f}")
            elif unit == '%':
                print(f"{display_name:<30}: {value:.1f}%")
            elif unit == ':1':
                print(f"{display_name:<30}: {value:.1f}:1")
            else:
                print(f"{display_name:<30}: {value:,.0f}")
        else:
            print(f"{display_name:<30}: N/A")

def compare_multiple_colleges(colleges_list):
    """Compare multiple colleges side by side"""
    if not colleges_list:
        return
    
    print(f"\n{'='*80}")
    print("COLLEGE COMPARISON")
    print(f"{'='*80}")
    
    # Display names
    print(f"{'Metric':<25}", end="")
    for college in colleges_list:
        name = college.get('Institution Name_college', 'Unknown')[:20]
        print(f"{name:<25}", end="")
    print()
    print("-" * 80)
    
    # Key metrics for comparison
    metrics = [
        ('Graduation Rate (%)', 'Bachelor\'s Degree Graduation Rate Bachelor Degree Within 6 Years - Total'),
        ('Net Price ($)', 'Average Net Price After Grants, 2020-21'),
        ('Earnings ($)', 'Median Earnings of Students Working and Not Enrolled 10 Years After Entry'),
        ('Gap ($)', 'Affordability Gap (net price minus income earned working 10 hrs at min wage)'),
        ('Admission Rate (%)', 'Total Percent of Applicants Admitted'),
        ('Student-Faculty', 'Student-to-Faculty Ratio'),
    ]
    
    for display_name, column_name in metrics:
        print(f"{display_name:<25}", end="")
        for college in colleges_list:
            value = safe_float(college.get(column_name))
            if value is not None:
                if '$' in display_name:
                    print(f"${value:>20,.0f}", end="")
                elif '%' in display_name:
                    print(f"{value:>22.1f}%", end="")
                else:
                    print(f"{value:>23.1f}", end="")
            else:
                print(f"{'N/A':>25}", end="")
        print()

def main():
    print("=== INTERACTIVE COLLEGE SEARCH & COMPARISON ===\n")
    
    # Load data
    csv_path = '../fronted/data/merged_clean.csv'
    colleges = load_college_data(csv_path)
    
    if not colleges:
        print("Failed to load data")
        return
    
    print(f"Loaded data for {len(colleges)} colleges")
    print("\nCommands:")
    print("- Type college name to search")
    print("- Type 'compare' to compare multiple colleges")
    print("- Type 'quit' to exit")
    
    selected_colleges = []
    
    while True:
        print(f"\nSelected for comparison: {len(selected_colleges)} colleges")
        command = input("\nEnter command or college name: ").strip()
        
        if command.lower() == 'quit':
            break
        elif command.lower() == 'compare':
            if selected_colleges:
                compare_multiple_colleges(selected_colleges)
            else:
                print("No colleges selected for comparison")
        elif command.lower() == 'clear':
            selected_colleges = []
            print("Cleared selection")
        elif command:
            # Search for colleges
            matches = search_colleges(colleges, command)
            
            if not matches:
                print(f"No colleges found matching '{command}'")
            elif len(matches) == 1:
                # Single match - display details and add to comparison
                display_college_info(matches[0])
                
                add_to_compare = input("\nAdd to comparison list? (y/n): ").strip().lower()
                if add_to_compare == 'y':
                    selected_colleges.append(matches[0])
                    print("Added to comparison list")
            else:
                # Multiple matches - show list
                print(f"\nFound {len(matches)} matches:")
                for i, college in enumerate(matches[:10], 1):  # Show first 10
                    name = college.get('Institution Name_college', 'Unknown')
                    state = college.get('State of Institution', 'Unknown')
                    print(f"{i:2d}. {name} ({state})")
                
                if len(matches) > 10:
                    print(f"... and {len(matches) - 10} more")
                
                try:
                    choice = input("\nEnter number to view details (or press Enter to skip): ").strip()
                    if choice:
                        idx = int(choice) - 1
                        if 0 <= idx < min(len(matches), 10):
                            display_college_info(matches[idx])
                            
                            add_to_compare = input("\nAdd to comparison list? (y/n): ").strip().lower()
                            if add_to_compare == 'y':
                                selected_colleges.append(matches[idx])
                                print("Added to comparison list")
                except (ValueError, IndexError):
                    print("Invalid selection")

if __name__ == "__main__":
    main()