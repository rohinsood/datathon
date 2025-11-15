"""
Data Preparation Script
=======================

Loads, cleans, and merges Affordability Gap and College Results data.

Outputs:
- outputs/data/merged_clean.csv
- outputs/logs/01_data_preparation.log
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR
OUTPUT_DIR = ROOT_DIR / 'outputs' / 'data'
LOG_DIR = ROOT_DIR / 'outputs' / 'logs'

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / '01_data_preparation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_data():
    """Load both datasets."""
    logger.info("="*80)
    logger.info("LOADING DATA")
    logger.info("="*80)
    
    # Load Affordability Gap Data
    affordability_file = DATA_DIR / 'Affordability Gap Data AY2022-23 2.17.25.xlsx - Affordability_latest_02-17-25 1.csv'
    logger.info(f"Loading Affordability Gap data from: {affordability_file}")
    
    df_affordability = pd.read_csv(affordability_file, low_memory=False)
    logger.info(f"✓ Affordability data loaded: {df_affordability.shape}")
    
    # Load College Results Data
    college_file = DATA_DIR / 'College Results View 2021 Data Dump for Export.xlsx - College Results View 2021 Data .csv'
    logger.info(f"Loading College Results data from: {college_file}")
    
    df_college = pd.read_csv(college_file, low_memory=False)
    logger.info(f"✓ College Results data loaded: {df_college.shape}")
    
    return df_affordability, df_college


def standardize_institution_ids(df_affordability, df_college):
    """Standardize institution ID column names to 'unit_id'."""
    logger.info("\nStandardizing institution ID columns...")
    
    # Affordability data
    df_affordability = df_affordability.rename(columns={'Unit ID': 'unit_id'})
    logger.info(f"✓ Affordability: 'Unit ID' → 'unit_id'")
    
    # College data
    df_college = df_college.rename(columns={
        'UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION': 'unit_id'
    })
    logger.info(f"✓ College Results: 'UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION' → 'unit_id'")
    
    return df_affordability, df_college


def check_for_duplicates(df, name):
    """Check for duplicate unit_ids and investigate."""
    logger.info(f"\n{'='*80}")
    logger.info(f"CHECKING FOR DUPLICATES: {name}")
    logger.info(f"{'='*80}")
    
    total = len(df)
    unique = df['unit_id'].nunique()
    duplicates = total - unique
    
    logger.info(f"Total rows: {total:,}")
    logger.info(f"Unique unit_ids: {unique:,}")
    logger.info(f"Duplicate rows: {duplicates:,} ({duplicates/total*100:.1f}%)")
    
    if duplicates > 0:
        logger.warning(f"⚠ WARNING: {name} has {duplicates:,} duplicate unit_ids!")
        
        # Find example duplicates
        dup_ids = df[df.duplicated('unit_id', keep=False)]['unit_id'].unique()[:3]
        logger.info(f"\nExample duplicate unit_ids: {dup_ids.tolist()}")
        
        # Show what varies for first duplicate
        example_id = dup_ids[0]
        example_rows = df[df['unit_id'] == example_id]
        logger.info(f"\nExample: unit_id={example_id} appears {len(example_rows)} times")
        
        # Show key columns for this duplicate
        key_cols = ['unit_id', 'Institution Name']
        if 'City' in df.columns:
            key_cols.append('City')
        if 'State Abbreviation' in df.columns:
            key_cols.append('State Abbreviation')
        
        available_cols = [c for c in key_cols if c in df.columns]
        logger.info(f"\nDuplicate rows for {example_id}:")
        for idx, row in example_rows[available_cols].head().iterrows():
            logger.info(f"  {dict(row)}")
        
        return True, duplicates
    else:
        logger.info(f"✓ No duplicates found")
        return False, 0


def deduplicate_affordability(df_affordability):
    """
    Remove duplicates from affordability data.
    Strategy: Keep first occurrence of each unit_id.
    """
    logger.info(f"\n{'='*80}")
    logger.info("DEDUPLICATING AFFORDABILITY DATA")
    logger.info(f"{'='*80}")
    
    before = len(df_affordability)
    
    # Keep first occurrence of each unit_id
    df_clean = df_affordability.drop_duplicates(subset='unit_id', keep='first').copy()
    
    after = len(df_clean)
    removed = before - after
    
    logger.info(f"Before deduplication: {before:,} rows")
    logger.info(f"After deduplication: {after:,} rows")
    logger.info(f"Removed: {removed:,} duplicate rows")
    
    return df_clean


def filter_to_4year(df_affordability, df_college):
    """Filter both datasets to 4-year bachelor's-granting institutions."""
    logger.info(f"\n{'='*80}")
    logger.info("FILTERING TO 4-YEAR INSTITUTIONS")
    logger.info(f"{'='*80}")
    
    # Filter Affordability data
    logger.info(f"\nAffordability data:")
    logger.info(f"  Before filtering: {len(df_affordability):,}")
    
    if 'Highest Degree Offered Name' in df_affordability.columns:
        df_aff_4yr = df_affordability[
            df_affordability['Highest Degree Offered Name'].isin([
                "Bachelor's degree",
                "Master's degree",
                "Doctor's degree - research/scholarship",
                "Doctor's degree -  professional practice",
                "Doctor's degree - research/scholarship and professional practice"
            ])
        ].copy()
    elif 'Institution Level Name' in df_affordability.columns:
        df_aff_4yr = df_affordability[
            df_affordability['Institution Level Name'] == 'Four or more years'
        ].copy()
    else:
        logger.warning("Could not find filtering column, using all data")
        df_aff_4yr = df_affordability.copy()
    
    logger.info(f"  After filtering: {len(df_aff_4yr):,}")
    logger.info(f"  Removed: {len(df_affordability) - len(df_aff_4yr):,}")
    
    # Filter College Results data
    logger.info(f"\nCollege Results data:")
    logger.info(f"  Before filtering: {len(df_college):,}")
    
    if 'Number of Bachelor Degrees Grand Total' in df_college.columns:
        df_college_4yr = df_college[
            df_college['Number of Bachelor Degrees Grand Total'].notna() &
            (df_college['Number of Bachelor Degrees Grand Total'] > 0)
        ].copy()
    else:
        logger.warning("Could not find filtering column, using all data")
        df_college_4yr = df_college.copy()
    
    logger.info(f"  After filtering: {len(df_college_4yr):,}")
    logger.info(f"  Removed: {len(df_college) - len(df_college_4yr):,}")
    
    return df_aff_4yr, df_college_4yr


