import tkinter as tk
import time
from PIL import Image, ImageTk


class AttendanceInfoScreen(tk.Toplevel):
    def __init__(self, master, emp_id="", full_name="", temperature="", attendance_time="",
                 attendance_type="Time-In", image_path="employee.jpg"):
        super().__init__(master)
        self.title("Attendance Information")

        # --- Enable True Fullscreen (Kiosk Mode) ---
        self.attributes("-fullscreen", True)
        self.config(cursor="none")  # hide mouse cursor
        self.bind("<Escape>", lambda e: self.destroy())  # press Esc to exit for debugging

        # --- Force the window to fully initialize before drawing ---
        self.update_idletasks()

        # --- Use actual screen resolution ---
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # --- Create Canvas (main layout area) ---
        self.canvas = tk.Canvas(self, width=screen_w, height=screen_h, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        # --- Load Background Image ---
        try:
            bg_img = Image.open("Time-In.png").resize((screen_w, screen_h))
            self.bg_photo = ImageTk.PhotoImage(bg_img)
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        except Exception as e:
            self.canvas.configure(bg="#84AEE3")
            print("⚠️ Background image failed to load:", e)

        # --- Title ---
        self.canvas.create_text(screen_w / 2, 60,
                                text="Attendance Information",
                                font=("Arial", 20, "bold"),
                                fill="black")

        # --- Rounded Rectangle Helper ---
        def round_rect(canvas, x1, y1, x2, y2, r=18, **kwargs):
            points = [
                x1 + r, y1,
                x2 - r, y1,
                x2, y1,
                x2, y1 + r,
                x2, y2 - r,
                x2, y2,
                x2 - r, y2,
                x1 + r, y2,
                x1, y2,
                x1, y2 - r,
                x1, y1 + r,
                x1, y1
            ]
            return canvas.create_polygon(points, smooth=True, **kwargs)

        # --- Left Info Boxes ---
        def create_field(label, value, y_pos):
            self.canvas.create_text(150, y_pos - 15, text=label,
                                    font=("Arial", 11), fill="black", anchor="w")
            round_rect(self.canvas, 130, y_pos - 10, 400, y_pos + 30, r=18,
                       fill="white", outline="#cfcfcf")
            self.canvas.create_text(265, y_pos + 10, text=value,
                                    font=("Arial", 12), fill="black")

        create_field("Employee ID", emp_id, 180)
        create_field("Full Name", full_name, 240)
        create_field("Temperature", f"{temperature}°C", 300)
        create_field(attendance_type, attendance_time, 360)

        # --- Employee Photo (Right Side) ---
        try:
            img = Image.open(image_path).resize((220, 260))
            self.photo_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(740, 270, image=self.photo_image, anchor="center")
        except Exception as e:
            self.canvas.create_text(740, 270, text="[No Photo]",
                                    font=("Arial", 12), fill="red")
            print("⚠️ Photo not found:", e)

        # --- Capsule "Done" Button Below Photo ---
        self.create_done_button(740, 470)

        # --- Force redraw after fullscreen ---
        self.after(200, self.redraw_all)

    def redraw_all(self):
        """Force canvas redraw after fullscreen loads."""
        self.update_idletasks()
        self.lift()
        self.focus_force()

    def create_done_button(self, x, y):
        # --- Capsule Shadow ---
        self.canvas.create_oval(
            x - 80, y - 20, x + 80, y + 20,
            fill="#366fa8", outline=""
        )

        # --- Capsule Button (main) ---
        done_btn = tk.Button(
            self,
            text="Done",
            font=("Arial", 12, "bold"),
            bg="#4A90E2",
            fg="white",
            activebackground="#5DA9F0",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            command=self.destroy
        )
        self.canvas.create_window(x, y, window=done_btn, width=160, height=45)


# --- Example Usage ---
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    screen = AttendanceInfoScreen(
        root,
        emp_id="2",
        full_name="Joseph Legaspi",
        temperature="36.8",
        attendance_time="3:58 AM",
        attendance_type="Time-Out",
        image_path="employee.jpg"
    )
    root.mainloop()
