# Production Deployment Guide

## Prerequisites

- AWS CLI configured with appropriate IAM permissions
- kubectl configured for target cluster
- Helm 3.x installed
- Terraform 1.8+ installed

## Step 1: Infrastructure (Terraform)

```bash
cd infrastructure/terraform/environments/prod

# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply (creates VPC, EKS, RDS, S3, MSK)
terraform apply tfplan

# Get kubeconfig
aws eks update-kubeconfig --name ai-cost-platform-prod --region us-east-1
```

## Step 2: Kubernetes Namespace & Secrets

```bash
cd infrastructure/kubernetes

# Create namespace
kubectl apply -f base/configmaps/namespace.yaml

# Create secrets (use your actual values)
kubectl create secret generic backend-secrets \
  --from-literal=DATABASE_URL="postgresql+asyncpg://..." \
  --from-literal=REDIS_URL="redis://..." \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -base64 32)" \
  -n ai-cost-platform
```

## Step 3: Deploy with Helm

```bash
cd infrastructure/helm

# Add dependencies
helm dependency update ai-cost-platform/

# Deploy
helm upgrade --install ai-cost-platform ./ai-cost-platform \
  --namespace ai-cost-platform \
  --values ai-cost-platform/values.yaml \
  --set backend.image.tag=1.0.0 \
  --set frontend.image.tag=1.0.0 \
  --wait --timeout 10m

# Verify
kubectl get pods -n ai-cost-platform
kubectl get ingress -n ai-cost-platform
```

## Step 4: Database Migration

```bash
# Run Alembic migrations
kubectl exec -it deploy/ai-cost-backend -n ai-cost-platform -- \
  alembic upgrade head
```

## Step 5: Verify Deployment

```bash
# Check pod health
kubectl get pods -n ai-cost-platform

# Check API health
curl https://api.aicostplatform.com/health

# Check metrics
kubectl port-forward svc/prometheus 9090:9090 -n monitoring &
# Visit http://localhost:9090
```

## Rollback

```bash
# Helm rollback
helm rollback ai-cost-platform 0 -n ai-cost-platform

# Or deploy specific version
helm upgrade ai-cost-platform ./ai-cost-platform \
  --set backend.image.tag=0.9.0 \
  --namespace ai-cost-platform
```
