import requests
import json

def fetch_job_data():
    url = "https://remoteok.com/api"
    
                # who is asking for data
                # can get this form google browser just search "my user agent"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    print("Fetching data from API...")
    
    # sending HTTP GET request to the site
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # connverting raw json response data  into a pythonb list of dictionaries
        jobs_data = response.json()
        
        # this is very important - RemoteOK returns metadata in index 0, so jobs start at index 1
        jobs_list = jobs_data[1:]
        
        print(f"Successfully fetched {len(jobs_list)} raw job postings!")
        
        # Inspect the very first job posting to see what raw fields we received
        print("\n--- SAMPLE RAW JOB POSTING ---")
        print(json.dumps(jobs_list[1], indent=4))
        
        return jobs_list
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return []

if __name__ == "__main__":
    raw_jobs = fetch_job_data()