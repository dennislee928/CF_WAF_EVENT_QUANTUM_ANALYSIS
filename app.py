import logging
from flask import Flask, jsonify
from datetime import datetime
import requests
import os
from collections import Counter
import numpy as np
from qiskit import QuantumCircuit, execute
from qiskit_aer import Aer
from qiskit_machine_learning.neural_networks import OpflowQNN
from qiskit_machine_learning.algorithms import NeuralNetworkClassifier
from qiskit.opflow import Z, I, PauliSumOp
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from qiskit_ibm_runtime import QiskitRuntimeService
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Setup logging
debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
log_level = logging.DEBUG if debug else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Retrieve the token from the environment
token = os.getenv('IBM_QUANTUM_API_TOKEN')
if not token:
    logger.error("IBM_QUANTUM_API_TOKEN is not set in environment variables.")
    raise EnvironmentError("IBM_QUANTUM_API_TOKEN is required but not set in the environment variables.")

# Initialize the Qiskit Runtime Service
try:
    service = QiskitRuntimeService(
        channel='ibm_quantum',
        instance='ibm-q/open/main',
        token=token
    )
except Exception as e:
    logger.critical(f"Failed to initialize Qiskit Runtime Service: {e}")
    raise SystemExit("Critical Error: Qiskit Runtime Service Initialization Failed")

# Fetch Security Center Data
def fetch_security_center_data():
    url = f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID')}/intel/attack-surface-report/issues"
    headers = {
       "X-Auth-Email": os.getenv("CLOUDFLARE_EMAIL"),
    "X-Auth-Key": os.getenv("CLOUDFLARE_API_KEY"),
    "Content-Type": "application/json"
    }
    params = {
        "per_page": 100,
    }
    ##See response
    response = requests.get(url, headers=headers, params=params)
    print("Response Status Code:", response.status_code)
    print("Response Body:", response.text)
   
   
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch security center data: {response.status_code} {response.text}:CF_ACCOUNT = {os.getenv('CLOUDFLARE_ACCOUNT_ID')}:CF_API_KEY = {os.getenv('CLOUDFLARE_API_KEY')}:CF_AUTH_EMAIL = {os.getenv('CLOUDFLARE_AUTH_EMAIL')}")
        return None

# Preprocess Data
def preprocess_data(data):
    issues = data.get("result", {}).get("issues", [])
    if not issues:
        return [], []

    issue_classes = [issue["issue_class"] for issue in issues]
    severities = [issue["severity"] for issue in issues]

    class_counts = Counter(issue_classes)
    severity_mapping = {"Low": 1, "Moderate": 2, "Critical": 3}

    severities_encoded = [severity_mapping[severity] for severity in severities]

    return list(class_counts.values()), severities_encoded

# Create Quantum Circuit
def create_circuit(class_counts, severities):
    n_qubits = max(len(class_counts), len(severities))
    qc = QuantumCircuit(n_qubits)

    for i, count in enumerate(class_counts):
        angle = 2 * np.pi * (count / max(class_counts))  # Normalize
        qc.ry(angle, i)

    for i, severity in enumerate(severities):
        angle = np.pi * (severity / max(severities))  # Normalize
        qc.rx(angle, i)

    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)

    return qc

# Simulate Quantum Circuit
def simulate_circuit(qc):
    backend = Aer.get_backend('statevector_simulator')
    result = execute(qc, backend).result()
    statevector = result.get_statevector()
    return statevector

# Create QASM File
def create_qasm_file(class_counts, severities, filename="cybersecurity.qasm"):
    qc = create_circuit(class_counts, severities)
    qasm_data = qc.qasm()

    with open(filename, "w") as f:
        f.write(qasm_data)

    print(f"QASM file created: {filename}")
    return filename

# Post QASM to IBM Quantum Lab
def post_to_ibm_quantum_lab(qasm_file):
    api_token = os.getenv("IBM_QUANTUM_API_TOKEN")
    url = "https://quantum-computing.ibm.com/api/v2.0/jobs"

    with open(qasm_file, "r") as f:
        qasm_code = f.read()

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "qasm": qasm_code,
        "backend": "ibm_brisbane ",
        "shots": 1024,
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("Job submitted successfully:", response.json())
    else:
        print("Failed to submit job:", response.text)

# Flask Routes
@app.route('/fetch_waf_data_endpoint', methods=['GET'])
def fetch_waf_data_endpoint():
    try:
        data = fetch_security_center_data()
        if data:
            logger.info(f"Fetched Security Center Data at {datetime.now()}: {len(data.get('result', {}).get('issues', []))} issues")
            return jsonify(data), 200
        else:
            logger.error("No data returned from the Security Center API.")
            return jsonify({"error": "Failed to fetch security center data"}), 500
    except Exception as e:
        logger.exception("An error occurred while fetching WAF data.")
        return jsonify({"error": str(e)}), 500

@app.route('/process-security-center-data', methods=['POST'])
def process_security_center_data():
    data = fetch_security_center_data()
    if not data:
        return jsonify({"error": "No security center data to process"}), 400

    # Preprocess Data
    class_counts, severities = preprocess_data(data)

    # Create and Simulate Quantum Circuit
    qc = create_circuit(class_counts, severities)
    statevector = simulate_circuit(qc)

    # Optional: Save QASM File and Post to IBM Quantum Lab
    qasm_file = create_qasm_file(class_counts, severities)
    post_to_ibm_quantum_lab(qasm_file)

    return jsonify({
        'processed_data': statevector.tolist(),
        'class_counts': class_counts,
        'severities': severities
    })
##For confirming homepage
@app.route("/", methods=["GET"])
def home():
    if request.headers.get("Accept") == "application/json":
        # Return a JSON response if the client accepts JSON
        return jsonify({"message": "Welcome to the Security Center Data Machine API"}), 200
    else:
        # Return a plain text response otherwise
        return "Welcome to the app!"


@app.route("/favicon.ico")
def favicon():
    return "", 204




# Main Entry
if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=True) 