import os
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0"}
RAW_DATA_PATH = "data/raw_jobs.json"

def get_robust_session():
    """Creates a requests session configured with exponential backoff retries."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

def fetch_job_data():
    logger.info("Starting data extraction from RemoteOK API...")
    session = get_robust_session()
    
    try:
        response = session.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
        
        with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        logger.info(f"Successfully extracted {len(data)} raw records to {RAW_DATA_PATH}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"API Extraction permanently failed after retries: {e}")
        raise

if __name__ == "__main__":
    fetch_job_data()