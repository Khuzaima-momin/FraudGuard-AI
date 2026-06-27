import os
import joblib
import pandas as pd
import numpy as np

# =====================================================
# LOAD MODEL FILES
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

MODEL_PATH = os.path.join(MODEL_DIR, "fraud.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
THRESHOLD_PATH = os.path.join(MODEL_DIR, "threshold.pkl")
FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
threshold = float(joblib.load(THRESHOLD_PATH))
feature_columns = joblib.load(FEATURE_COLUMNS_PATH)

# =====================================================
# TRANSACTION TYPE MAPPING
# =====================================================

TYPE_MAPPING = {
    "CASH_IN": 0,
    "CASH_OUT": 1,
    "DEBIT": 2,
    "PAYMENT": 3,
    "TRANSFER": 4
}

# =====================================================
# FEATURE ENGINEERING
# =====================================================

def create_features(data):

    df = pd.DataFrame([data])

    # -------------------------------------------------
    # Encode transaction type
    # -------------------------------------------------

    df["type"] = (
        df["type"]
        .astype(str)
        .str.upper()
        .map(TYPE_MAPPING)
        .fillna(-1)
    )

    # -------------------------------------------------
    # Create hour feature
    # (your notebook used "hour")
    # -------------------------------------------------

    df["hour"] = df["step"] % 24

    # -------------------------------------------------
    # Amount per hour
    # EXACTLY SAME AS NOTEBOOK
    # -------------------------------------------------

    df["amount_per_hour"] = (
        df["amount"] / (df["hour"] + 1)
    )

    # -------------------------------------------------
    # Balance change ratio
    # EXACTLY SAME AS NOTEBOOK
    # -------------------------------------------------

    df["balance_change_ratio"] = (
        abs(
            df["oldbalanceOrg"]
            - df["newbalanceOrig"]
        )
        / (df["oldbalanceOrg"] + 1)
    )

    # -------------------------------------------------
    # Destination balance ratio
    # EXACTLY SAME AS NOTEBOOK
    # -------------------------------------------------

    df["dest_balance_ratio"] = (
        df["newbalanceDest"]
        / (df["oldbalanceDest"] + 1)
    )

    # -------------------------------------------------
    # Large transaction flag
    #
    # IMPORTANT:
    # During training you used:
    #
    # threshold_large = quantile(0.95)
    #
    # You should ideally save this value from
    # training and load it.
    #
    # For now use 200000 as approximation.
    # -------------------------------------------------

    LARGE_THRESHOLD = 200000

    df["is_large_transaction"] = (
        df["amount"] > LARGE_THRESHOLD
    ).astype(int)

    # -------------------------------------------------
    # Add missing columns
    # -------------------------------------------------

    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0

    # -------------------------------------------------
    # Ensure same order as training
    # -------------------------------------------------

    df = df[feature_columns]

    return df


# =====================================================
# PREDICTION FUNCTION
# =====================================================

def predict_fraud(data):

    try:

        features = create_features(data)

        print("\n========== FEATURES ==========")
        print(features)

        scaled = scaler.transform(features)

        probability = float(
            model.predict_proba(scaled)[0][1]
        )

        is_fraud = probability >= threshold

        fraud_probability = round(
            probability * 100, 2
        )

        confidence = round(
            max(probability, 1 - probability) * 100,
            2
        )

        if fraud_probability < 30:
            risk = "LOW"

        elif fraud_probability < 60:
            risk = "MEDIUM"

        elif fraud_probability < 90:
            risk = "HIGH"

        else:
            risk = "CRITICAL"

        return {
            "success": True,
            "is_fraud": bool(is_fraud),
            "fraud_probability": fraud_probability,
            "risk_level": risk,
            "confidence": f"{confidence}%",
            "threshold_used": round(threshold * 100, 2)
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }