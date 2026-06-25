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
5001:5000 \
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
