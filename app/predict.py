import os
import joblib
import pandas as pd
import numpy as np

# =====================================================
# LOAD MODEL ARTIFACTS
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

MODEL_PATH = os.path.join(MODEL_DIR, "fraud.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
THRESHOLD_PATH = os.path.join(MODEL_DIR, "threshold.pkl")
FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    loaded_threshold = joblib.load(THRESHOLD_PATH)
    # Ensure threshold is cast safely as a plain float regardless of structure format
    threshold = float(loaded_threshold) if not isinstance(loaded_threshold, (list, np.ndarray)) else float(loaded_threshold[0])
    feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
except FileNotFoundError as e:
    raise FileNotFoundError(
        f"Critical model files are missing from directory: {MODEL_DIR}. Error detailed: {e}"
    )

# =====================================================
# CORRECT COLAB ENCODING MAPPING
# =====================================================
TYPE_MAPPING = {
    "CASH_IN": 0,
    "CASH_OUT": 1,
    "DEBIT": 2,
    "PAYMENT": 3,
    "TRANSFER": 4
}

# =====================================================
# FEATURE PREPROCESSING
# =====================================================

def create_features(data):
    """
    Transforms raw dictionary input data into a DataFrame format matching
    the precise feature transformations performed during Colab training.
    """
    # Create copy of incoming data dictionary to prevent side-effects on original tracking data
    input_dict = dict(data)
    
    # Safely drop identifier tracking metrics if accidentally passed down by APIs
    for unwanted_col in ["isFraud", "isFlaggedFraud", "nameOrig", "nameDest"]:
        input_dict.pop(unwanted_col, None)

    df = pd.DataFrame([input_dict])

    epsilon = 1e-6

    # 1. Encode transaction type mapping
    if "type" in df.columns:
        df["type"] = df["type"].map(TYPE_MAPPING).fillna(-1)

    # 2. Time Features Alignment
    if "step" in df.columns:
        df["hours"] = df["step"] % 24
        df["day"] = df["step"] // 24
    else:
        df["hours"] = 0
        df["day"] = 0

    # 3. Size Features Alignment
    df["is_large_transaction"] = (df["amount"] > 200000).astype(int) if "amount" in df.columns else 0
    df["amount_per_hour"] = df["amount"] / (df["hours"] + epsilon) if "amount" in df.columns else 0

    # 4. Balance Delta Math Error Correction (Exactly matching the notebook)
    if "oldbalanceOrg" in df.columns and "amount" in df.columns and "newbalanceOrig" in df.columns:
        df["orig_balance_error"] = df["oldbalanceOrg"] - df["amount"] - df["newbalanceOrig"]
    else:
        df["orig_balance_error"] = 0.0

    if "oldbalanceDest" in df.columns and "amount" in df.columns and "newbalanceDest" in df.columns:
        df["dest_balance_error"] = df["oldbalanceDest"] + df["amount"] - df["newbalanceDest"]
    else:
        df["dest_balance_error"] = 0.0

    # 5. Keep only features expected by the training matrix setup
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0.0

    # Force identical positioning order matching X_train array template
    df = df[feature_columns]

    return df

# =====================================================
# MAIN SOFTWARE PREDICTION ROUTINE
# =====================================================

def predict_fraud(data):
    """
    Main entry point for software backend validation. Processes data dictionary 
    objects and applies optimal inference weights.
    """
    try:
        # Preprocess features matching exactly how the notebook sets columns up
        df_features = create_features(data)

        # Scale data parameters utilizing loaded configuration maps
        scaled_data = scaler.transform(df_features)

        # Predict real probabilities directly from class index 1 (Fraud Class)
        prob_array = model.predict_proba(scaled_data)
        probability = float(prob_array[0][1])

        # Evaluate logic against optimal decision boundary threshold saved from the notebook
        is_fraud = bool(probability >= threshold)
        fraud_probability_pct = float(round(probability * 100, 2))

        # Categorize threat status zones
        if fraud_probability_pct < 30.0:
            risk_level = "LOW"
        elif fraud_probability_pct < 60.0:
            risk_level = "MEDIUM"
        elif fraud_probability_pct < 90.0:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Calculate logical model output split certainty bounds 
        confidence_pct = float(round(max(probability, 1.0 - probability) * 100, 2))

        return {
            "success": True,
            "is_fraud": is_fraud,
            "fraud_probability": fraud_probability_pct,
            "risk_level": risk_level,
            "confidence": f"{confidence_pct}%",
            "threshold_used": float(round(threshold * 100, 2))
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Live processing execution failure: {str(e)}"
        }