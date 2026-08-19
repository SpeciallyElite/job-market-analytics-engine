import pandas as pd
from extract import fetch_job_data

def clean_job_data(raw_jobs):
    if not raw_jobs:
        print("No raw data provided to clean.")
        return pd.DataFrame() #reutrns empty dataframe, we return a dataframe because that's what our next script load is gonna be taking

    print("Cleaning and transforming data with Pandas...")

    # converts the raw job dictionaries into a dataframe from
    df = pd.DataFrame(raw_jobs)

    selected_columns = ['company', 'position', 'location', 'tags', 'date']
    
    # now we filter the dataframe to keep only existing selected columns
    # alternative (fast)
    # df = df[[col for col in selected_columns if col in df.columns]]
    existing_cols = []
    for col in selected_columns:
        if col in df.columns:
            existing_cols.append(col)

    df = df[existing_cols]

    # filling empty or null locations with "remote"
    if 'location' in df.columns:
        df['location'] = df['location'].fillna('Remote')
        df['location'] = df['location'].replace('', 'Remote')

    # from ['python', 'sql'] to 'python, sql'
    if 'tags' in df.columns:
        df['tags'] = df['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')

    # from iso timestamp to (YYYY-MM-DD)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    print(f"Transformation complete! Cleaned {len(df)} rows.")
    
    return df

if __name__ == "__main__":
    raw_data = fetch_job_data()
    
    cleaned_df = clean_job_data(raw_data)
    
    print("\n--- FIRST 5 ROWS OF CLEANED DATA TABLE ---")
    print(cleaned_df.head())           #gives teh first 5 rows