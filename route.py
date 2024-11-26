from qiskit import QuantumCircuit, Aer, execute
##
import numpy as np
from collections import Counter
##
from qiskit import QuantumCircuit, Aer, execute
from qiskit.visualization import plot_histogram
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

##
def preprocess_data(data):
    issues = data.get("result", {}).get("issues", [])
    if not issues:
        return [], []

    # Extract issue classes and severities
    issue_classes = [issue["issue_class"] for issue in issues]
    severities = [issue["severity"] for issue in issues]

    # Count occurrences of each issue class
    class_counts = Counter(issue_classes)
    severity_mapping = {"Low": 1, "Moderate": 2, "Critical": 3}

    # Map severities to numerical values
    severities_encoded = [severity_mapping[severity] for severity in severities]

    return list(class_counts.values()), severities_encoded
##
def create_circuit(class_counts, severities):
    # Determine the number of qubits required
    n_qubits = max(len(class_counts), len(severities))

    # Initialize quantum circuit
    qc = QuantumCircuit(n_qubits)

    # Encode class counts into quantum states
    for i, count in enumerate(class_counts):
        angle = 2 * np.pi * (count / max(class_counts))  # Normalize and convert to rotation angle
        qc.ry(angle, i)

    # Encode severities as weighted rotations
    for i, severity in enumerate(severities):
        angle = np.pi * (severity / max(severities))  # Normalize and convert to rotation angle
        qc.rx(angle, i)

    # Add entanglement to correlate features
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)

    return qc

##
def simulate_circuit(qc):
    backend = Aer.get_backend('statevector_simulator')
    result = execute(qc, backend).result()
    statevector = result.get_statevector()
    return statevector