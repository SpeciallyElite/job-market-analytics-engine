import os
import logging
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from extract import fetch_job_data
from transform import transform_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("load")

load_dotenv(override=True)

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rootpassword")
DB_HOST = os.getenv("DB_HOST", "de_postgres_container")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "de_database")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def load_data():
    logger.info("Running the extraction:")
    fetch_job_data()

    logger.info("Starting database load process...")
    df_companies, df_categories, df_jobs = transform_data()

    if df_jobs.empty:
        logger.warning("No valid job data to load into PostgreSQL. Exiting load step.")
        return

    try:
        engine = create_engine(DB_URL)
        
        with engine.begin() as conn:
            logger.info("Database connection established. Starting transaction...")

            logger.info(f"Upserting {len(df_companies)} companies into dim_companies...")
            for _, row in df_companies.iterrows():
                conn.execute(
                    text("""
                        INSERT INTO dim_companies (company_name, company_logo_url)
                        VALUES (:company_name, :company_logo_url)
                        ON CONFLICT (company_name) DO UPDATE
                        SET company_logo_url = EXCLUDED.company_logo_url;
                    """),
                    {
                        "company_name": row["company_name"],
                        "company_logo_url": row["company_logo_url"]
                    }
                )

            logger.info(f"Upserting {len(df_categories)} categories into dim_categories...")
            for _, row in df_categories.iterrows():
                conn.execute(
                    text("""
                        INSERT INTO dim_categories (category_name)
                        VALUES (:category_name)
                        ON CONFLICT (category_name) DO NOTHING;
                    """),
                    {"category_name": row["category_name"]}
                )

            logger.info("Fetching dimension IDs for fact table foreign key mappings...")
            comp_map = pd.read_sql("SELECT company_id, company_name FROM dim_companies;", conn) \
                        .set_index("company_name")["company_id"].to_dict()
            
            cat_map = pd.read_sql("SELECT category_id, category_name FROM dim_categories;", conn) \
                        .set_index("category_name")["category_id"].to_dict()

            logger.info(f"Upserting {len(df_jobs)} jobs into fct_job_postings...")
            inserted_jobs = 0
            for _, row in df_jobs.iterrows():
                company_id = comp_map.get(row["company_name"])
                category_id = cat_map.get(row["category_name"])

                if not company_id:
                    logger.warning(f"Skipping job ID {row['job_id']}: Company '{row['company_name']}' ID not found.")
                    continue

                conn.execute(
                    text("""
                        INSERT INTO fct_job_postings (
                            source_job_id, company_id, category_id, title,
                            publication_date, candidate_required_location, url
                        )
                        VALUES (
                            :source_job_id, :company_id, :category_id, :title,
                            :publication_date, :candidate_required_location, :url
                        )
                        ON CONFLICT (source_job_id) DO UPDATE SET
                            company_id = EXCLUDED.company_id,
                            category_id = EXCLUDED.category_id,
                            title = EXCLUDED.title,
                            publication_date = EXCLUDED.publication_date,
                            candidate_required_location = EXCLUDED.candidate_required_location,
                            url = EXCLUDED.url;
                    """),
                    {
                        "source_job_id": row["job_id"],
                        "company_id": company_id,
                        "category_id": category_id,
                        "title": row["title"],
                        "publication_date": row["publication_date"],
                        "candidate_required_location": row["candidate_required_location"],
                        "url": row["url"]
                    }
                )
                inserted_jobs += 1

            logger.info(f"Successfully committed transaction! Loaded {inserted_jobs} job records to database.")

    except Exception as e:
        logger.error(f"Database transaction failed! All changes rolled back automatically. Error: {e}")
        raise e

if __name__ == "__main__":
    load_data()