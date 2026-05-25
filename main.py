import base64
import json
import os
import datetime
from flask import Flask, request
from google.cloud import bigquery
from google.cloud import storage

app = Flask(__name__)

# Initialize clients
bq_client = bigquery.Client()
storage_client = storage.Client()

# Environment variables
DATASET_ID = os.environ.get('DATASET_ID', 'document_pipeline')
TABLE_ID = os.environ.get('TABLE_ID', 'metadata')

@app.route('/', methods=['POST'])
def index():
    envelope = request.get_json()
    if not envelope:
        msg = 'no Pub/Sub message received'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    pubsub_message = envelope['message']
    
    bucket_name = None
    file_name = None

    if 'attributes' in pubsub_message:
        attributes = pubsub_message['attributes']
        bucket_name = attributes.get('bucketId')
        file_name = attributes.get('objectId')
        event_type = attributes.get('eventType')
        
        # Only process on finalize
        if event_type and event_type != 'OBJECT_FINALIZE':
            print(f'Ignoring event type: {event_type}')
            return ('', 204)
            
    if not bucket_name or not file_name:
        print(f'Could not find bucket or filename in message')
        return ('', 204)
        
    print(f'Processing file: {file_name} from bucket: {bucket_name}')

    try:
        # Simulate processing / OCR
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        # Read the file content
        content = blob.download_as_text()
        
        # Extracted metadata
        word_count = len(content.split())
        
        # Create some dummy tags based on word count
        tags = ["document"]
        if word_count > 500:
            tags.append("long")
        else:
            tags.append("short")
            
        metadata = {
            "filename": file_name,
            "date": datetime.datetime.utcnow().isoformat(),
            "tags": json.dumps(tags),
            "word_count": word_count
        }
        
        # Insert into BigQuery
        table_ref = f"{bq_client.project}.{DATASET_ID}.{TABLE_ID}"
        errors = bq_client.insert_rows_json(table_ref, [metadata])
        
        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
            return f"Error inserting into BigQuery", 500
        else:
            print(f"Successfully processed and inserted metadata for {file_name}")
            return ('', 204)
            
    except Exception as e:
        print(f"Error processing document: {e}")
        return f"Internal Server Error", 500

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=PORT, debug=True)
