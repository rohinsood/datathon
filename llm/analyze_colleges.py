import pandas as pd

# Read the CSV file
df = pd.read_csv('../fronted/data/merged_clean.csv')

# Get basic info about the dataset
print("Dataset shape:", df.shape)
print("\nColumn names (first 20):")
print(df.columns[:20].tolist())

# Focus on key metrics - find relevant columns
key_columns = []
for col in df.columns:
    if any(keyword in col.lower() for keyword in ['name', 'net price', 'graduation', 'cost', 'tuition', 'hbcu']):
        key_columns.append(col)

print("\nKey columns found:")
for col in key_columns:
    print(f"- {col}")

# Show first few rows of key data
if 'Institution Name_college' in df.columns:
    print("\nFirst 5 institutions:")
    print(df[['Institution Name_college', 'State of Institution']].head())