from flask import Blueprint, render_template, request, jsonify
from app.predict import predict_fraud

main = Blueprint("main", __name__)


# =====================================================
# HOME PAGE
# =====================================================

@main.route("/")
def home():

    transaction_types = [
        "CASH_IN",
        "CASH_OUT",
        "DEBIT",
        "PAYMENT",
        "TRANSFER"
    ]

    return render_template(
        "index.html",
        transaction_types=transaction_types
    )


# =====================================================
# SINGLE PREDICTION
# =====================================================
@main.route("/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        result = predict_fraud(data)

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =====================================================
# BATCH PREDICTION
# =====================================================

@main.route("/batch", methods=["POST"])
def batch_predict():

    try:

        transactions = request.get_json()

        results = []

        for index, transaction in enumerate(transactions):

            try:

                prediction = predict_fraud(transaction)

                prediction["index"] = index

                results.append(prediction)

            except Exception as e:

                results.append({
                    "index": index,
                    "error": str(e)
                })

        return jsonify(results)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500