def merge_datasets(df_affordability, df_college):
    """Merge datasets on unit_id."""
    logger.info(f"\n{'='*80}")
    logger.info("MERGING DATASETS")
    logger.info(f"{'='*80}")
    
    n_aff = len(df_affordability)
    n_college = len(df_college)
    
    logger.info(f"\nBefore merge:")
    logger.info(f"  Affordability: {n_aff:,} institutions")
    logger.info(f"  College Results: {n_college:,} institutions")
    
    # Inner join
    df_merged = pd.merge(
        df_affordability,
        df_college,
        on='unit_id',
        how='inner',
        suffixes=('_affordability', '_college')
    )
    
    n_merged = len(df_merged)
    merge_rate_aff = (n_merged / n_aff * 100) if n_aff > 0 else 0
    merge_rate_college = (n_merged / n_college * 100) if n_college > 0 else 0
    
    logger.info(f"\nAfter merge:")
    logger.info(f"  Merged: {n_merged:,} institutions")
    logger.info(f"  Merge rate (from Affordability): {merge_rate_aff:.1f}%")
    logger.info(f"  Merge rate (from College): {merge_rate_college:.1f}%")
    logger.info(f"  Total columns: {df_merged.shape[1]}")
    
    # Verify 1:1 merge
    if merge_rate_college > 100:
        logger.error(f"✗ MERGE ERROR: Merge rate > 100% indicates duplicates!")
        raise ValueError("Merge created duplicate rows - check for duplicate unit_ids")
    
    logger.info(f"✓ Merge successful (1:1 relationship verified)")
    
    return df_merged


def filter_required_variables(df_merged):
    """Filter to rows with required variables present."""
    logger.info(f"\n{'='*80}")
    logger.info("FILTERING FOR REQUIRED VARIABLES")
    logger.info(f"{'='*80}")
    
    required_vars = [
        'Affordability Gap (net price minus income earned working 10 hrs at min wage)',
        'Median Earnings of Students Working and Not Enrolled 10 Years After Entry',
        "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"
    ]
    
    initial_n = len(df_merged)
    df_clean = df_merged.copy()
    
    for var in required_vars:
        if var in df_clean.columns:
            before = len(df_clean)
            df_clean = df_clean[df_clean[var].notna()].copy()
            removed = before - len(df_clean)
            logger.info(f"  {var[:50]:<50} Removed: {removed:,}")
    
    final_n = len(df_clean)
    total_removed = initial_n - final_n
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Before filtering: {initial_n:,} institutions")
    logger.info(f"After filtering: {final_n:,} institutions")
    logger.info(f"Total removed: {total_removed:,} ({total_removed/initial_n*100:.1f}%)")
    logger.info(f"{'='*80}")
    
    if final_n < 500:
        logger.warning(f"⚠ WARNING: Final sample ({final_n}) is below minimum (500)")
    else:
        logger.info(f"✓ Final sample size adequate ({final_n:,} >= 500)")
    
    return df_clean


def save_data(df, filename):
    """Save cleaned data."""
    output_path = OUTPUT_DIR / filename
    df.to_csv(output_path, index=False)
    logger.info(f"\n✓ Data saved to: {output_path}")
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    return output_path


def main():
    """Main execution function."""
    try:
        # Load data
        df_affordability, df_college = load_data()
        
        # Standardize IDs
        df_affordability, df_college = standardize_institution_ids(df_affordability, df_college)
        
        # Check for duplicates
        has_dups_aff, _ = check_for_duplicates(df_affordability, "Affordability")
        has_dups_college, _ = check_for_duplicates(df_college, "College Results")
        
        # Deduplicate if needed
        if has_dups_aff:
            df_affordability = deduplicate_affordability(df_affordability)
            # Verify deduplication worked
            check_for_duplicates(df_affordability, "Affordability (after dedup)")
        
        # Filter to 4-year institutions
        df_aff_4yr, df_college_4yr = filter_to_4year(df_affordability, df_college)
        
        # Merge datasets
        df_merged = merge_datasets(df_aff_4yr, df_college_4yr)
        
        # Filter for required variables
        df_clean = filter_required_variables(df_merged)
        
        # Save
        output_path = save_data(df_clean, 'merged_clean.csv')
        
        logger.info(f"\n{'='*80}")
        logger.info("DATA PREPARATION COMPLETE ✓")
        logger.info(f"{'='*80}")
        logger.info(f"Final dataset: {output_path}")
        logger.info(f"Institutions: {len(df_clean):,}")
        logger.info(f"Columns: {df_clean.shape[1]}")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ ERROR: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

