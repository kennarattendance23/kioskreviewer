import os
import cv2
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from picamera2 import Picamera2
from pyfingerprint.pyfingerprint import PyFingerprint
import face_recognition
import mysql.connector

SAVE_DIR = "registered_faces"
os.makedirs(SAVE_DIR, exist_ok=True)

DB_CONFIG = {
    "host": "kennardb-mysql-moonlitguardian23-9f54.e.aivencloud.com",
    "port": 12769,
    "user": "avnadmin",
    "password": "AVNS_Qyja81mEQ4otUCCMC1S",
    "database": "defaultdb",
    "ssl_ca": "ca.pem"
}

def validate_employee_id(employee_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees WHERE employee_id=%s", (employee_id,))
    emp = cursor.fetchone()
    cursor.close(); conn.close()
    if not emp:
        return False, False
    registered = bool(emp.get("face_embedding") or emp.get("fingerprint_id"))
    return True, registered

def save_registration_to_db(employee_id, face_embedding, fingerprint_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE employees
        SET face_embedding=%s, fingerprint_id=%s
        WHERE employee_id=%s
    """, (json.dumps(face_embedding), str(fingerprint_id), employee_id))
    conn.commit(); cursor.close(); conn.close()

def get_face_embedding(face_img):
    rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    enc = face_recognition.face_encodings(rgb)
    return enc[0].tolist() if enc else None

class FacialFingerprintRegistration(tk.Toplevel):

    def __init__(self, master=None):
        super().__init__(master)
        self.attributes("-fullscreen", True)
        self.configure(bg="#d9e6f2")
        self.protocol("WM_DELETE_WINDOW", self.safe_close)

        self.employee_id = None
        self.picam = None
        self.face_embedding = None

        self.last_activity = self._current_time()
        self.bind_all("<Any-KeyPress>", self.reset_activity_timer)
        self.bind_all("<Any-Button>", self.reset_activity_timer)
        self.bind_all("<Motion>", self.reset_activity_timer)
        self.idle_seconds = 20  
        self.check_idle_timeout()

        self.build_enter_id_screen()

    def _current_time(self):
        import time
        return time.time()

    def reset_activity_timer(self, event=None):
        self.last_activity = self._current_time()

    def check_idle_timeout(self):
        import time
        if self._current_time() - self.last_activity > self.idle_seconds:
            self.cancel_to_idle()
            return
        self.after(1000, self.check_idle_timeout)

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def build_enter_id_screen(self):
        self.clear()

        bg = Image.open("Time-In.png").resize((1030, 650))
        self.bg_photo = ImageTk.PhotoImage(bg)
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(relwidth=1, relheight=1)
        bg_label.lower()

        card = tk.Frame(self, bg="#80adf0")
        card.place(relx=0.3, rely=0.5, anchor="center")

        tk.Label(
            card, text="Enter Employee ID",
            font=("Arial", 22, "bold"),
            bg="#80adf0"
        ).grid(row=0, column=0, pady=10)

        self.entry_id = tk.Entry(
            card, font=("Arial", 22),
            justify="center", width=16
        )
        self.entry_id.grid(row=1, column=0, pady=10)

        actions = tk.Frame(card, bg="#80adf0")
        actions.grid(row=2, column=0, pady=15)

        tk.Button(
            actions, text="Submit",
            font=("Arial", 18),
            width=10,
            command=self.validate_and_start_face
        ).pack(side="left", padx=10)

        tk.Button(
            actions, text="Cancel",
            font=("Arial", 18),
            width=10,
            command=self.cancel_to_idle
        ).pack(side="left", padx=10)

        keypad = tk.Frame(self, bg="#80adf0")
        keypad.place(relx=0.75, rely=0.5, anchor="center")

        keys = [
            ("1",0,0),("2",0,1),("3",0,2),
            ("4",1,0),("5",1,1),("6",1,2),
            ("7",2,0),("8",2,1),("9",2,2),
            ("⌫",3,0),("0",3,1),("CLR",3,2)
        ]

        for text, r, c in keys:
            if text == "⌫":
                cmd = lambda: self.entry_id.delete(len(self.entry_id.get())-1, tk.END)
            elif text == "CLR":
                cmd = lambda: self.entry_id.delete(0, tk.END)
            else:
                cmd = lambda t=text: self.entry_id.insert(tk.END, t)

            tk.Button(
                keypad,
                text=text,
                font=("Arial", 18),
                width=5,
                height=2,
                command=cmd
            ).grid(row=r, column=c, padx=6, pady=6)

    def validate_and_start_face(self):
        eid = self.entry_id.get().strip()
        if not eid.isdigit():
            messagebox.showerror("Error", "Invalid Employee ID")
            return

        exists, registered = validate_employee_id(eid)
        if not exists or registered:
            messagebox.showerror("Error", "Employee not eligible")
            return

        self.employee_id = eid
        self.start_face_registration()

    def start_face_registration(self):
        self.clear()

        bg = Image.open("Time-In.png").resize((1030, 650))
        self.bg_photo = ImageTk.PhotoImage(bg)
        tk.Label(self, image=self.bg_photo).place(relwidth=1, relheight=1)

        tk.Label(self, text="Face Registration", font=("Arial", 22, "bold"), bg="#80adf0").pack(pady=12)

        self.cam_label = tk.Label(self)
        self.cam_label.pack()

        tk.Button(self, text="Capture", font=("Arial", 18), command=self.capture_face).pack(pady=10)
        tk.Button(self, text="Cancel", font=("Arial", 18), command=self.cancel_to_idle).pack()

        self.picam = Picamera2()
        self.picam.configure(self.picam.create_preview_configuration(main={"format": "RGB888"}))
        self.picam.start()
        self.update_camera_loop()

    def update_camera_loop(self):
        if not self.picam:
            return
        frame = self.picam.capture_array()
        img = ImageTk.PhotoImage(Image.fromarray(frame))
        self.cam_label.configure(image=img)
        self.cam_label.image = img
        self.after(30, self.update_camera_loop)

    def capture_face(self):
        frame = self.picam.capture_array()
        emb = get_face_embedding(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        if not emb:
            messagebox.showerror("Error", "No face detected")
            return

        self.face_embedding = emb
        self.picam.stop(); self.picam.close(); self.picam = None
        self.start_fingerprint_registration()

    def start_fingerprint_registration(self):
        self.clear()

        bg = Image.open("Time-In.png").resize((1030, 650))
        self.bg_photo = ImageTk.PhotoImage(bg)
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(relwidth=1, relheight=1)
        bg_label.lower()

        self.configure(bg="#80adf0")

        container = tk.Frame(self, bg="#80adf0")
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            container,
            text="Please place your finger to the sensor for registration",
            font=("Arial", 22, "bold"),  
            bg="#80adf0"
        ).pack(pady=(0, 10))

        self.fp_status = tk.Label(
            container,
            text="Waiting for finger",
            font=("Arial", 22, "bold"),  
            fg="#2b4cff",
            bg="#80adf0"
        )
        self.fp_status.pack(pady=(0, 20))

        fp_img = Image.open("fingerprint.png").resize((200, 240))  
        self.fp_photo = ImageTk.PhotoImage(fp_img)
        tk.Label(container, image=self.fp_photo, bg="#80adf0").pack(pady=(0,20))

        self.scan_bar_bg = tk.Frame(container, bg="black", width=400, height=20)  
        self.scan_bar_bg.pack(pady=20)

        self.scan_bar_part1 = tk.Frame(self.scan_bar_bg, bg="green", width=0, height=20)
        self.scan_bar_part1.place(x=0, y=0)

        self.scan_bar_part2 = tk.Frame(self.scan_bar_bg, bg="green", width=0, height=20)
        self.scan_bar_part2.place(x=200, y=0)

        tk.Button(
            container,
            text="CANCEL",
            font=("Arial", 22, "bold"),  
            width=14,
            bg="#dbe7f6",
            relief="flat",
            command=self.cancel_to_idle
        ).pack(pady=(10,0))

        self.after(500, self.scan_fingerprint)


    def fill_scan_bar(self, bar, target_width, callback=None):
        current_width = bar.winfo_width()
        if current_width < target_width:
            bar.config(width=current_width + 8)
            self.after(30, lambda: self.fill_scan_bar(bar, target_width, callback))
        else:
            if callback:
                callback()

    def scan_fingerprint(self):
        self.fp_status.config(text="Scanning...")
        fp = PyFingerprint('/dev/serial0', 57600, 0xFFFFFFFF, 0x00000000)
        if not fp.verifyPassword():
            messagebox.showerror("Error", "Fingerprint sensor error")
            return

        def step1():
            if not fp.readImage():
                self.after(100, step1)
                return
            fp.convertImage(0x01)

            for i in range(fp.getTemplateCount()):
                fp.loadTemplate(i, 0x02)
                score = fp.compareCharacteristics()
                if score > 40:
                    self.scan_bar_part1.config(width=0)
                    self.scan_bar_part2.config(width=0)
                    self.fp_status.config(text="Waiting for finger")
                    self.after(100, lambda: messagebox.showerror("Duplicate", "Fingerprint already registered"))
                    self.after(2000, step1)
                    return

            self.scan_bar_part1.config(width=200)
            self.fp_status.config(text="Remove finger...")
            self.after(1500, step2)

        def step2():
            self.fp_status.config(text="Place same finger again")
            if not fp.readImage():
                self.after(100, step2)
                return
            fp.convertImage(0x02)
            fp.createTemplate()
            pos = fp.storeTemplate()

            self.fill_scan_bar(self.scan_bar_part2, 200, callback=lambda: self.show_done_screen())
            save_registration_to_db(self.employee_id, self.face_embedding, pos)

        step1()

    def show_done_screen(self):
        self.clear()

        bg = Image.open("Time-In.png").resize((1030, 650))
        self.bg_photo = ImageTk.PhotoImage(bg)
        bg_label = tk.Label(self, image=self.bg_photo)
        bg_label.place(relwidth=1, relheight=1)
        bg_label.lower()

        tk.Label(
            self,
            text="REGISTRATION COMPLETE",
            font=("Arial", 26, "bold"),
            fg="green",
            bg="#80adf0"
        ).place(relx=0.5, rely=0.45, anchor="center")

        self.after(3000, self.safe_close)

    def cancel_to_idle(self):
        try:
            if self.picam:
                self.picam.stop(); self.picam.close()
        except:
            pass
        self.destroy()

    def safe_close(self):
        self.cancel_to_idle()

if __name__ == "__main__":
    root = tk.Tk(); root.withdraw()
    FacialFingerprintRegistration(root).grab_set()
    root.mainloop()
