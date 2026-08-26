-- Drop existing tables if re-running (order matters due to foreign keys)
DROP TABLE IF EXISTS fct_job_postings CASCADE;
DROP TABLE IF EXISTS dim_companies CASCADE;
DROP TABLE IF EXISTS dim_categories CASCADE;

-- 1. Create Dimension: Companies
CREATE TABLE dim_companies (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) UNIQUE NOT NULL,
    company_logo_url TEXT
);

-- 2. Create Dimension: Categories
CREATE TABLE dim_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);

-- 3. Create Fact: Job Postings
CREATE TABLE fct_job_postings (
    job_id SERIAL PRIMARY KEY,
    source_job_id INT UNIQUE NOT NULL,
    company_id INT REFERENCES dim_companies(company_id),
    category_id INT REFERENCES dim_categories(category_id),
    title VARCHAR(255) NOT NULL,
    publication_date TIMESTAMP,
    candidate_required_location VARCHAR(255),
    -- job_type VARCHAR(50),
    -- salary VARCHAR(100),
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);