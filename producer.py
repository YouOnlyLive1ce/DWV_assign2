import polars as pl
import random
import requests
import asyncio

class Producer:
    def __init__(self):
        self.df = pl.read_csv('ip_addresses.csv')
        self.max_latency = 1
        self.url = 'http://consumer-service:5000' 
        # self.url='http://localhost:5000'  # when running from local terminals
        self.row_num = 0
    
    async def send_request(self):
        await asyncio.sleep(random.uniform(0, self.max_latency))
                    
        row = self.df.row(self.row_num, named=True)
        self.row_num += 1
        
        row_data = {
            "ip address": row['ip address'],
            "Latitude": float(row['Latitude']),
            "Longitude": float(row['Longitude']),
            "suspicious": float(row.get('suspicious', 0.0))
        }
        return row_data

async def main():
    producer = Producer()
    while True:
        row_data = await producer.send_request()
        response = requests.post(
            f"{producer.url}/api/data",
            json=row_data
        )
        print(response.text)

if __name__ == "__main__":
    asyncio.run(main())