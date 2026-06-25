# MLflow Local Setup Guide

## Prerequisites

* Python 3.X+
* Linux VM or Local Machine
* Internet Access

---

## 1. Create a Virtual Environment

```bash
mkdir mlflow-setup && cd mlflow-setup

python3 -m venv .venv
source .venv/bin/activate
```

---

## 2. Install MLflow

```bash
pip install --upgrade pip
pip install mlflow
```

Verify installation:

```bash
mlflow --version
```

---

## 3. Initialize MLflow Database

```bash
mlflow db upgrade sqlite:///mlflow.db
```

---

## 4. Start MLflow Server

```bash
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --host 0.0.0.0 \
  --port 5000 \
  --workers 1 \
  --allowed-hosts '*'
```

Access MLflow UI:

```text
http://<VM-IP>:5000
```

---

## 5. Configure Tracking URI

```bash
export MLFLOW_TRACKING_URI=http://<VM-IP>:5000
```

Verify:

```bash
echo $MLFLOW_TRACKING_URI
```

---

## 6. Test MLflow Tracking

Create `sample_mlflow.py`

```python
import mlflow

mlflow.set_experiment("demo-experiment")

with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_metric("accuracy", 0.95)

print("Run completed successfully")
```

Run:

```bash
python sample_mlflow.py
```

Verify the experiment and run in the MLflow UI.

---

## Useful Commands

```bash
# Check MLflow version
mlflow --version

# Check if MLflow is listening on port 5000
sudo ss -tulpn | grep 5000

# Verify UI locally
curl http://localhost:5000
```

---

## Notes

* SQLite is suitable for local development and testing.
* Use a dedicated database (PostgreSQL/MySQL) for production deployments.
* Use shared artifact storage (S3, MinIO, etc.) when multiple users are logging models.
