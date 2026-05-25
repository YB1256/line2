import base64
import json
import os
import random
from datetime import datetime, timezone
from flask import Flask, request
from google.cloud import bigquery

app = Flask(__name__)

# Initialize BigQuery client
# We expect the environment variables PROJECT_ID, BQ_DATASET, and BQ_TABLE to be set.
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
BQ_DATASET = os.environ.get('BQ_DATASET', 'document_pipeline')
BQ_TABLE = os.environ.get('BQ_TABLE', 'metadata')

bq_client = None

def get_bq_client():
    global bq_client
    if bq_client is None:
        bq_client = bigquery.Client(project=PROJECT_ID)
    return bq_client

def simulate_ocr(filename):
    """Simulate OCR processing of a document to extract tags and word count."""
    print(f"Simulating OCR for {filename}...")
    possible_tags = ["invoice", "receipt", "contract", "report", "memo", "confidential", "draft"]
    
    # Generate mock data
    word_count = random.randint(100, 5000)
    tags = ",".join(random.sample(possible_tags, k=random.randint(1, 3)))
    
    return {
        "word_count": word_count,
        "tags": tags
    }

@app.route("/", methods=["GET"])
def health_check():
    return "Service is healthy and ready to process documents.", 200

@app.route("/", methods=["POST"])
def process_document():
    """Receive and parse Pub/Sub messages."""
    envelope = request.get_json()
    if not envelope:
        msg = "no Pub/Sub message received"
        print(f"error: {msg}")
        return f"Bad Request: {msg}", 400

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "invalid Pub/Sub message format"
        print(f"error: {msg}")
        return f"Bad Request: {msg}", 400

    pubsub_message = envelope["message"]

    if "data" in pubsub_message:
        try:
            data = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
            data_json = json.loads(data)
        except Exception as e:
            msg = f"Invalid Pub/Sub message data: {e}"
            print(f"error: {msg}")
            return f"Bad Request: {msg}", 400
    else:
        msg = "Pub/Sub message missing data"
        print(f"error: {msg}")
        return f"Bad Request: {msg}", 400

    # Extract filename from the GCS event payload
    filename = data_json.get("name")
    bucket = data_json.get("bucket")
    
    if not filename:
        msg = "No filename found in event"
        print(f"error: {msg}")
        # Return 204 to acknowledge so Pub/Sub doesn't retry invalid messages
        return f"No Content: {msg}", 204
    
    print(f"Received event for file: gs://{bucket}/{filename}")

    # Process the document
    ocr_results = simulate_ocr(filename)
    
    # Prepare BigQuery record
    record = {
        "filename": filename,
        "date": datetime.now(timezone.utc).isoformat(),
        "tags": ocr_results["tags"],
        "word_count": ocr_results["word_count"]
    }
    
    print(f"Extracted metadata: {record}")
    
    # Insert into BigQuery
    try:
        client = get_bq_client()
        table_id = f"{client.project}.{BQ_DATASET}.{BQ_TABLE}"
        
        errors = client.insert_rows_json(table_id, [record])
        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
            return "Internal Server Error", 500
        else:
            print(f"Successfully inserted record into {table_id}")
            
    except Exception as e:
        print(f"Failed to insert into BigQuery: {e}")
        return "Internal Server Error", 500

    return "Success", 204

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
