# MLflow Deployment on Kubernetes using Helm

## Overview

This document describes how to deploy MLflow on a Kubernetes cluster using Helm. The examples use a Kind cluster for demonstration purposes, but the same procedure can be followed on production-grade Kubernetes platforms such as Amazon EKS, Azure AKS, Google GKE, OpenShift, or on-premises Kubernetes clusters.

---

# Prerequisites

## Infrastructure

* Linux VM (Amazon Linux, RHEL, Ubuntu, etc.)
* Minimum:

  * 2 vCPU
  * 4 GB RAM
  * 20 GB Storage
* Internet access for downloading container images and Helm charts

---

# Install Docker

Amazon Linux 2023:

```bash
sudo dnf update -y
sudo dnf install docker -y

sudo systemctl enable docker
sudo systemctl start docker

docker --version
```

Add current user to Docker group:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker run hello-world
```

---

# Install kubectl

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s \
https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

chmod +x kubectl
sudo mv kubectl /usr/local/bin/

kubectl version --client
```

---

# Install Kind

```bash
curl -Lo ./kind \
https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64

chmod +x ./kind
sudo mv ./kind /usr/local/bin/
```

Verify:

```bash
kind version
```

---

# Create Kubernetes Cluster

Create cluster:

```bash
cat > kind_config.yaml <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

kind create cluster --config kind_config.yaml  --name mlflow
```

Verify:

```bash
kubectl cluster-info
kubectl get nodes
```

Expected:

```text
NAME                   STATUS   ROLES           AGE
mlflow-control-plane   Ready    control-plane   xxm
```

---

# Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

Verify:

```bash
helm version
```

---

# Add MLflow Helm Repository

Browse for official documentation `https://community-charts.github.io/docs/charts/mlflow/basic-installation` 

```bash
helm repo add community-charts \
https://community-charts.github.io/helm-charts

helm repo update
```

Verify:

```bash
helm search repo mlflow
```

---

# Create Namespace

```bash
kubectl create namespace mlflow
```

---

# Deploy MLflow

Install MLflow using SQLite backend:

```bash
helm install mlflow community-charts/mlflow \
  --namespace mlflow \
  --set backendStore.defaultSqlitePath=/tmp/mlflow.db
  --set extraArgs.allowed-hosts="*"
```

---

# Verify Deployment

Check deployment:

```bash
kubectl get pods -n mlflow
```

Expected:

```text
NAME                     READY   STATUS
mlflow-xxxxxxxxxx-xxxxx  1/1     Running
```

Monitor startup:

```bash
kubectl get pods -n mlflow -w
```

---

# Access MLflow UI

Get pod name:

```bash
export POD_NAME=$(kubectl get pods -n mlflow \
-o jsonpath="{.items[0].metadata.name}")
```

Port forward:

```bash
kubectl port-forward pod/$POD_NAME \
5000:5000 \
-n mlflow \
--address 0.0.0.0
```

Access:

```text
http://<SERVER-IP>:5001
```

---

# Troubleshooting

## Pod Not Starting

Check logs:

```bash
kubectl logs -n mlflow <pod-name>
```

Check pod events:

```bash
kubectl describe pod <pod-name> -n mlflow
```

---

## Read-only Filesystem Error

Error:

```text
OSError: [Errno 30] Read-only file system: '/mlflow/data'
```

Cause:

MLflow attempts to create the SQLite database in a read-only path.

Resolution:

Use:

```bash
--set backendStore.defaultSqlitePath=/tmp/mlflow.db
```

or configure a Persistent Volume.

---

## Invalid Host Header

Error:

```text
Invalid Host header - possible DNS rebinding attack detected
```

Cause:

MLflow security middleware rejects requests from unapproved hosts.

Resolution:

Configure allowed hosts or expose MLflow using a Kubernetes Service/Ingress.Replace `*` with host details.
```
 helm install mlflow community-charts/mlflow \
  --namespace mlflow \
  --create-namespace \
  --set backendStore.defaultSqlitePath=/tmp/mlflow.db \
  --set extraArgs.allowed-hosts="*"
```

---

# Production Recommendations

For production environments, avoid SQLite.

Recommended architecture:

* MLflow Server
* PostgreSQL Backend Store
* Amazon S3 / MinIO Artifact Store
* Persistent Volumes
* Ingress Controller
* TLS Certificates
* RBAC-enabled Kubernetes Cluster

Architecture:

```text
Users
  |
Ingress / Load Balancer
  |
MLflow Server
  |
+-------------------+
| PostgreSQL        |
| S3 / MinIO        |
+-------------------+
```

This architecture provides persistence, scalability, backup, and multi-user support.

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
