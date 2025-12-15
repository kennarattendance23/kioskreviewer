from flask import Flask, request, jsonify

app = Flask(__name__)

# store fingerprint status in memory
fingerprint_status = {"status": "pending"}

@app.route("/verify", methods=["POST"])
def verify():
    """
    Endpoint to be called by phone app/browser when fingerprint succeeds.
    Example: POST http://192.168.1.24:5000/verify  { "status": "success" }
    """
    data = request.json
    if data and data.get("status") == "success":
        fingerprint_status["status"] = "success"
        return jsonify({"message": "Fingerprint verified"}), 200
    else:
        fingerprint_status["status"] = "failed"
        return jsonify({"message": "Fingerprint failed"}), 400

@app.route("/status", methods=["GET"])
def status():
    """Laptop polls this to check if fingerprint was done on phone."""
    return jsonify(fingerprint_status)

@app.route("/reset", methods=["POST"])
def reset():
    """Reset fingerprint status before new scan."""
    fingerprint_status["status"] = "pending"
    return jsonify({"message": "Status reset"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # accessible on LAN
