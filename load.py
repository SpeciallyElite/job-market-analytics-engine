import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from transform import transform_data
from extract import fetch_job_data

def load_data_to_postgres(df_companies, df_categories, df_jobs):
    if df_companies.empty or df_jobs.empty:
        print("DataFrames are empty. Nothing to load into database.")
        return

    load_dotenv()

    # Matching environment variables with local fallbacks
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5433")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
    DB_NAME = os.getenv("DB_NAME", "de_database")

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    print("Connecting to PostgreSQL database...")
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        # 1. Load dim_companies & capture company_id mapping
        company_id_map = {}
        print(f"Loading {len(df_companies)} companies into 'dim_companies'...")
        for _, row in df_companies.iterrows():
            result = conn.execute(
                text("""
                    INSERT INTO dim_companies (company_name, company_logo_url)
                    VALUES (:name, :logo)
                    ON CONFLICT (company_name) DO UPDATE
                    SET company_logo_url = EXCLUDED.company_logo_url
                    RETURNING company_id, company_name;
                """),
                {"name": row["company_name"], "logo": row["company_logo_url"]}
            )
            c_id, c_name = result.fetchone()
            company_id_map[c_name] = c_id

        # 2. Load dim_categories & capture category_id mapping
        category_id_map = {}
        print(f"Loading {len(df_categories)} categories into 'dim_categories'...")
        for _, row in df_categories.iterrows():
            result = conn.execute(
                text("""
                    INSERT INTO dim_categories (category_name)
                    VALUES (:cat_name)
                    ON CONFLICT (category_name) DO UPDATE
                    SET category_name = EXCLUDED.category_name
                    RETURNING category_id, category_name;
                """),
                {"cat_name": row["category_name"]}
            )
            cat_id, cat_name = result.fetchone()
            category_id_map[cat_name] = cat_id

        # 3. Prepare Fact table records using mapped Foreign Keys
        print(f"Loading {len(df_jobs)} jobs into 'fct_job_postings'...")
        for _, row in df_jobs.iterrows():
            c_id = company_id_map.get(row["company_name"])
            cat_id = category_id_map.get(row["category_name"])

            pub_date = row["publication_date"]
            pub_date_val = None if pd.isna(pub_date) else pub_date

            conn.execute(
                text("""
                    INSERT INTO fct_job_postings (
                        source_job_id, company_id, category_id, title,
                        publication_date, candidate_required_location, url
                    ) VALUES (
                        :source_job_id, :company_id, :category_id, :title,
                        :publication_date, :candidate_required_location, :url
                    )
                    ON CONFLICT (source_job_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        url = EXCLUDED.url;
                """),
                {
                    "source_job_id": row["job_id"],
                    "company_id": c_id,
                    "category_id": cat_id,
                    "title": row["title"],
                    "publication_date": pub_date_val,
                    "candidate_required_location": row["candidate_required_location"],
                    "url": row["url"]
                    # "job_type": row["job_type"],
                    # "salary": row["salary"],
                }
            )

    print("Successfully loaded Star Schema data into PostgreSQL!")

if __name__ == "__main__":
    raw_data = fetch_job_data()
    df_companies, df_categories, df_jobs = transform_data(raw_data)
    load_data_to_postgres(df_companies, df_categories, df_jobs)