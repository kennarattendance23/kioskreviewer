# attendancelog_timein.py  (fixed)
import tkinter as tk
import time
from PIL import Image, ImageTk


class AttendanceInfoScreen(tk.Toplevel):
    WIDTH = 900
    HEIGHT = 500

    def __init__(self, master, emp_id="", full_name="", temperature="", time_in="", image_path="employee.jpg"):
        super().__init__(master)
        self.title("Attendance Information")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)

        # --- Create canvas first (important) ---
        self.canvas = tk.Canvas(self, width=self.WIDTH, height=self.HEIGHT, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # --- Background Image drawn ON the canvas ---
        try:
            bg_img = Image.open("time-in.png").resize((self.WIDTH, self.HEIGHT))
            self.bg_image = ImageTk.PhotoImage(bg_img)
            # draw the background image at the top-left of the canvas
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        except Exception as e:
            # fallback background color if image not available
            self.canvas.configure(bg="#84AEE3")
            print("⚠️ Background image 'time-in.png' not found or failed to load:", e)

        # --- Title ---
        self.canvas.create_text(self.WIDTH/2.8, 60,
                                text="Attendance Information",
                                font=("Arial", 16, "bold"),
                                fill="black")

        # --- Rounded Entry Helper ---
        def round_rect(canvas, x1, y1, x2, y2, r=18, **kwargs):
            points = [
                x1+r, y1,
                x2-r, y1,
                x2, y1,
                x2, y1+r,
                x2, y2-r,
                x2, y2,
                x2-r, y2,
                x1+r, y2,
                x1, y2,
                x1, y2-r,
                x1, y1+r,
                x1, y1
            ]
            return canvas.create_polygon(points, smooth=True, **kwargs)

        def create_field(label, value, y_pos):
            # Label
            self.canvas.create_text(160, y_pos-15, text=label,
                                    font=("Arial", 10), fill="black", anchor="w")
            # Rounded rectangle
            round_rect(self.canvas, 140, y_pos-10, 400, y_pos+30, r=18,
                       fill="white", outline="#cfcfcf")
            # Value text
            self.canvas.create_text(270, y_pos+10, text=value,
                                    font=("Arial", 12), fill="black")

        # --- Employee Info Fields ---
        create_field("Employee ID", emp_id, 120)
        create_field("Full Name", full_name, 180)
        create_field("Temperature", f"{temperature}°C", 240)
        create_field("Time-In", time_in, 300)

        # --- Employee Photo ---
        try:
            img = Image.open(image_path).resize((180, 220))
            self.photo_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(650, 190, image=self.photo_image, anchor="center")
        except Exception as e:
            self.canvas.create_text(650, 190, text="[No Photo]",
                                    font=("Arial", 12), fill="red")
            print("⚠️ Photo not found:", e)

        # --- Done Button ---
        self.done_button = tk.Button(self, text="Done", font=("Arial", 10, "bold"),
                                     bg="white", fg="black", relief="flat",
                                     command=self.destroy)
        # create after canvas so button is on top
        self.done_button.place(x=600, y=350, width=120, height=40)
        self.done_button.config(highlightthickness=0, bd=0)

        # --- Bottom Bar ---
        bottom_frame = tk.Frame(self, bg="#6689bd", height=35)
        bottom_frame.pack(side="bottom", fill="x")
        bottom_frame.lift()

        self.clock_label = tk.Label(bottom_frame, text="", font=("Arial", 10),
                                    bg="#6689bd", fg="white")
        self.clock_label.pack(side="left", padx=20)

        self.date_label = tk.Label(bottom_frame, text="", font=("Arial", 10),
                                   bg="#6689bd", fg="white")
        self.date_label.pack(side="right", padx=20)

        self.update_clock()

    def update_clock(self):
        now = time.strftime("%I:%M %p").lstrip("0")
        today = time.strftime("%A, %B %d, %Y")
        self.clock_label.config(text=now)
        self.date_label.config(text=today)
        self.after(1000, self.update_clock)


# --- Example Usage (test window) ---
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main root window

    # Example data
    screen = AttendanceInfoScreen(
        root,
        emp_id="A3B9X",
        full_name="Juan P. Dela Cruz",
        temperature="36.9",
        time_in="7:49 AM",
        image_path="employee.jpg"
    )
    root.mainloop()
