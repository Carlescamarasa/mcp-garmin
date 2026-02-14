import logging
from garminconnect import Garmin
import os
import json
from datetime import date, timedelta
import csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SESSION_FILE = "session.json"
OUTPUT_FILE = "vo2max_history.csv"

def get_garmin_client() -> Garmin:
    if not os.path.exists(SESSION_FILE):
        raise FileNotFoundError("Session file not found.")
    
    garmin_api = Garmin()
    garmin_api.garth.load(SESSION_FILE)
    return garmin_api

def main():
    try:
        client = get_garmin_client()
        
        # Calculate dates
        end_date = date.today()
        start_date = end_date - timedelta(days=365 * 4) # 4 years
        
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        print(f"Fetching VO2Max data from {start_str} to {end_str}...")
        
        # The URL seems to be /metrics-service/metrics/maxmet/daily/{start}/{end}
        # We need to construct this URL. 
        # In the library it is client.garmin_connect_metrics_url which is "/metrics-service/metrics/maxmet/daily"
        # So we append start and end date.
        
        url = f"/metrics-service/metrics/maxmet/daily/{start_str}/{end_str}"
        
        try:
            data = client.connectapi(url)
            
            if not isinstance(data, list):
                print(f"Unexpected data format: {type(data)}")
                return
            
            print(f"Received {len(data)} records.")
            
            vo2max_data = []
            
            for record in data:
                generic = record.get("generic", {})
                date_val = generic.get("calendarDate")
                vo2_precise = generic.get("vo2MaxPreciseValue")
                vo2_int = generic.get("vo2MaxValue")
                
                if date_val and (vo2_precise or vo2_int):
                    vo2max_data.append({
                        "date": date_val,
                        "vo2MaxPrecise": vo2_precise,
                        "vo2MaxInteger": vo2_int
                    })
            
            # Sort by date
            vo2max_data.sort(key=lambda x: x["date"])
            
            # Write to CSV
            with open(OUTPUT_FILE, 'w', newline='') as csvfile:
                fieldnames = ['date', 'vo2MaxPrecise', 'vo2MaxInteger']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in vo2max_data:
                    writer.writerow(row)
            
            print(f"Saved {len(vo2max_data)} records to {OUTPUT_FILE}")
            
            # Print evolution summary
            if vo2max_data:
                first = vo2max_data[0]
                last = vo2max_data[-1]
                values = [x['vo2MaxPrecise'] for x in vo2max_data if x['vo2MaxPrecise'] is not None]
                if not values:
                     values = [x['vo2MaxInteger'] for x in vo2max_data if x['vo2MaxInteger'] is not None]

                if values:
                    min_val = min(values)
                    max_val = max(values)
                    avg_val = sum(values) / len(values)
                    
                    print("\n--- Summary ---")
                    print(f"Start ({first['date']}): {first.get('vo2MaxPrecise') or first.get('vo2MaxInteger')}")
                    print(f"End ({last['date']}): {last.get('vo2MaxPrecise') or last.get('vo2MaxInteger')}")
                    print(f"Min: {min_val}")
                    print(f"Max: {max_val}")
                    print(f"Average: {avg_val:.2f}")
                    
                    # Print monthly averages for evolution
                    # ... simple listing for now
                    print("\n--- Yearly Evolution ---")
                    current_year = None
                    for row in vo2max_data:
                        year = row['date'][:4]
                        if year != current_year:
                            current_year = year
                            val = row.get('vo2MaxPrecise') or row.get('vo2MaxInteger')
                            print(f"{year}: Started/Recorded at {val}")

        except Exception as e:
            print(f"Error fetching data: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
