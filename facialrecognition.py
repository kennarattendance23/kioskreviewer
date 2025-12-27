import cv2  
import tkinter as tk
import time
import numpy as np
import mysql.connector
import face_recognition
import json
import os
from picamera2 import Picamera2
from libcamera import Transform
from attendance_db import has_time_in_today, has_time_out_today  


DB_CONFIG = {
    "host": "kennardb-mysql-moonlitguardian23-9f54.e.aivencloud.com",
    "port": 12769,
    "user": "avnadmin",
    "password": "AVNS_Qyja81mEQ4otUCCMC1S",
    "database": "defaultdb",
    "ssl_ca": "ca.pem"
}

def load_employees():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT employee_id, name, face_embedding, image FROM employees WHERE status='Active'")
    employees = cursor.fetchall()
    conn.close()

    photos_dir = "/home/kennarautoshop/Desktop/admin_dashboard/backend/uploads/"
    fallback_img = os.path.join(photos_dir, "no-photo.png")

    if not os.path.exists(photos_dir):
        os.makedirs(photos_dir)

    for emp in employees:
        try:
            emp["embedding"] = np.array(json.loads(emp["face_embedding"]), dtype=np.float32)
        except Exception:
            emp["embedding"] = None

        photo_data = emp.get("image")

        if isinstance(photo_data, bytes):
            img_filename = f"{emp['employee_id']}.jpg"
            img_path = os.path.join(photos_dir, img_filename)
            with open(img_path, "wb") as f:
                f.write(photo_data)
            emp["image"] = img_path

        elif isinstance(photo_data, str):
            if not os.path.isabs(photo_data):
                photo_data = os.path.join(photos_dir, photo_data)
            if not os.path.exists(photo_data):
                photo_data = fallback_img
            emp["image"] = photo_data

        else:
            emp["image"] = fallback_img

    return employees


def get_face_embedding(face_img):
    rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    embeddings = face_recognition.face_encodings(rgb_face)
    if len(embeddings) > 0:
        return embeddings[0]
    return None


def recognize_face(face_img, employees, tolerance=0.6):
    live_embedding = get_face_embedding(face_img)
    if live_embedding is None:
        return None

    best_match, best_score = None, 1.0
    for emp in employees:
        if emp["embedding"] is not None:
            distance = face_recognition.face_distance([emp["embedding"]], live_embedding)[0]
            if distance < best_score:
                best_score = distance
                best_match = emp

    if best_match and best_score <= tolerance:
        return best_match
    return None


def is_blurry(image, threshold=100.0):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    fm = cv2.Laplacian(gray, cv2.CV_64F).var()
    return fm < threshold


def get_background(path="Time-In.png", screen_w=1024, screen_h=600):
    bg = cv2.imread(path)
    if bg is None:
        bg = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
        bg[:] = (0, 0, 0)
    else:
        bg = cv2.resize(bg, (screen_w, screen_h))
    return bg


def filled_rounded_rectangle(img, pt1, pt2, color, radius=20):
    x1, y1 = pt1
    x2, y2 = pt2
    cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
    cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
    cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1)
    cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1)
    cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1)
    cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1)


def draw_notification(frame, message, color=(0, 0, 255),
                      text_color=(255, 255, 255), font_scale=0.9,
                      center=False, box_y=None):
    h, w, _ = frame.shape
    overlay = frame.copy()
    (tw, th), _ = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)

    padding_x, padding_y = 30, 20

    if center:
        x1 = (w - tw) // 2 - padding_x
        y1 = (h - th) // 2 - padding_y
    elif box_y is not None:
        x1 = (w - tw) // 2 - padding_x
        y1 = box_y
    else:
        x1 = (w - tw) // 2 - padding_x
        y1 = int(h * 0.85 - (th + 2 * padding_y) // 2)

    x2 = x1 + tw + 2 * padding_x
    y2 = y1 + th + 2 * padding_y

    filled_rounded_rectangle(overlay, (x1, y1), (x2, y2), color, 20)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    text_x = (w - tw) // 2
    text_y = (y1 + y2 + th) // 2 - 5
    cv2.putText(frame, message, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 2, cv2.LINE_AA)
    return frame


def draw_fancy_box(img, x, y, w, h, color=(255, 255, 255), thickness=2, length=40):
    cv2.line(img, (x, y), (x + length, y), color, thickness)
    cv2.line(img, (x, y), (x, y + length), color, thickness)
    cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
    cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)
    cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
    cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)
    cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)


