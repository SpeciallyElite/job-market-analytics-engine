import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from transform import clean_job_data
from extract import fetch_job_data

def load_data_to_postgres(df, table_name="remote_jobs"):
    if df.empty:
        print("DataFrame is empty. Nothing to load into database.")
        return

    load_dotenv()

    # we are matching what we have in here to the docker yml. that (x, "localhost") is a fallback bro
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5433")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
    DB_NAME = os.getenv("DB_NAME", "de_database")

    # dynamic connection for cleanliness you kno what i mean dawg?
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    print("Connecting to PostgreSQL database...")
    engine = create_engine(DATABASE_URL)

    # writing the dataframe to the sql table
    print(f"Loading {len(df)} rows into table '{table_name}'...")
    
    # if_exists='replace': remmeber that it dletes tables if it exists and creates a new one
    # if_exists='append': adds/appends a new row to the existing table, whatever you wanna call it
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists='replace',
        index=False  # originally panda has its own column which we don't need 0, 1, 2 like that so we remove it with this command
    )

    print(f"Successfully loaded data into PostgreSQL table: '{table_name}'!")

if __name__ == "__main__":
    raw_data = fetch_job_data()
    
    cleaned_df = clean_job_data(raw_data)
    
    load_data_to_postgres(cleaned_df)



