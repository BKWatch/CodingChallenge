import pandas as pd
import json
def process_data(input_file):
    # Read the TSV file into a DataFrame
    df = pd.read_csv(input_file, sep='\t')
    
    # Fill missing values with empty strings
    df.fillna('', inplace=True)
    
    # Update 'organization' column if 'last' contains 'LLC' 
    # formatting is not correct. So it has to be tweaked
    mask = df['last'].str.contains('Inc\.|Ltd\.|LLC', case=False)
    df.loc[mask, 'organization'] = df.loc[mask, 'last']
    df.loc[mask, 'last'] = ''
    
    return df

def main():
    input_file = 'input/input2.tsv'
    processed_data = process_data(input_file)
    data = processed_data.to_dict(orient='records')
    print(json.dumps(data, indent=2))
if __name__ == "__main__":
    main()