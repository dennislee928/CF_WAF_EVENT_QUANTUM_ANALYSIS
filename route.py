from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/fetch-waf-data', methods=['GET'])
def fetch_waf_data_endpoint():
    data = fetch_waf_data()
    if data:
        # Log or process the data locally
        print(f"Fetched WAF Data at {datetime.now()}: {len(data.get('result', []))} events")
        return jsonify(data)
    else:
        return jsonify({"error": "Failed to fetch WAF data"}), 500

if __name__ == '__main__':
    app.run(debug=True)
