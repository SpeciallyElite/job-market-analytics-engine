import pandas as pd
from extract import fetch_job_data

def transform_data(raw_jobs):
    if not raw_jobs:
        print("No raw data provided to clean.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    print("Cleaning and transforming data into Star Schema with Pandas...")

    # 1. Transform dim_companies
    companies = []
    for job in raw_jobs:
        if isinstance(job, dict) and job.get("company"):
            companies.append({
                "company_name": job.get("company"),
                "company_logo_url": job.get("company_logo")
            })
    df_companies = (
        pd.DataFrame(companies)
        .drop_duplicates(subset=["company_name"])
        .dropna(subset=["company_name"])
    )

    # 2. Transform dim_categories (Extracting & flattening RemoteOK tags)
    categories = []
    for job in raw_jobs:
        if isinstance(job, dict) and job.get("tags"):
            tags = job.get("tags")
            if isinstance(tags, list):
                for tag in tags:
                    categories.append({
                        "category_name": str(tag).strip().lower()
                    })
    df_categories = (
        pd.DataFrame(categories)
        .drop_duplicates(subset=["category_name"])
        .dropna(subset=["category_name"])
    )

    # 3. Transform fct_job_postings
    jobs = []
    for job in raw_jobs:
        if isinstance(job, dict) and job.get("id"):
            # Select primary tag or default category
            primary_tag = None
            tags = job.get("tags")
            if isinstance(tags, list) and len(tags) > 0:
                primary_tag = str(tags[0]).strip().lower()

            jobs.append({
                "job_id": job.get("id"),
                "company_name": job.get("company"),       # Temporary lookup key for load.py
                "category_name": primary_tag,             # Temporary lookup key for load.py
                "title": job.get("position"),
                "publication_date": job.get("date"),
                "candidate_required_location": job.get("location"),
                "url": job.get("url")
                # "job_type": job.get("job_type", "Full Time"),
                # "salary": str(job.get("salary")) if job.get("salary") else "Not Specified",
            })

    df_jobs = pd.DataFrame(jobs).dropna(subset=["job_id", "title"])

    # Apply your Pandas cleaning logic!
    if 'candidate_required_location' in df_jobs.columns:
        df_jobs['candidate_required_location'] = (
            df_jobs['candidate_required_location'].fillna('Remote').replace('', 'Remote')
        )

    if 'publication_date' in df_jobs.columns:
        df_jobs['publication_date'] = pd.to_datetime(df_jobs['publication_date'], errors='coerce')

    print(f"Transformation complete! Cleaned {len(df_companies)} companies, {len(df_categories)} categories, and {len(df_jobs)} jobs.")

    return df_companies, df_categories, df_jobs

if __name__ == "__main__":
    raw_data = fetch_job_data()
    df_comp, df_cat, df_jobs = transform_data(raw_data)
    
    print("\n--- FIRST 5 ROWS OF JOBS FACT TABLE ---")
    print(df_jobs.head())