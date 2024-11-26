from qiskit import QuantumCircuit, Aer, execute
##
import numpy as np
from collections import Counter
##
from flask import Flask, jsonify
from datetime import datetime
import requests
import os

app = Flask(__name__)

@app.route('/fetch-waf-data', methods=['GET'])
def fetch_waf_data_endpoint():
    data = fetch_security_center_data()
    if data:
        # Log or process the data locally
        print(f"Fetched WAF Data at {datetime.now()}: {len(data.get('result', []))} events")
        return jsonify(data)
    else:
        return jsonify({"error": "Failed to fetch WAF data"}), 500

if __name__ == '__main__':
    app.run(debug=True)
##

def fetch_security_center_data():
    url = f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID')}/intel/attack-surface-report/issues"
    headers = {
        "X-Auth-Email": "cloudflare.admin@twister5.com.tw",  # Replace with your actual email
        "X-Auth-Key": "daf08ebac1a4805ecb820fa699ca0d8b0b9e2",  # Replace with your actual key
       
        "Content-Type": "application/json",
    }
    params = {
        "per_page": 100,  # Adjust the number of records per request
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch WAF data:", response.text)
        return None
    
##

@app.route('/process_security_center_data', methods=['POST'])
def process_security_center_data():
    data = fetch_security_center_data()
    if not data:
        return jsonify({"error": "No WAF data to process"}), 400

    # Example Qiskit processing
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    backend = Aer.get_backend('statevector_simulator')
    result = execute(qc, backend).result()
    statevector = result.get_statevector()

    return jsonify({'processed_data': statevector.tolist()})