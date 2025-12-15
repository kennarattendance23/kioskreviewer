from pyfingerprint.pyfingerprint import PyFingerprint

try:
    fp = PyFingerprint('/dev/serial0', 57600, 0xFFFFFFFF, 0x00000000)

    if not fp.verifyPassword():
        raise ValueError("Fingerprint sensor password incorrect")

    print("Deleting ALL fingerprint templates...")
    fp.clearDatabase()
    print("✅ All fingerprint templates deleted successfully!")

except Exception as e:
    print("❌ Error:", str(e))
