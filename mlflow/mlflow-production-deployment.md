# MLflow Production Deployment on Kubernetes

## Overview

This guide describes how to deploy MLflow on Kubernetes using Helm with a production-grade backend.

### Architecture

| Component | Service |
|-----------|---------|
| MLflow Server | Kubernetes |
| Backend Store | Amazon RDS PostgreSQL |
| Artifact Store | Amazon S3 |
| Package Manager | Helm |

---

## Prerequisites

- Kubernetes Cluster
- Helm 3.x
- Amazon RDS PostgreSQL
- Amazon S3 Bucket
- AWS CLI
- kubectl

---

# Step 1 - Create Namespace

```bash
kubectl create namespace mlflow
```

---

# Step 2 - Create Amazon RDS PostgreSQL

Recommended Configuration

- Engine : PostgreSQL
- Version : Latest Stable
- Template : Free Tier / Dev (Practice)
- Storage : gp3
- Enable Automated Backups
- Public Access : No (Recommended)
- Security Group : Allow TCP 5432 from Kubernetes Worker Nodes only

> Do **not** select **Connect to EC2 compute resource**. Configure networking manually using Security Groups.

---

# Step 3 - Configure PostgreSQL

Login as the master user.

```sql
CREATE DATABASE mlflow;

CREATE USER mlflowuser WITH PASSWORD 'StrongPassword';

GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflowuser;

\c mlflow

GRANT USAGE, CREATE ON SCHEMA public TO mlflowuser;

ALTER SCHEMA public OWNER TO mlflowuser;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO mlflowuser;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO mlflowuser;
```

---

# Step 4 - Create Amazon S3 Bucket

Create a bucket for MLflow artifacts.

Example

```
mlflow-artifacts-prod
```

Artifacts stored in S3 include:

- Models
- Datasets
- Plots
- Metrics
- Images
- Any logged files

---

# Step 5 - Deploy MLflow

```bash
helm install mlflow community-charts/mlflow \
  --namespace mlflow \
  --set backendStore.databaseMigration=true \
  --set backendStore.postgres.enabled=true \
  --set backendStore.postgres.host=<RDS-ENDPOINT> \
  --set backendStore.postgres.port=5432 \
  --set backendStore.postgres.database=mlflow \
  --set backendStore.postgres.user=mlflowuser \
  --set-string backendStore.postgres.password='<PASSWORD>'
  --set extraArgs.allowed-hosts="*" 
```

> Always use **--set-string** when the password contains special characters such as `$`.

---

# Step 6 - Configure Artifact Store

# Configure S3 Artifact Storage

MLflow stores:

* Metrics
* Parameters
* Experiments
* Models
* Datasets
* Artifacts

By default, artifacts are stored locally inside the MLflow container.

For production environments, configure Amazon S3 as the artifact store.

---

## Create AWS Credentials Secret

Create a Kubernetes Secret containing AWS credentials.

```bash
kubectl create secret generic mlflow-s3-secret \
  -n mlflow \
  --from-literal=AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID> \
  --from-literal=AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY>
```

Verify:

```bash
kubectl get secret mlflow-s3-secret -n mlflow
```

Expected:

```text
NAME               TYPE     DATA
mlflow-s3-secret   Opaque   2
```

---

## Configure MLflow for S3

Download chart values:

```bash
helm show values community-charts/mlflow > values.yaml
```

Locate the `artifactRoot.s3` section and update:

```yaml
artifactRoot:
  s3:
    enabled: true

    bucket: tad-churn-datasets

    existingSecret:
      name: mlflow-s3-secret
      keyOfAccessKeyId: AWS_ACCESS_KEY_ID
      keyOfSecretAccessKey: AWS_SECRET_ACCESS_KEY
```

---

## Upgrade MLflow Deployment

```bash
helm upgrade mlflow community-charts/mlflow \
  -n mlflow \
  -f values.yaml
```

---

## Verify Environment Variables

Check whether AWS credentials are injected into the pod.

```bash
kubectl exec -it deploy/mlflow -n mlflow -- env | grep AWS
```

Expected:

```text
AWS_ACCESS_KEY_ID=xxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxx
```
---

# Verify Artifact Storage

Create a test experiment from a client machine.

Example:

```python
import mlflow

mlflow.set_tracking_uri("http://<SERVER-IP>:5001")

with mlflow.start_run():
    mlflow.log_param("test", "value")
```

Verify in MLflow UI:

```text
Experiments -> Runs -> Artifacts
```

Artifacts should appear successfully.

---

# Step 7 - Verify Deployment

```bash
kubectl get pods -n mlflow

kubectl logs deployment/mlflow -n mlflow

kubectl port-forward svc/mlflow 5000:5000 -n mlflow
```

Access

```
http://localhost:5000
```

---

# Common Issues

### Password Authentication Failed

Cause

- Password not quoted.
- Shell removes `$`.

Correct

```bash
--set-string backendStore.postgres.password='Password$123'
```

---

### no pg_hba.conf entry ... no encryption

Cause

- SSL not enabled while connecting to Amazon RDS.

Solution

- Use SSL (`sslmode=require`) if required by your RDS configuration.

---

### permission denied for schema public

Grant permissions.

```sql
GRANT USAGE, CREATE ON SCHEMA public TO mlflowuser;

ALTER SCHEMA public OWNER TO mlflowuser;
```

---

### Database Migration Fails

Check

```bash
kubectl logs deployment/mlflow -n mlflow -c mlflow-db-migration
```

---

# Production Recommendations

- Use Amazon RDS PostgreSQL instead of SQLite.
- Use Amazon S3 for artifact storage.
- Store passwords in Kubernetes Secrets.
- Restrict Security Groups to Kubernetes nodes only.
- Enable automated RDS backups.
- Use IAM Roles instead of long-lived AWS keys when possible.
- Configure Ingress with TLS for external access.
- Monitor MLflow using Kubernetes health checks.

---

# Useful Commands

```bash
kubectl get pods -n mlflow

kubectl describe pod <pod-name> -n mlflow

kubectl logs deployment/mlflow -n mlflow

kubectl rollout restart deployment mlflow -n mlflow

helm upgrade mlflow community-charts/mlflow ...

helm uninstall mlflow -n mlflow
```