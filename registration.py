import os
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import numpy as np
import mysql.connector
import json
from picamera2 import Picamera2
from pyfingerprint.pyfingerprint import PyFingerprint
import face_recognition
import customtkinter as ctk

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
# FACE REGISTRATION
# ==============================
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

SAVE_DIR = "registered_faces"
os.makedirs(SAVE_DIR, exist_ok=True)

EMPLOYEE_ID = os.environ.get("EMPLOYEE_ID")  # <-- get employee ID from Flask

def get_face_embedding(face_img):
    rgb_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_img)
    if len(encodings) > 0:
        return encodings[0].tolist()
    else:
        return None

class FaceRegistrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Facial Registration System")
        self.root.attributes("-fullscreen", True)

        # Background Image
        bg_image_path = "Time-In.png"
        bg_image = Image.open(bg_image_path)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        bg_image = bg_image.resize((screen_w, screen_h), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(bg_image)

        self.canvas = tk.Canvas(root, width=screen_w, height=screen_h)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)

        self.instruction_text_id = self.canvas.create_text(
            screen_w // 2, 50,
            text=f"Employee ID: {EMPLOYEE_ID} | Align your face for registration",
            fill="black", font=("Arial", 18)
        )

        self.video_label = tk.Label(root)
        self.video_window = self.canvas.create_window(screen_w // 2, screen_h // 2, window=self.video_label)

        self.face_registered = False
        self.countdown_started = False
        self.start_time = None
        self.box_width = 250
        self.box_height = 250

        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "XRGB8888", "size": (620, 460)}
        )
        self.picam2.configure(config)
        self.picam2.start()

        self.update_video()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_video(self):
        frame = self.picam2.capture_array()
        if frame is not None:
            h, w, _ = frame.shape
            x1 = w // 2 - self.box_width // 2
            y1 = h // 2 - self.box_height // 2
            x2 = x1 + self.box_width
            y2 = y1 + self.box_height

            display_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
            face_in_box = False
            if len(faces) > 0:
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                fx, fy, fw, fh = faces[0]
                if (x1 < fx and x2 > fx + fw and y1 < fy and y2 > fy + fh):
                    face_in_box = True

            status_text = ""
            if face_in_box and not self.face_registered:
                if not self.countdown_started:
                    box_color = (0, 0, 255)
                    self.start_time = time.time()
                    self.countdown_started = True
                    status_text = "Face aligned! Capturing in 3s..."
                else:
                    elapsed = int(time.time() - self.start_time)
                    if elapsed < 3:
                        box_color = (0, 255, 0)
                        status_text = f"Capturing in {3 - elapsed}..."
                    else:
                        box_color = (0, 255, 0)
                        self.countdown_started = False
                        status_text = "Processing..."
                        self.root.after(500, lambda: self.register_face(frame, x1, y1, self.box_width, self.box_height))
            else:
                box_color = (0, 0, 255)
                self.countdown_started = False
                status_text = "Align your face inside the box"

            cv2.rectangle(display_frame, (x1, y1), (x2, y2), box_color, 2)
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.root.after(20, self.update_video)

    def register_face(self, frame, x, y, w, h):
        self.face_registered = True
        face_img = frame[y:y + h, x:x + w]
        face_img = cv2.resize(face_img, (250, 250))
        self.embedding = get_face_embedding(face_img)
        if self.embedding is None:
            self.face_registered = False
            return
        self.face_img = face_img
        self.show_preview(face_img)

    def show_preview(self, face_img):
        preview_win = tk.Toplevel(self.root)
        preview_win.attributes("-fullscreen", True)
        canvas = tk.Canvas(preview_win, width=preview_win.winfo_screenwidth(),
                           height=preview_win.winfo_screenheight())
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)

        img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        lbl = tk.Label(preview_win, image=imgtk, bd=0)
        lbl.image = imgtk
        canvas.create_window(preview_win.winfo_screenwidth() // 2,
                             preview_win.winfo_screenheight() // 2, window=lbl)

        btn_frame = tk.Frame(preview_win, bg="#7FB3FF")
        canvas.create_window(preview_win.winfo_screenwidth() // 2,
                             preview_win.winfo_screenheight() - 100, window=btn_frame)

        def proceed_action():
            preview_win.destroy()
            self.picam2.stop()
            self.root.destroy()
            FingerprintRegistration(self.embedding, self.face_img, EMPLOYEE_ID).mainloop()

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        proceed_btn = ctk.CTkButton(master=btn_frame, text="Proceed", command=proceed_action)
        proceed_btn.pack(side="left", padx=20)
        retake_btn = ctk.CTkButton(master=btn_frame, text="Retake",
                                   command=lambda: self.retake(preview_win))
        retake_btn.pack(side="left", padx=20)

    def retake(self, win):
        win.destroy()
        self.face_registered = False
        self.countdown_started = False

    def on_close(self):
        self.picam2.stop()
        self.root.destroy()

# ==============================
# FINGERPRINT REGISTRATION
# ==============================
class FingerprintRegistration(tk.Tk):
    def __init__(self, embedding, face_img, employee_id):
        super().__init__()
        self.attributes("-fullscreen", True)
        self.embedding = embedding
        self.face_img = face_img
        self.employee_id = employee_id

        bg_image_path = "Time-In.png"
        bg_image = Image.open(bg_image_path)
        bg_image = bg_image.resize((self.winfo_screenwidth(), self.winfo_screenheight()), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(bg_image)
        self.canvas = tk.Canvas(self, width=self.winfo_screenwidth(), height=self.winfo_screenheight())
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)

        self.status_text_id = self.canvas.create_text(self.winfo_screenwidth() // 2, 100,
                                                      text="Place your finger on the sensor", fill="black",
                                                      font=("Arial", 18))

        self.after(500, self.wait_for_finger)

    def wait_for_finger(self):
        try:
            fp = PyFingerprint('/dev/serial0', 57600, 0xFFFFFFFF, 0x00000000)
            if not fp.verifyPassword():
                raise ValueError("Fingerprint sensor password incorrect")

            def poll_finger():
                if fp.readImage():
                    self.process_fingerprint(fp)
                else:
                    self.after(50, poll_finger)

            poll_finger()
        except Exception as e:
            self.canvas.itemconfig(self.status_text_id, text=f"Error: {str(e)}", fill="red")
            self.after(3000, self.destroy)

    def process_fingerprint(self, fp):
        try:
            fp.convertImage(0x01)
            fp.createTemplate()
            position = fp.storeTemplate()
            self.save_to_database(position)
            self.after(3000, self.destroy)
        except Exception as e:
            self.canvas.itemconfig(self.status_text_id, text=f"Error: {str(e)}", fill="red")
            self.after(3000, self.destroy)

    def save_to_database(self, fingerprint_id):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            embedding_str = json.dumps(self.embedding)
            sql = """UPDATE employees SET face_embedding=%s, fingerprint_id=%s WHERE employee_id=%s"""
            cursor.execute(sql, (embedding_str, str(fingerprint_id), self.employee_id))
            conn.commit()
            conn.close()
            self.canvas.itemconfig(self.status_text_id, text="✅ Registration completed!", fill="green")
        except Exception as e:
            self.canvas.itemconfig(self.status_text_id, text=f"DB Error: {str(e)}", fill="red")

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRegistrationApp(root)
    root.mainloop()
