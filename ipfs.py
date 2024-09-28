# ipfs.py
import requests
import io
import pandas as pd

# Function to add a DataFrame as CSV to IPFS
def add_csv_to_ipfs(df):
    # Convert DataFrame to CSV bytes
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    files = {'file': ('data.csv', csv_bytes)}
    response = requests.post('http://127.0.0.1:5001/api/v0/add', files=files)
    if response.status_code == 200:
        ipfs_hash = response.json()['Hash']
        return ipfs_hash
    else:
        raise Exception(f"IPFS add error: {response.text}")

# Function to get CSV from IPFS and return as DataFrame
def get_csv_from_ipfs(ipfs_hash):
    params = {'arg': ipfs_hash}
    response = requests.post('http://127.0.0.1:5001/api/v0/cat', params=params)
    if response.status_code == 200:
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))
        return df
    else:
        raise Exception(f"IPFS cat error: {response.text}")
