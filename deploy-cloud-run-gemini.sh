#!/bin/bash
# Deploy RAG API with Gemini to Google Cloud Run

set -e

echo "🚀 Deploying RAG API with Gemini to Cloud Run..."

# Configuration
PROJECT_ID="${1:-YOUR_PROJECT_ID}"
REGION="${2:-us-central1}"
SERVICE_NAME="rag-api-gemini"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi

# Set project
echo "📋 Setting project to: ${PROJECT_ID}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com

# Build container
echo "🏗️  Building container image..."
gcloud builds submit \
    --tag ${IMAGE_NAME} \
    --file Dockerfile.gemini \
    .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "PINECONE_INDEX=sheldonbrain-rag"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Service URL: ${SERVICE_URL}"
echo ""
echo "🔑 Next steps:"
echo "1. Set environment variables:"
echo "   gcloud run services update ${SERVICE_NAME} \\"
echo "     --region ${REGION} \\"
echo "     --update-env-vars GOOGLE_API_KEY=your_gemini_key,PINECONE_API_KEY=your_pinecone_key"
echo ""
echo "2. Test the API:"
echo "   curl ${SERVICE_URL}/health"
echo ""
echo "3. Query the memory:"
echo "   curl -X POST ${SERVICE_URL}/query \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"query\": \"What is GUT?\", \"top_k\": 3}'"
echo ""
