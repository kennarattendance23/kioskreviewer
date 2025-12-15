# database.py
import cv2
import os

# Configure these if you want DB saving. If left None, saving is disabled.
DB_ENABLED = False
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "KennarDB"
}

def save_face_image(employee_id, image_rgb, folder="faces"):
    """
    Save face image locally (and optionally to DB).
    image_rgb: numpy array (RGB)
    """
    os.makedirs(folder, exist_ok=True)
    fname = os.path.join(folder, f"{employee_id}_{int(__import__('time').time())}.jpg")
    # Convert RGB to BGR for OpenCV
    bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(fname, bgr)
    print(f"[database] saved face image to {fname}")
    # DB saving omitted in this minimal version. Re-enable DB_ENABLED and add mysql code if needed.
