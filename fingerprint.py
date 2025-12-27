from pyfingerprint.pyfingerprint import PyFingerprint
import mysql.connector
from mysql.connector import Error
import time

DB_CONFIG = {
    "host": "kennardb-mysql-moonlitguardian23-9f54.e.aivencloud.com",
    "port": 12769,
    "user": "avnadmin",
    "password": "AVNS_Qyja81mEQ4otUCCMC1S",
    "database": "defaultdb",
    "ssl_ca": "ca.pem"
}

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
            return int(result[0])   
        return None
    except Error as e:
        print("Database error:", e)
        return None


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

    while f.readImage() == False:
        pass

    f.convertImage(0x01)

    result = f.searchTemplate()
    positionNumber = result[0]  
    accuracyScore = result[1]   

    if positionNumber == -1:
        print("No match found")
        return False

    print(f"Found template at position {positionNumber} (Score: {accuracyScore})")
    db_fingerprint_id = get_employee_fingerprint_id(employee_id)

    if db_fingerprint_id is None:
        print("No fingerprint_id found in database for employee", employee_id)
        return False

    if positionNumber == db_fingerprint_id:
        print("Fingerprint verified successfully for employee", employee_id)
        return True
    else:
        print("Fingerprint mismatch! Expected", db_fingerprint_id, "but scanned", positionNumber)
        return False