def start_facial_recognition(mode="Time-In"):
    from main import EmployeeInfoScreen  

    root_tmp = tk.Tk()
    screen_w = root_tmp.winfo_screenwidth()
    screen_h = root_tmp.winfo_screenheight()
    root_tmp.destroy()

    employees = load_employees()

    global picam2
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (640, 480)})
    config["transform"] = Transform(hflip=False, vflip=False)
    picam2.configure(config)
    picam2.start()

    cv2.namedWindow("Facial Recognition", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Facial Recognition", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    frame_interval = 0.2
    attempts, success = 0, False
    recognized_emp = None
    fail_attempts = 0
    timeout_seconds = 10

    box_w, box_h = 320, 320
    x1, y1 = (screen_w - box_w) // 2, (screen_h - box_h) // 2
    x2, y2 = x1 + box_w, y1 + box_h

    while attempts < 3 and not success:
        start_time = time.time()
        no_face_start = None
        last_capture_time = 0

        while time.time() - start_time < 30:
            current_time = time.time()
            if current_time - last_capture_time < frame_interval:
                if cv2.waitKey(1) & 0xFF == 27:
                    release_camera()
                    cv2.destroyAllWindows()
                    return "ESC"
                continue
            last_capture_time = current_time

            frame_orig = picam2.capture_array()
            gray = cv2.cvtColor(frame_orig, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80, 80))

            display_frame = cv2.resize(frame_orig, (screen_w, screen_h))
            valid_face, roi = False, None
            feedback = "Position your face"
            feedback_color = (255, 255, 255)
            margin = 10

            if len(faces) > 0:
                feedback = "Align your face"
                feedback_color = (255, 0, 0)
                for (fx, fy, fw, fh) in faces:
                    scale_x = screen_w / frame_orig.shape[1]
                    scale_y = screen_h / frame_orig.shape[0]
                    fx_disp, fy_disp = int(fx * scale_x), int(fy * scale_y)
                    fw_disp, fh_disp = int(fw * scale_x), int(fh * scale_y)
                    if fx_disp >= x1 - margin and fy_disp >= y1 - margin and fx_disp + fw_disp <= x2 + margin and fy_disp + fh_disp <= y2 + margin:
                        if fh < 100:
                            feedback = "Move closer"
                            feedback_color = (255, 0, 0)
                        elif fh > 350:
                            feedback = "Move farther"
                            feedback_color = (255, 0, 0)
                        else:
                            roi = frame_orig[fy:fy+fh, fx:fx+fw]
                            if is_blurry(roi):
                                feedback = "Hold still, image is blurry"
                                feedback_color = (0, 165, 255)
                                roi = None
                            else:
                                feedback = "Scanning..."
                                feedback_color = (0, 200, 0)
                                valid_face = True
                        break

            draw_fancy_box(display_frame, x1, y1, box_w, box_h,
                           color=(0, 255, 0) if valid_face else (0, 0, 255),
                           thickness=3, length=50)

            display_frame = draw_notification(display_frame, feedback,
                                              color=feedback_color,
                                              box_y=y2 + 20)
            cv2.imshow("Facial Recognition", display_frame)

            if valid_face and roi is not None:
                cv2.waitKey(2000)
                match = recognize_face(roi, employees)
                if match:
                    recognized_emp = match

                    if mode == "Time-In" and has_time_in_today(recognized_emp["employee_id"]):
                        already_frame = get_background("Time-In.png", screen_w, screen_h)
                        already_frame = draw_notification(
                            already_frame,
                            f"{recognized_emp['name']}, You already Time-In today!",
                            color=(0, 200, 0),
                            font_scale=1.0,
                            center=True
                        )
                        cv2.imshow("Facial Recognition", already_frame)
                        cv2.waitKey(2500)
                        release_camera()
                        cv2.destroyAllWindows()
                        return "ALREADY_TIMEIN"

                    if mode == "Time-Out" and not has_time_in_today(recognized_emp["employee_id"]):
                        no_in_frame = get_background("Time-In.png", screen_w, screen_h)
                        no_in_frame = draw_notification(
                            no_in_frame,
                            f"{recognized_emp['name']}, You cannot Time-Out without Time-In!",
                            color=(0, 0, 255),
                            font_scale=1.0,
                            center=True
                        )
                        cv2.imshow("Facial Recognition", no_in_frame)
                        cv2.waitKey(2500)
                        release_camera()
                        cv2.destroyAllWindows()
                        return "NO_TIMEIN"

                    if mode == "Time-Out" and has_time_out_today(recognized_emp["employee_id"]):
                        already_out_frame = get_background("Time-In.png", screen_w, screen_h)
                        already_out_frame = draw_notification(
                            already_out_frame,
                            f"{recognized_emp['name']}, You already logged Time-Out today!",
                            color=(0, 200, 0),
                            font_scale=1.0,
                            center=True
                        )
                        cv2.imshow("Facial Recognition", already_out_frame)
                        cv2.waitKey(2500)
                        release_camera()
                        cv2.destroyAllWindows()
                        return "ALREADY_TIMEOUT"

                    success = True
                    release_camera()
                    cv2.destroyAllWindows()
                    EmployeeInfoScreen(
                        None,
                        emp_id=recognized_emp["employee_id"],
                        full_name=recognized_emp["name"],
                        image_path=recognized_emp.get("image"),
                        mode=mode
                    )
                    return "SUCCESS"

                else:
                    fail_attempts += 1
                    if fail_attempts >= 3:
                        warning_frame = get_background("Time-In.png", screen_w, screen_h)
                        warning_frame = draw_notification(
                            warning_frame,
                            "Warning! Please ask assistance to the admin's office.",
                            color=(26, 178, 254),
                            font_scale=1.0,
                            center=True
                        )
                        cv2.imshow("Facial Recognition", warning_frame)
                        cv2.waitKey(2500)
                        release_camera()
                        cv2.destroyAllWindows()
                        return "MAX_ATTEMPTS_REACHED"
                    else:
                        fail_frame = get_background("Time-In.png", screen_w, screen_h)
                        fail_frame = draw_notification(
                            fail_frame,
                            "Sorry! We didn't recognize you. Please try again!",
                            color=(0, 0, 255),
                            font_scale=1.0,
                            center=True
                        )
                        cv2.imshow("Facial Recognition", fail_frame)
                        cv2.waitKey(1000)
                        break

            if not valid_face:
                if no_face_start is None:
                    no_face_start = time.time()
                elif time.time() - no_face_start >= timeout_seconds:
                    release_camera()
                    cv2.destroyAllWindows()
                    return "NO_FACE_TIMEOUT"

            if cv2.waitKey(1) & 0xFF == 27:
                release_camera()
                cv2.destroyAllWindows()
                return "ESC"

        attempts += 1

    release_camera()
    cv2.destroyAllWindows()
    return "FAIL"


def release_camera():
    global picam2
    if picam2:
        picam2.stop()
        picam2.close()
        picam2 = None
