# Production Deployment Guide

## Overview

This guide covers deploying the AI Software Generator Platform to production environments using Docker, Kubernetes, and cloud platforms.

## Prerequisites

### Infrastructure Requirements
- **Kubernetes Cluster**: Version 1.24+ (EKS, GKE, AKS, or self-hosted)
- **PostgreSQL**: Version 14+ (managed or self-hosted)
- **MinIO**: S3-compatible object storage
- **Redis**: Version 7+ (optional, for caching)
- **Load Balancer**: Nginx Ingress Controller or cloud load balancer
- **SSL Certificate**: Valid certificate for HTTPS

### Resource Requirements
- **CPU**: 8+ cores minimum, 16+ recommended
- **RAM**: 32GB minimum, 64GB recommended
- **Storage**: 100GB+ for generated projects and logs
- **Network**: 1Gbps minimum bandwidth

## Quick Deployment

### Using Docker Compose (Single Server)

```bash
# Clone repository
git clone https://github.com/your-org/ai-software-generator.git
cd ai-software-generator

# Configure environment
cp .env.prod.example .env
nano .env  # Edit production values

# Deploy
make deploy-prod

# Verify deployment
curl https://your-domain.com/health
```

### Using Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n ai-devgen
kubectl get services -n ai-devgen

# Get service URL
kubectl get ingress -n ai-devgen
```

## Detailed Deployment

### 1. Infrastructure Setup

#### PostgreSQL Database

**AWS RDS:**
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier ai-devgen-prod \
  --db-instance-class db.t3.large \
  --engine postgres \
  --engine-version 14.7 \
  --master-username devgen \
  --master-user-password your-secure-password \
  --allocated-storage 100 \
  --vpc-security-group-ids sg-your-security-group \
  --db-subnet-group-name your-subnet-group
```

**Google Cloud SQL:**
```bash
# Create Cloud SQL instance
gcloud sql instances create ai-devgen-prod \
  --database-version POSTGRES_14 \
  --cpu 2 \
  --memory 8GB \
  --region us-central1 \
  --root-password your-secure-password
```

#### MinIO Object Storage

**AWS S3:**
```bash
# Create S3 bucket
aws s3 mb s3://ai-devgen-projects-prod \
  --region us-east-1

# Configure bucket policy for MinIO compatibility
aws s3api put-bucket-versioning \
  --bucket ai-devgen-projects-prod \
  --versioning-configuration Status=Enabled
```

**MinIO on Kubernetes:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: minio/minio:latest
        ports:
        - containerPort: 9000
        env:
        - name: MINIO_ROOT_USER
          value: "admin"
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: password
        command: ["minio", "server", "/data"]
        volumeMounts:
        - name: minio-storage
          mountPath: /data
      volumes:
      - name: minio-storage
        persistentVolumeClaim:
          claimName: minio-pvc
```

#### Redis (Optional)

**AWS ElastiCache:**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id ai-devgen-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1
```

### 2. Application Deployment

#### Environment Configuration

Create production environment file:

```bash
# .env.prod
APP_ENV=production
APP_NAME=AI Software Generator
APP_VERSION=1.0.0

# Database
POSTGRES_HOST=your-rds-endpoint.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_USER=devgen
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=devgen

# MinIO
MINIO_ENDPOINT=your-minio-endpoint.com
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_SECURE=true
MINIO_BUCKET=ai-devgen-projects

# Redis
REDIS_URL=redis://your-redis-endpoint:6379

# AI Providers
OPENAI_API_KEY=sk-your-production-key
ANTHROPIC_API_KEY=sk-ant-your-production-key

# Security
JWT_SECRET_KEY=your-256-bit-production-secret
KEYCLOAK_URL=https://auth.your-domain.com

# Monitoring
LOKI_URL=https://logs.your-domain.com
PROMETHEUS_URL=https://metrics.your-domain.com
```

#### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api-gateway:
    image: ai-devgen/api-gateway:latest
    environment:
      - APP_ENV=production
    ports:
      - "80:8000"
    depends_on:
      - orchestrator
      - codegen-service
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  orchestrator:
    image: ai-devgen/orchestrator:latest
    environment:
      - APP_ENV=production
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  # ... other services with similar configuration
```

#### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: ai-devgen
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: ai-devgen/api-gateway:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ai-devgen-config
        - secretRef:
            name: ai-devgen-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 3. Networking and Security

#### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-devgen-ingress
  namespace: ai-devgen
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.your-domain.com
    - app.your-domain.com
    secretName: ai-devgen-tls
  rules:
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
  - host: app.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

#### SSL/TLS Setup

**Using cert-manager:**
```yaml
# k8s/cert-issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@your-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

#### Network Policies

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-devgen-network-policy
  namespace: ai-devgen
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: minio
    ports:
    - protocol: TCP
      port: 9000
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

### 4. Monitoring and Logging

#### Prometheus Metrics

```yaml
# k8s/prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ai-devgen-monitor
  namespace: ai-devgen
spec:
  selector:
    matchLabels:
      app: ai-devgen
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

#### Loki Logging

```yaml
# k8s/loki.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: ai-devgen
data:
  loki.yaml: |
    auth_enabled: false
    server:
      http_listen_port: 3100
    ingester:
      lifecycler:
        address: 127.0.0.1
        ring:
          kvstore:
            store: inmemory
          replication_factor: 1
        final_sleep: 0s
      chunk_idle_period: 1h
      max_chunk_age: 1h
      chunk_target_size: 1048576
      chunk_retain_period: 30s
      max_transfer_retries: 0
    schema_config:
      configs:
        - from: 2020-10-24
          store: boltdb-shipper
          object_store: filesystem
          schema: v11
          index:
            prefix: index_
            period: 24h
    storage_config:
      boltdb_shipper:
        active_index_directory: /tmp/loki/boltdb-shipper-active
        cache_location: /tmp/loki/boltdb-shipper-cache
        cache_ttl: 24h
        shared_store: filesystem
      filesystem:
        directory: /tmp/loki/chunks
    chunk_store_config:
      max_look_back_period: 0s
    table_manager:
      retention_deletes_enabled: false
      retention_period: 0s
```

#### Grafana Dashboards

```yaml
# k8s/grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-devgen-dashboard
  namespace: ai-devgen
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "AI DevGen Platform",
        "tags": ["ai-devgen"],
        "timezone": "browser",
        "panels": [
          {
            "title": "API Requests",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total[5m])",
                "legendFormat": "{{method}} {{path}}"
              }
            ]
          }
        ]
      }
    }
```

### 5. Backup and Recovery

#### Database Backup

```bash
# PostgreSQL backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/devgen_$DATE.sql"

pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://ai-devgen-backups/

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "devgen_*.sql" -mtime +7 -delete
```

#### Automated Backups

```yaml
# k8s/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: ai-devgen
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:14
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB > /backup/backup.sql
              aws s3 cp /backup/backup.sql s3://ai-devgen-backups/
            envFrom:
            - secretRef:
                name: database-secret
            - secretRef:
                name: aws-secret
            volumeMounts:
            - name: backup-volume
              mountPath: /backup
          volumes:
          - name: backup-volume
            emptyDir: {}
          restartPolicy: OnFailure
```

### 6. Scaling and Performance

#### Horizontal Pod Autoscaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: ai-devgen
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Resource Optimization

```yaml
# k8s/resource-limits.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: ai-devgen-limits
  namespace: ai-devgen
spec:
  limits:
  - default:
      memory: 512Mi
      cpu: 500m
    defaultRequest:
      memory: 256Mi
      cpu: 250m
    type: Container
