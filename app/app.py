from flask import Flask, jsonify
import os

app = Flask(__name__)
VERSION = os.getenv("APP_VERSION", "4.2.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PAYMENT_MODE = os.getenv("PAYMENT_MODE", "fixed")
PAYMENT_FIX = "Payment validation now rejects malformed payment references before processing."
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
    return jsonify({
        "payment": "success",
        "defect_fixed": PAYMENT_MODE == "fixed",
        "version": VERSION,
    })
@app.get("/products")
def products():
    search = os.getenv("PRODUCT_SEARCH", "").lower()

    product_list = [
        {"id": 1, "name": "Laptop", "price": 55000},
        {"id": 2, "name": "Smartphone", "price": 25000},
        {"id": 3, "name": "Headphones", "price": 3000}
    ]

    if search:
        product_list = [
            product for product in product_list
            if search in product["name"].lower()
        ]

    return jsonify({
        "products": product_list,
        "count": len(product_list),
        "version": VERSION
    })
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8081")))
