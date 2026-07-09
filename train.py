"""Train churn prediction model using Logistic Regression and register with MLflow"""

import os
import pickle
import pandas as pd
import mlflow
import mlflow.sklearn

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
)

# ----------------------------------------------------
# MLflow Configuration
# ----------------------------------------------------

try:
    MLFLOW_TRACKING_URI = os.environ["MLFLOW_TRACKING_URI"]
except KeyError:
    raise Exception("MLFLOW_TRACKING_URI environment variable is not set")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("churn-prediction")

print(f"Using MLflow Tracking URI: {MLFLOW_TRACKING_URI}")

# ----------------------------------------------------
# Load Dataset
# ----------------------------------------------------

df = pd.read_csv("data/churn_data.csv")

features = [
    "age",
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "num_support_calls",
]

X = df[features]
y = df["churn"]

# ----------------------------------------------------
# Split Dataset
# ----------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
)

# ----------------------------------------------------
# Start MLflow Run
# ----------------------------------------------------

with mlflow.start_run():

    # Model Parameters
    max_iter = 1000
    random_state = 42

    # Create Model
    model = LogisticRegression(
        max_iter=max_iter,
        random_state=random_state,
    )

    # ------------------------------------------------
    # Train Model
    # ------------------------------------------------

    model.fit(X_train, y_train)

    # ------------------------------------------------
    # Predictions
    # ------------------------------------------------

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # ------------------------------------------------
    # Metrics
    # ------------------------------------------------

    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    # ------------------------------------------------
    # Log Parameters
    # ------------------------------------------------

    mlflow.log_param("algorithm", "LogisticRegression")
    mlflow.log_param("max_iter", max_iter)
    mlflow.log_param("random_state", random_state)
    mlflow.log_param("test_size", 0.2)

    # ------------------------------------------------
    # Log Metrics
    # ------------------------------------------------

    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("auc_roc", auc)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    mlflow.log_metric("f1_score", f1)

    # ------------------------------------------------
    # Save Local Model
    # ------------------------------------------------

    os.makedirs("models", exist_ok=True)

    with open("models/churn_model.pkl", "wb") as f:
        pickle.dump(model, f)

    print("Model saved to models/churn_model.pkl")

    # ------------------------------------------------
    # Register Model in MLflow
    # ------------------------------------------------

    try:

        model_info = mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name="churn-model",
        )

        print("Model registered successfully.")
        print(f"Model URI: {model_info.model_uri}")

    except Exception as e:

        print("MLflow model registration failed.")
        print(str(e))

# ----------------------------------------------------
# Results
# ----------------------------------------------------

print("\n========== TRAINING RESULTS ==========")
print(f"Algorithm : Logistic Regression")
print(f"Accuracy  : {accuracy:.4f}")
print(f"AUC-ROC   : {auc:.4f}")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1 Score  : {f1:.4f}")

print("\nTraining completed successfully.")



# """Train churn prediction model and register with MLflow"""

# import os
# import pickle
# import pandas as pd
# import mlflow
# import mlflow.sklearn

# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import accuracy_score, roc_auc_score

# # ----------------------------------------------------

# # MLflow Configuration

# # ----------------------------------------------------

# try:
#     MLFLOW_TRACKING_URI = os.environ["MLFLOW_TRACKING_URI"]
# except KeyError:
#     raise Exception(
#         "MLFLOW_TRACKING_URI environment variable is not set"
#     )

# mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
# mlflow.set_experiment("churn-prediction")

# print(f"Using MLflow Tracking URI: {MLFLOW_TRACKING_URI}")

# # ----------------------------------------------------

# # Load Dataset

# # ----------------------------------------------------

# df = pd.read_csv("data/churn_data.csv")

# features = [
# "age",
# "tenure_months",
# "monthly_charges",
# "total_charges",
# "num_support_calls"
# ]

# X = df[features]
# y = df["churn"]

# # ----------------------------------------------------

# # Split Dataset

# # ----------------------------------------------------

# X_train, X_test, y_train, y_test = train_test_split(
# X,
# y,
# test_size=0.2,
# random_state=42
# )

# # ----------------------------------------------------

# # Start MLflow Run

# # ----------------------------------------------------

# with mlflow.start_run():

#     n_estimators = 100
#     random_state = 42

#     model = RandomForestClassifier(
#         n_estimators=n_estimators,
#         random_state=random_state
#     )

#     # Train Model
#     model.fit(X_train, y_train)

#     # Predictions
#     y_pred = model.predict(X_test)
#     y_proba = model.predict_proba(X_test)[:, 1]

#     # Metrics
#     accuracy = accuracy_score(y_test, y_pred)
#     auc = roc_auc_score(y_test, y_proba)

#     # ------------------------------------------------
#     # Log Parameters
#     # ------------------------------------------------

#     mlflow.log_param("n_estimators", n_estimators)
#     mlflow.log_param("random_state", random_state)
#     mlflow.log_param("test_size", 0.2)

#     # ------------------------------------------------
#     # Log Metrics
#     # ------------------------------------------------

#     mlflow.log_metric("accuracy", accuracy)
#     mlflow.log_metric("auc_roc", auc)

#     # ------------------------------------------------
#     # Log Dataset Artifact
#     # ------------------------------------------------

#     # mlflow.log_artifact("data/churn_data.csv")

#     # ------------------------------------------------
#     # Save Local PKL File
#     # ------------------------------------------------

#     os.makedirs("models", exist_ok=True)

#     with open("models/churn_model.pkl", "wb") as f:
#         pickle.dump(model, f)

#     print("Model saved to models/churn_model.pkl")

#     # ------------------------------------------------
#     # Register Model in MLflow
#     # ------------------------------------------------

#     try:

#         model_info = mlflow.sklearn.log_model(
#             sk_model=model,
#             artifact_path="model",
#             registered_model_name="churn-model"
#         )

#         print("Model registered successfully.")
#         print(f"Model URI: {model_info.model_uri}")

#     except Exception as e:

#         print("MLflow model registration failed.")
#         print(str(e))

# # ------------------------------------------------
# # Results
# # ------------------------------------------------

# print("\n========== TRAINING RESULTS ==========")
# print(f"Accuracy : {accuracy:.4f}")
# print(f"AUC-ROC  : {auc:.4f}")

# print("\nTraining completed successfully.")











# """Train churn prediction model"""
# import pandas as pd
# import pickle
# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import accuracy_score, roc_auc_score

# # Load data
# df = pd.read_csv('data/churn_data.csv')

# # Features and target
# features = ['age', 'tenure_months', 'monthly_charges', 'total_charges', 'num_support_calls']
# X = df[features]
# y = df['churn']

# # Split
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # Train
# model = RandomForestClassifier(n_estimators=100, random_state=42)
# model.fit(X_train, y_train)

# # Evaluate
# y_pred = model.predict(X_test)
# y_proba = model.predict_proba(X_test)[:, 1]

# accuracy = accuracy_score(y_test, y_pred)
# auc = roc_auc_score(y_test, y_proba)

# print(f"Accuracy: {accuracy:.4f}")
# print(f"AUC-ROC: {auc:.4f}")

# # Save model
# with open('models/churn_model.pkl', 'wb') as f:
#     pickle.dump(model, f)

# print("Model saved to models/churn_model.pkl")