```

### 7. Security Hardening

#### Pod Security Standards

```yaml
# k8s/pod-security.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: ai-devgen-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'MustRunAs'
    ranges:
    - min: 1
      max: 65535
  fsGroup:
    rule: 'MustRunAs'
    ranges:
    - min: 1
      max: 65535
```

#### Secrets Management

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-devgen-secrets
  namespace: ai-devgen
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  anthropic-api-key: <base64-encoded-key>
  jwt-secret: <base64-encoded-secret>
  postgres-password: <base64-encoded-password>
```

### 8. CI/CD Pipeline

#### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Configure AWS
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Build and Push Docker Images
      run: |
        docker build -t ai-devgen/api-gateway ./saas-devgen/api-gateway
        docker tag ai-devgen/api-gateway:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/ai-devgen/api-gateway:latest
        docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/ai-devgen/api-gateway:latest

    - name: Deploy to Kubernetes
      run: |
        aws eks update-kubeconfig --region us-east-1 --name ai-devgen-prod
        kubectl apply -f k8s/
        kubectl rollout status deployment/api-gateway -n ai-devgen
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check all services
kubectl get pods -n ai-devgen

# Check service endpoints
curl https://api.your-domain.com/health

# Check database connectivity
kubectl exec -it deployment/postgres -- psql -U devgen -d devgen -c "SELECT 1"
```

### Log Analysis

```bash
# View application logs
kubectl logs -f deployment/api-gateway -n ai-devgen

# Search logs with Loki
logcli query '{namespace="ai-devgen"}' --addr=https://logs.your-domain.com
```

### Performance Monitoring

```bash
# Check resource usage
kubectl top pods -n ai-devgen

# Check HPA status
kubectl get hpa -n ai-devgen

# View metrics
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
```

## Troubleshooting

### Common Issues

#### Pod Crashes
```bash
# Check pod logs
kubectl logs <pod-name> -n ai-devgen

# Check pod events
kubectl describe pod <pod-name> -n ai-devgen

# Check resource limits
kubectl get pods -n ai-devgen --field-selector=status.phase=Failed
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it deployment/api-gateway -- nc -zv postgres 5432

# Check database logs
kubectl logs deployment/postgres -n ai-devgen
```

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n ai-devgen

# Adjust resource limits
kubectl edit deployment <deployment-name> -n ai-devgen
```

### Rollback Procedures

```bash
# Rollback deployment
kubectl rollout undo deployment/api-gateway -n ai-devgen

# Rollback to specific version
kubectl rollout undo deployment/api-gateway --to-revision=2 -n ai-devgen
```

## Cost Optimization

### Resource Optimization

- Use spot instances for non-critical workloads
- Implement auto-scaling based on actual usage
- Use managed services (RDS, ElastiCache) for databases
- Optimize container images for size

### Monitoring Costs

```bash
# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Review logs for errors
   - Check disk usage
   - Update dependencies

2. **Monthly:**
   - Security patches
   - Performance optimization
   - Backup verification

3. **Quarterly:**
   - Major version updates
   - Architecture review
   - Cost optimization

### Getting Help

- 📧 **Email**: support@ai-devgen.com
- 📚 **Documentation**: https://docs.ai-devgen.com
- 💬 **Community**: https://discord.gg/ai-devgen
- 🐛 **Issues**: https://github.com/ai-devgen/platform/issues
- 📞 **Enterprise Support**: Contact your account manager

## Next Steps

1. **Plan Deployment**: Choose your infrastructure provider
2. **Configure Environment**: Set up production environment variables
3. **Deploy Infrastructure**: Create databases, storage, and networking
4. **Deploy Application**: Use Docker Compose or Kubernetes manifests
5. **Configure Monitoring**: Set up logging, metrics, and alerting
6. **Test Deployment**: Verify all services are working
7. **Go Live**: Start accepting production traffic
8. **Monitor and Optimize**: Continuously improve performance and costs

For detailed configuration examples and cloud-specific guides, visit our [production deployment documentation](https://docs.ai-devgen.com/deployment).
