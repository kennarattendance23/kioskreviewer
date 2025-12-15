import tkinter as tk
import time
import cv2
from PIL import Image, ImageTk, ImageDraw
import facialrecognition
import fingerprint
from temperature import TemperatureScreen, get_temperature
from attendancelog import AttendanceInfoScreen
from attendance_db import log_attendance
from attendance_db import mark_absent_employees
import os
from tkinter import messagebox
os.chdir("/home/kennarautoshop/Desktop/kennarautoshop_attendancesystem/attendance")


# --- Fullscreen & Kiosk Helper Function ---
def make_fullscreen(window):
    window.attributes("-fullscreen", True)
    window.config(cursor="none")
    window.resizable(False, False)
    window.protocol("WM_DELETE_WINDOW", lambda: None)
    window.bind("<Escape>", lambda e: None)
    window.bind("<Alt-F4>", lambda e: None)
    window.bind("<Control-Shift-Q>", lambda e: exit_kiosk(window))

def exit_kiosk(window):
    print("Admin exit triggered. Exiting kiosk mode...")
    try:
        if hasattr(window, "cap"):
            window.cap.release()
    except:
        pass
    window.destroy()

# --- Fade transition helpers ---
def fade_out(window, step=0.05, delay=20):
    try:
        alpha = window.attributes("-alpha")
        if alpha > 0:
            alpha = max(alpha - step, 0)
            window.attributes("-alpha", alpha)
            window.after(delay, lambda: fade_out(window, step, delay))
    except:
        pass

def fade_in(window, step=0.05, delay=20):
    try:
        alpha = window.attributes("-alpha")
        if alpha < 1:
            alpha = min(alpha + step, 1)
            window.attributes("-alpha", alpha)
            window.after(delay, lambda: fade_in(window, step, delay))
    except:
        pass

# --- Rounded Button ---
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None,
                 bg="#cfecf7", hover_bg="#b5d8e6", active_bg="#9fc6d8",
                 fg="black", font=("Arial", 12, "bold"), radius=20, padding=10):
        super().__init__(parent, highlightthickness=0, bg=parent["bg"])
        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self.fg = fg
        self.font = font
        self.radius = radius
        self.padding = padding

        self.width = 160
        self.height = 50

        self.round_rect = self.create_round_rect(
            5, 5, self.width, self.height, radius=self.radius, fill=self.bg, outline=self.bg
        )
        self.text = self.create_text(
            self.width // 2, self.height // 2, text=text, fill=self.fg, font=self.font
        )

        self.config(width=self.width + self.padding, height=self.height + self.padding)

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

        self.tag_bind(self.text, "<Enter>", self.on_enter)
        self.tag_bind(self.text, "<Leave>", self.on_leave)
        self.tag_bind(self.text, "<Button-1>", self.on_click)
        self.tag_bind(self.text, "<ButtonRelease-1>", self.on_release)

    def create_round_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1,
            x2, y1 + radius, x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2, x1, y2,
            x1, y2 - radius, x1, y1 + radius, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, event=None):
        self.itemconfig(self.round_rect, fill=self.hover_bg, outline=self.hover_bg)

    def on_leave(self, event=None):
        self.itemconfig(self.round_rect, fill=self.bg, outline=self.bg)

    def on_click(self, event=None):
        self.itemconfig(self.round_rect, fill=self.active_bg, outline=self.active_bg)

    def on_release(self, event=None):
        if self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery()) == self:
            self.itemconfig(self.round_rect, fill=self.hover_bg, outline=self.hover_bg)
        else:
            self.itemconfig(self.round_rect, fill=self.bg, outline=self.bg)
        if self.command:
            self.command()

