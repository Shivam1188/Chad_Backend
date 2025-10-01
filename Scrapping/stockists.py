import requests
import json
import pandas as pd

def get_stockist_api_data():
    widget_tag = "map_p3xg5y6q"   
    api_url = f"https://stockist.co/api/v1/{widget_tag}/locations/all"
    
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    return None

def save_to_excel(data, filename="stockist_data.xlsx"):
    if isinstance(data, dict) and "locations" in data:
        records = data["locations"]
    elif isinstance(data, list):
        records = data
    else:
        records = [data]

    df = pd.json_normalize(records)
    
    df.to_excel(filename, index=False)
    print(f"✅ Data saved to {filename}")

data = get_stockist_api_data()
if data:
    save_to_excel(data)
else:
    print("❌ Failed to fetch data")
