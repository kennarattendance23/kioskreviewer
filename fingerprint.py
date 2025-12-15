from pyfingerprint.pyfingerprint import PyFingerprint
import mysql.connector
from mysql.connector import Error
import time

# ==============================
# DATABASE CONFIG
# ==============================
DB_CONFIG = {
    "host": "kennardb-mysql-moonlitguardian23-9f54.e.aivencloud.com",
    "port": 12769,
    "user": "avnadmin",
    "password": "AVNS_Qyja81mEQ4otUCCMC1S",
    "database": "defaultdb",
    "ssl_ca": "ca.pem"
}

# ==============================
# DB HELPER
# ==============================
def get_employee_fingerprint_id(employee_id):
    """Fetch fingerprint_id from database for a given employee_id"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT fingerprint_id FROM employees WHERE employee_id = %s", (employee_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return int(result[0])   # fingerprint_id stored as string in DB → cast to int
        return None
    except Error as e:
        print("Database error:", e)
        return None


# ==============================
# FINGERPRINT VERIFICATION
# ==============================
def wait_for_fingerprint(employee_id):
    """
    Waits for a fingerprint scan and verifies if it matches the stored fingerprint_id
    of the given employee.
    """
    try:
        f = PyFingerprint('/dev/ttyS0', 57600, 0xFFFFFFFF, 0x00000000)

        if not f.verifyPassword():
            raise ValueError("The given fingerprint sensor password is wrong!")

    except Exception as e:
        print("Fingerprint sensor init failed:", e)
        return False

    print("Waiting for finger...")

    # Loop until a finger is read
    while f.readImage() == False:
        pass

    # Convert image to characteristics and store in charbuffer 1
    f.convertImage(0x01)

    # Search for fingerprint in library
    result = f.searchTemplate()
    positionNumber = result[0]  # template index
    accuracyScore = result[1]   # match accuracy

    if positionNumber == -1:
        print("No match found")
        return False

    print(f"Found template at position {positionNumber} (Score: {accuracyScore})")
    # Get expected fingerprint_id from DB
    db_fingerprint_id = get_employee_fingerprint_id(employee_id)

    if db_fingerprint_id is None:
        print("No fingerprint_id found in database for employee", employee_id)
        return False

    # Compare AS608 matched position with DB fingerprint_id
    if positionNumber == db_fingerprint_id:
        print("Fingerprint verified successfully for employee", employee_id)
        return True
    else:
        print("Fingerprint mismatch! Expected", db_fingerprint_id, "but scanned", positionNumber)
        return False
