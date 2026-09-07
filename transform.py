import os
import json
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

RAW_DATA_PATH = "data/raw_jobs.json"

def transform_data():
    logger.info("Starting data transformation process...")

    if not os.path.exists(RAW_DATA_PATH):
        logger.error(f"Transformation failed: File {RAW_DATA_PATH} does not exist!")
        raise FileNotFoundError(f"Missing raw data file at {RAW_DATA_PATH}")

    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if not raw_data:
        logger.warning("Raw data file is empty. Returning empty DataFrames.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    jobs_raw = raw_data[1:] if len(raw_data) > 1 and isinstance(raw_data[0], dict) and "legal" in raw_data[0] else raw_data
    logger.info(f"Loaded {len(jobs_raw)} raw job payloads for parsing.")

    companies_list = []
    categories_set = set()
    fact_jobs_list = []
    skipped_count = 0

    for idx, job in enumerate(jobs_raw):
        try:
            if not isinstance(job, dict):
                logger.warning(f"Row #{idx}: Record is not a valid JSON dictionary. Skipping.")
                skipped_count += 1
                continue

            company_name = job.get("company")
            job_id = job.get("id")

            if not company_name or not str(company_name).strip():
                logger.warning(f"Row #{idx}: Missing company name. Skipping record.")
                skipped_count += 1
                continue

            if not job_id:
                logger.warning(f"Row #{idx}: Missing job ID for company '{company_name}'. Skipping record.")
                skipped_count += 1
                continue

            companies_list.append({
                "company_name": str(company_name).strip(),
                "company_logo_url": str(job.get("company_logo", "")).strip()
            })

            tags = job.get("tags", [])
            primary_tag = None
            if isinstance(tags, list):
                for tag in tags:
                    if tag and str(tag).strip():
                        cleaned_tag = str(tag).strip().lower()
                        categories_set.add(cleaned_tag)
                        if not primary_tag:
                            primary_tag = cleaned_tag  

            fact_jobs_list.append({
                "job_id": job_id,
                "company_name": str(company_name).strip(),
                "category_name": primary_tag,
                "title": str(job.get("position", "Unknown Position")).strip(),
                "publication_date": job.get("date"),
                "candidate_required_location": str(job.get("location", "Remote")).strip(),
                "url": str(job.get("url", "")).strip()
            })

        except Exception as e:
            logger.warning(f"Row #{idx}: Unexpected error parsing record (ID: {job.get('id', 'Unknown')}): {e}. Skipping.")
            skipped_count += 1
            continue

    df_companies = (
        pd.DataFrame(companies_list)
        .drop_duplicates(subset=["company_name"])
        .dropna(subset=["company_name"])
    ) if companies_list else pd.DataFrame()

    df_categories = (
        pd.DataFrame([{"category_name": c} for c in categories_set])
        .drop_duplicates(subset=["category_name"])
        .dropna(subset=["category_name"])
    ) if categories_set else pd.DataFrame()

    df_jobs = pd.DataFrame(fact_jobs_list) if fact_jobs_list else pd.DataFrame()

    if not df_jobs.empty:
        if 'candidate_required_location' in df_jobs.columns:
            df_jobs['candidate_required_location'] = (
                df_jobs['candidate_required_location'].fillna('Remote').replace('', 'Remote')
            )

        if 'publication_date' in df_jobs.columns:
            df_jobs['publication_date'] = pd.to_datetime(df_jobs['publication_date'], errors='coerce')

        df_jobs = df_jobs.dropna(subset=["job_id", "title"])

    logger.info(
        f"Transformation complete! Processed: {len(df_jobs)} valid jobs, "
        f"{len(df_companies)} companies, {len(df_categories)} categories | Skipped: {skipped_count} bad rows."
    )

    return df_companies, df_categories, df_jobs

if __name__ == "__main__":
    df_comp, df_cat, df_j = transform_data()
    print("\n--- FIRST 5 ROWS OF JOBS FACT TABLE ---")
    print(df_j.head())