from flask import Flask, request, jsonify
import subprocess
import threading
import os

app = Flask(__name__)

# Path to your registration.py
REGISTRATION_SCRIPT = "/home/kennarautoshop/Desktop/kennarautoshop_attendancesystem/attendance/facial_fingerprint_registration.py"  # Update to your actual path

def run_registration(employee_id):
    """
    Runs the registration.py script in a separate thread.
    Pass the employee_id as an environment variable.
    """
    env = os.environ.copy()
    env["EMPLOYEE_ID"] = str(employee_id)
    try:
        subprocess.run(["python3", REGISTRATION_SCRIPT], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running registration.py: {e}")

@app.route("/api/register", methods=["POST"])
def trigger_registration():
    data = request.json
    employee_id = data.get("employee_id")
    if not employee_id:
        return jsonify({"message": "Employee ID is required"}), 400

    # Run registration in background so Flask doesn't block
    thread = threading.Thread(target=run_registration, args=(employee_id,))
    thread.start()

    return jsonify({"message": f"Registration started for Employee ID {employee_id}"}), 200

if __name__ == "__main__":
    # Run on all interfaces so frontend can access from another device
    app.run(host="0.0.0.0", port=5001)