# --- Employee Info Screen ---
class EmployeeInfoScreen(tk.Toplevel):
    def __init__(self, master, emp_id="", full_name="", image_path="", mode="Time-In"):
        super().__init__(master)
        make_fullscreen(self)
        self.attributes("-alpha", 0.0)
        fade_in(self)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        # --- Background image ---
        self.canvas = tk.Canvas(self, width=screen_w, height=screen_h, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            bg_img = Image.open("Time-In.png").resize((screen_w, screen_h))
            self.bg_photo = ImageTk.PhotoImage(bg_img)
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        except Exception as e:
            self.canvas.configure(bg="#a3c7f0")
            print("⚠️ Background image not found:", e)

        left_x = screen_w * 0.35
        center_y = screen_h / 2 - 40

        # --- Title ---
        self.canvas.create_text(screen_w / 2, center_y - 200,
                                text="Check the Information",
                                font=("Arial", 24, "bold"), fill="#1b1b1b", anchor="center")

        # --- Labels ---
        self.canvas.create_text(left_x - 90, center_y - 70, text="Employee ID",
                                font=("Arial", 11), fill="#1b1b1b", anchor="w")
        self.canvas.create_text(left_x - 90, center_y + 10, text="Full Name",
                                font=("Arial", 11), fill="#1b1b1b", anchor="w")

        # --- Capsule Box ---
        def draw_capsule_box(canvas, x, y, width, height, r=25, text_value=""):
            x1, y1 = x - width / 2, y - height / 2
            x2, y2 = x + width / 2, y + height / 2
            points_box = [
                x1 + r, y1, x2 - r, y1, x2, y1,
                x2, y1 + r, x2, y2 - r, x2, y2,
                x2 - r, y2, x1 + r, y2, x1, y2,
                x1, y2 - r, x1, y1 + r, x1, y1
            ]
            canvas.create_polygon(points_box, smooth=True, fill="#e0e0e0", outline="#e0e0e0")
            canvas.create_polygon(points_box, smooth=True, fill="white", outline="#dcdcdc")
            canvas.create_text(x, y, text=text_value, font=("Arial", 13), fill="#000000")

        draw_capsule_box(self.canvas, left_x, center_y - 40, 320, 40, text_value=emp_id)
        draw_capsule_box(self.canvas, left_x, center_y + 40, 320, 40, text_value=full_name)

        # --- Photo ---
        photo_x = screen_w * 0.7
        photo_y = center_y
        try:
            img = Image.open(image_path).resize((200, 240))
            self.photo_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(photo_x, photo_y, image=self.photo_image, anchor="center")
        except Exception as e:
            self.canvas.create_text(photo_x, photo_y, text="[Photo not found]",
                                    font=("Arial", 12), fill="#666")
            print("⚠️ Photo not found:", e)

        # --- Status message ---
        self.status_text_id = self.canvas.create_text(
            left_x, center_y + 120,
            text="Please scan your fingerprint to proceed.",
            font=("Arial", 11, "italic"), fill="#2e2e2e", anchor="center"
        )

        # --- Bottom clock and date ---
        bottom_frame = tk.Frame(self, bg="#6689bd", height=40)
        bottom_frame.pack(side="bottom", fill="x")
        self.clock_label = tk.Label(bottom_frame, text="", font=("Arial", 10), bg="#6689bd", fg="white")
        self.clock_label.pack(side="left", padx=20)
        self.date_label = tk.Label(bottom_frame, text="", font=("Arial", 10), bg="#6689bd", fg="white")
        self.date_label.pack(side="right", padx=20)
        self.update_clock()

        self.emp_id = emp_id
        self.full_name = full_name
        self.image_path = image_path
        self.mode = mode
        self.attempts = 0
        self.max_attempts = 2
        self.after(2000, self.check_fingerprint)

    def update_clock(self):
        now = time.strftime("%I:%M %p").lstrip("0")
        today = time.strftime("%A, %B %d, %Y")
        self.clock_label.config(text=now)
        self.date_label.config(text=today)
        self.after(1000, self.update_clock)

    def check_fingerprint(self):
        try:
            success = fingerprint.wait_for_fingerprint(self.emp_id)
        except Exception as e:
            success = False
            print("⚠️ Fingerprint error:", e)

        if success:
            self.canvas.itemconfig(self.status_text_id, text="✅ Fingerprint verified!", fill="green")
            self.after(500, self.show_temperature_screen)
        else:
            self.attempts += 1
            if self.attempts < self.max_attempts:
                self.canvas.itemconfig(
                    self.status_text_id,
                    text=f"❌ Fingerprint mismatch! Attempt {self.attempts}/{self.max_attempts}",
                    fill="red"
                )
                self.after(2000, self.check_fingerprint)
            else:
                self.canvas.itemconfig(
                    self.status_text_id,
                    text="❌ Too many failed attempts. Returning to idle...",
                    fill="red"
                )
                self.after(2500, self.destroy)

    def show_temperature_screen(self):
        fade_out(self)
        self.after(400, lambda: (
        TemperatureScreenWithAttendance(
            self.master,
            self.emp_id,
            self.full_name,
            self.image_path,
            self.mode
        ),
        self.destroy()  # ✅ properly close the Employee Info Screen
    ))

# --- Temperature + Attendance ---
class TemperatureScreenWithAttendance(TemperatureScreen):
    def __init__(self, master, emp_id, full_name, image_path, mode):
        super().__init__(master)
        make_fullscreen(self)
        self.attributes("-alpha", 0.0)
        fade_in(self)
        self.emp_id = emp_id
        self.full_name = full_name
        self.image_path = image_path
        self.mode = mode
        self.after(3000, self.show_attendance_log)

    def show_attendance_log(self):
        temp_value = get_temperature() or 0.0
        log_attendance(self.emp_id, self.full_name, float(temp_value), self.mode)
        AttendanceInfoScreen(
            self.master,
            emp_id=self.emp_id,
            full_name=self.full_name,
            temperature=f"{temp_value:.1f}",
            attendance_time=time.strftime("%I:%M %p").lstrip("0"),
            attendance_type=self.mode,
            image_path=self.image_path
        )
        self.destroy()

# --- Idle Screen ---
class IdleScreen(tk.Tk):
    def __init__(self, video_path="workshop.mp4"):
        super().__init__()
        self.title("Kennar Auto Shop - Attendance System")
        make_fullscreen(self)
        self.attributes("-alpha", 1.0)
        self.lift()
        self.attributes("-topmost", True)
        self.after(1000, lambda: self.attributes("-topmost", False))

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")
        self.configure(bg="#5E77A0")

        self.video_path = video_path
        self.cap = cv2.VideoCapture(self.video_path)
        self.video_label = tk.Label(self, bg="#5E77A0")
        self.video_label.pack(side="left", fill="both", expand=True)

        center_frame = tk.Frame(self, width=300, height=500, bg="#5E77A0")
        center_frame.pack(side="left", fill="both", expand=False)

        content_frame = tk.Frame(center_frame, bg="#5E77A0")
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.clock_label = tk.Label(content_frame, text="", font=("Arial", 36, "bold"), fg="white", bg="#5E77A0")
        self.clock_label.pack(pady=(0, 10))
        self.date_label = tk.Label(content_frame, text="", font=("Arial", 12), fg="white", bg="#5E77A0")
        self.date_label.pack(pady=(0, 40))

        self.btn_in = RoundedButton(content_frame, text="Time - In", command=self.time_in)
        self.btn_in.pack(pady=20)
        self.btn_out = RoundedButton(content_frame, text="Time - Out", command=self.time_out)
        self.btn_out.pack(pady=10)
        # --- REGISTER BUTTON ---
        self.btn_register = RoundedButton(content_frame, text="Register", command=self.open_registration)
        self.btn_register.pack(pady=10)

        self.is_processing = False

        self.update_clock()
        self.update_video()

    # --- UPDATE CLOCK/VIDEO ---
    def update_clock(self):
        now = time.strftime("%I:%M %p").lstrip("0")
        today = time.strftime("%A, %B %d, %Y")
        self.clock_label.config(text=now)
        self.date_label.config(text=today)
        self.after(1000, self.update_clock)

    def update_video(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (750, 600))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            self.video_label.config(image=img)
            self.video_label.image = img
        self.after(33, self.update_video)


        # --- FIXED: OPEN REGISTRATION ---
    def open_registration(self):
        try:
            from facial_fingerprint_registration import FacialFingerprintRegistration
            reg_window = FacialFingerprintRegistration(master=self)
            reg_window.grab_set()
            self.wait_window(reg_window)
            self.deiconify()
        except Exception as e:
            print("⚠️ Failed to open registration:", e)
            messagebox.showerror("Registration Error", f"Failed to open registration:\n{e}")



    # --- FACIAL RECOGNITION METHODS ---
    def run_facial_recognition(self, mode):
        if getattr(self, "is_processing", False):
            print("⚠️ Recognition already in progress...")
            return
        self.is_processing = True
        self.btn_in.itemconfig(self.btn_in.round_rect, fill="#cccccc")
        self.btn_out.itemconfig(self.btn_out.round_rect, fill="#cccccc")

        fade_out(self)
        self.after(400, lambda: self.start_facial_recognition_process(mode))

    def attempt_camera_recovery(self):
        """
        Try to call optional cleanup helpers in other modules to free camera resources.
        These functions are optional — if present in modules we call them.
        """
        print("Attempting camera recovery...")
        # try to call facialrecognition.cleanup or release_camera if provided
        try:
            if hasattr(facialrecognition, "release_camera"):
                facialrecognition.release_camera()
                print("Called facialrecognition.release_camera()")
        except Exception as e:
            print("facialrecognition.release_camera() failed:", e)
        # try fingerprint cleanup (if it holds serial resource)
        try:
            if hasattr(fingerprint, "release_sensor"):
                fingerprint.release_sensor()
                print("Called fingerprint.release_sensor()")
        except Exception as e:
            print("fingerprint.release_sensor() failed:", e)

    def start_facial_recognition_process(self, mode):
        try:
            try:
                result = facialrecognition.start_facial_recognition(mode)
            except RuntimeError as re:
                # handle Picamera2 "Device or resource busy" / init errors
                msg = str(re)
                print("Camera init error:", msg)
                # Try one recovery attempt
                self.attempt_camera_recovery()
                # small short delay to allow cleanup
                time.sleep(0.6)
                try:
                    result = facialrecognition.start_facial_recognition(mode)
                except Exception as re2:
                    # still failed — inform admin with helpful message
                    print("Second attempt failed:", re2)
                    messagebox.showerror("Camera Error",
                                         "Camera initialization failed (device busy). "
                                         "Make sure no other camera window (registration) is open and try again.")
                    result = {"ok": False, "message": "Camera busy or initialization failed."}
            fade_in(self)
            if isinstance(result, str):
                if result == "ALREADY_LOGGED":
                    print("⚠️ Already Timed-In. Returning to Idle.")
                    return
                result = {"ok": False, "message": result}

            if result.get("ok"):
                EmployeeInfoScreen(
                    self,
                    emp_id=result.get("emp_id", ""),
                    full_name=result.get("full_name", ""),
                    image_path=result.get("image_path", ""),
                    mode=mode
                )
            else:
                print(f"{mode} failed: {result.get('message', 'Unknown error')}")
        except Exception as e:
            print("Unexpected error during facial recognition:", e)
            # If Picamera2 raised a different error during init
            if "Camera _init_ sequence did not complete" in str(e) or "Failed to acquire camera" in str(e):
                # Attempt recovery once
                self.attempt_camera_recovery()
                messagebox.showerror("Camera Error", "Camera failed to initialize. Please close other camera windows and try again.")
            else:
                messagebox.showerror("Recognition Error", f"An unexpected error occurred:\n{e}")
        finally:
            self.is_processing = False
            self.reset_button_colors()

    def reset_button_colors(self):
        self.btn_in.itemconfig(self.btn_in.round_rect, fill=self.btn_in.bg)
        self.btn_out.itemconfig(self.btn_out.round_rect, fill=self.btn_out.bg)

    def time_in(self):
        print("Starting facial recognition for Time-In...")
        self.run_facial_recognition("Time-In")

    def time_out(self):
        print("Starting facial recognition for Time-Out...")
        self.run_facial_recognition("Time-Out")

# --- Run App ---
if __name__ == "__main__":
    app = IdleScreen("montage.MP4")
    app.mainloop()
