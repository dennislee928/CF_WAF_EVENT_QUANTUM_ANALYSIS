from qiskit import QuantumCircuit, Aer, execute
##
import numpy as np
from collections import Counter
##
from qiskit import QuantumCircuit, Aer, execute
from qiskit.visualization import plot_histogram
##
from qiskit_machine_learning.neural_networks import OpflowQNN
from qiskit_machine_learning.algorithms import NeuralNetworkClassifier
from qiskit.opflow import Z, I, StateFn, PauliSumOp
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

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

##
def create_qasm_file(class_counts, severities, filename="cybersecurity.qasm"):
    qc = create_circuit(class_counts, severities)  # Reuse your quantum circuit creation function
    qasm_data = qc.qasm()

    # Save the QASM data to a file
    with open(filename, "w") as f:
        f.write(qasm_data)

    print(f"QASM file created: {filename}")
    return filename

##
def post_to_ibm_quantum_lab(qasm_file):
    # Replace with your IBM Quantum API token
    api_token = os.getenv("IBM_QUANTUM_API_TOKEN")
    url = "https://quantum-computing.ibm.com/api/v2.0/jobs"

    # Read the QASM file
    with open(qasm_file, "r") as f:
        qasm_code = f.read()

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    # Prepare payload
    payload = {
        "qasm": qasm_code,
        "backend": "ibmq_qasm_simulator",  # Specify the IBM backend
        "shots": 1024,  # Number of shots for the job
    }

    # Submit job
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("Job submitted successfully:", response.json())
    else:
        print("Failed to submit job:", response.text)
##
def post_processed_data(data):
    url = "https://quantum-computing.ibm.com/api/v2.0/jobs"
    api_token = os.getenv("IBM_QUANTUM_API_TOKEN")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "data": data,
        "backend": "ibmq_qasm_simulator",  # Specify backend
        "shots": 1024,
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("Data submitted successfully:", response.json())
    else:
        print("Failed to submit data:", response.text)

