from flask import Flask, jsonify
import os

app = Flask(__name__)
VERSION = os.getenv("APP_VERSION", "4.2.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PAYMENT_MODE = os.getenv("PAYMENT_MODE", "fixed")
PAYMENT_FIX = "Payment validation rejects malformed payment references before processing."
FAIL_HEALTH = os.getenv("FAIL_HEALTH", "false").lower() == "true"

@app.get("/")
def home():
    return jsonify({
        "application": "retail-platform",
        "version": VERSION,
        "environment": ENVIRONMENT,
        "payment_status": "fixed" if PAYMENT_MODE == "fixed" else "legacy",
        "payment_fix": PAYMENT_FIX,
    })

@app.get("/health")
def health():
    if FAIL_HEALTH:
        return jsonify({"status": "unhealthy", "version": VERSION}), 500
    return jsonify({"status": "healthy", "version": VERSION}), 200

@app.get("/payment")
def payment():
    payment_reference = os.getenv("PAYMENT_REFERENCE", "").strip()

    if not payment_reference or len(payment_reference) < 6:
        return jsonify({
            "payment": "rejected",
            "defect_fixed": True,
            "reason": "Invalid payment reference",
            "version": VERSION,
        }), 400

    return jsonify({
        "payment": "success",
        "defect_fixed": True,
        "payment_reference": payment_reference,
        "version": VERSION,
    }), 200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8081")))
