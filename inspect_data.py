import logging
from garminconnect import Garmin
import os
import json
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SESSION_FILE = "session.json"

def get_garmin_client() -> Garmin:
    if not os.path.exists(SESSION_FILE):
        raise FileNotFoundError("Session file not found.")
    
    garmin_api = Garmin()
    garmin_api.garth.load(SESSION_FILE)
    return garmin_api

def main():
    try:
        client = get_garmin_client()
        today = date.today().isoformat()
        
        print(f"Fetching data for {today}...")
        
        # Try get_training_status
        try:
            status = client.get_training_status(today)
            print("\n--- Training Status ---")
            print(json.dumps(status, indent=2)[:500] + "...") # Print first 500 chars
            if 'vo2Max' in str(status):
                print(">>> VO2Max found in Training Status")
        except Exception as e:
            print(f"Error fetching training status: {e}")

        # Try get_max_metrics
        try:
            metrics = client.get_max_metrics(today)
            print("\n--- Max Metrics ---")
            print(json.dumps(metrics, indent=2))
        except Exception as e:
            print(f"Error fetching max metrics: {e}")

        # Try get_user_summary
        try:
            summary = client.get_user_summary(today)
            print("\n--- User Summary ---")
            print(json.dumps(summary, indent=2)[:500] + "...")
            if 'vo2Max' in str(summary):
                print(">>> VO2Max found in User Summary")
        except Exception as e:
            print(f"Error fetching user summary: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
