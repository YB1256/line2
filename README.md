# GCP Serverless Event-Driven Document Processing Pipeline

This project implements an event-driven architecture on Google Cloud to process uploaded documents and extract metadata.

## Architecture

1. **Ingestion**: Users upload files to a Cloud Storage bucket.
2. **Trigger**: Cloud Storage triggers a Pub/Sub message on the `OBJECT_FINALIZE` event.
3. **Processor**: A Python-based Cloud Run service receives the message, simulates OCR processing, and extracts metadata.
4. **Storage**: The metadata is streamed into a BigQuery dataset.

## Prerequisites

- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed and authenticated.
- A GCP project with billing enabled.
- PowerShell (for the deployment script).

## Deployment

1. Open PowerShell and navigate to this directory.
2. Run the deployment script with your project ID and a **globally unique** bucket name:

```powershell
.\deploy.ps1 -ProjectID "your-gcp-project-id" -BucketName "your-unique-bucket-name-12345"
```

## How It Works

Once deployed, you can test the pipeline by uploading a file to your Cloud Storage bucket:

```bash
echo "This is a test document to process" > test.txt
gcloud storage cp test.txt gs://your-unique-bucket-name-12345/
```

After a few seconds, you can query your BigQuery table to see the extracted metadata:

```bash
bq query --use_legacy_sql=false 'SELECT * FROM `your-gcp-project-id.document_pipeline.metadata`'
```
