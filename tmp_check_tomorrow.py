
import os
import json
from datetime import date, timedelta
from garminconnect import Garmin

SESSION_FILE = "session.json"

def get_garmin_client() -> Garmin:
    garmin_api = Garmin()
    garmin_api.garth.load(SESSION_FILE)
    return garmin_api

def main():
    try:
        client = get_garmin_client()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        # El mètode per obtenir el calendari pot variar segons la versió de la llibreria
        # Intentem obtenir activitats planejades
        print(f"Checking calendar for {tomorrow}...")
        
        # En algunes versions és get_calendar_activities
        try:
            calendar = client.get_calendar_activities(tomorrow, tomorrow)
            print("Calendar activities:")
            print(json.dumps(calendar, indent=2))
        except Exception as e:
            print(f"Error get_calendar_activities: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
