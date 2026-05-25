<#
.SYNOPSIS
Deploys the GCP Serverless Document Processing Pipeline

.DESCRIPTION
This script creates the necessary infrastructure in Google Cloud:
1. BigQuery Dataset & Table
2. Cloud Storage Bucket
3. Pub/Sub Topic & Service Account Permissions
4. Cloud Run Service Deployment
5. Pub/Sub Push Subscription

.EXAMPLE
.\deploy.ps1 -ProjectID "my-gcp-project" -BucketName "my-unique-bucket-name"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectID,
    
    [Parameter(Mandatory=$true)]
    [string]$BucketName,
    
    [string]$Region = "us-central1",
    [string]$DatasetID = "document_pipeline",
    [string]$TableID = "metadata",
    [string]$TopicName = "document-upload-topic",
    [string]$ServiceName = "document-processor",
    [string]$InvokerSA = "pubsub-invoker-sa"
)

Write-Host "Setting project to $ProjectID..."
gcloud config set project $ProjectID

Write-Host "Enabling necessary GCP APIs..."
gcloud services enable run.googleapis.com pubsub.googleapis.com storage.googleapis.com bigquery.googleapis.com cloudbuild.googleapis.com

Write-Host "Creating BigQuery Dataset and Table..."
bq mk -d --location=US $DatasetID
bq mk -t --schema filename:STRING,date:TIMESTAMP,tags:STRING,word_count:INTEGER $DatasetID.$TableID

Write-Host "Creating Cloud Storage Bucket..."
gcloud storage buckets create gs://$BucketName --location=$Region

Write-Host "Creating Pub/Sub Topic..."
gcloud pubsub topics create $TopicName

Write-Host "Configuring GCS Notification to Pub/Sub..."
$StorageSA = gcloud storage service-agent --project=$ProjectID --format="value(email)"
gcloud pubsub topics add-iam-policy-binding $TopicName --member="serviceAccount:$StorageSA" --role="roles/pubsub.publisher"
gcloud storage buckets notifications create gs://$BucketName --topic=$TopicName --event-types=OBJECT_FINALIZE

Write-Host "Deploying Cloud Run Service..."
gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --set-env-vars="DATASET_ID=$DatasetID,TABLE_ID=$TableID" `
    --no-allow-unauthenticated

Write-Host "Setting up Pub/Sub Push Subscription..."
gcloud iam service-accounts create $InvokerSA --display-name "Pub/Sub Invoker SA"

gcloud run services add-iam-policy-binding $ServiceName `
    --member="serviceAccount:$InvokerSA@$ProjectID.iam.gserviceaccount.com" `
    --role="roles/run.invoker" `
    --region=$Region

$ServiceUrl = gcloud run services describe $ServiceName --platform managed --region $Region --format="value(status.url)"

gcloud pubsub subscriptions create document-upload-sub `
    --topic $TopicName `
    --push-endpoint="$ServiceUrl/" `
    --push-auth-service-account="$InvokerSA@$ProjectID.iam.gserviceaccount.com"

Write-Host "Deployment Complete! Upload files to gs://$BucketName to trigger the pipeline."
