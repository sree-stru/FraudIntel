#!/bin/bash
set -e
echo ""
echo "🛡️  FraudIntel — Google Cloud Run Deployment"
echo "============================================="
echo ""

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
SERVICE_NAME="fraudintel"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "📋 Configuration:"
echo "   Project:  ${PROJECT_ID}"
echo "   Region:   ${REGION}"
echo "   Service:  ${SERVICE_NAME}"
echo ""

echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo "⬆️  Pushing to Container Registry..."
docker push ${IMAGE_NAME}:latest

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars "APP_ENV=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}"

URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Application URL: ${URL}"
echo ""
echo "🧪 Test endpoints:"
echo "   Health:    ${URL}/api/health"
echo "   Stats:     ${URL}/api/dashboard/stats"
echo "   Dashboard: ${URL}/"
echo ""
