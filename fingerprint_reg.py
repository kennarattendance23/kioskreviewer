import tkinter as tk
import time
from PIL import Image, ImageTk

class FingerprintRegistration(tk.Tk):
    WIDTH = 900
    HEIGHT = 500
    # Fingerprint image size (change these values to resize)
    FP_WIDTH = 190
    FP_HEIGHT = 220

    def __init__(self):
        super().__init__()
        self.title("Fingerprint Registration")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)

        # --- Canvas for UI screens ---
        self.canvas = tk.Canvas(self, width=self.WIDTH, height=self.HEIGHT, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Load and set background image
        try:
            bg_img = Image.open("Time-In.png").resize((self.WIDTH, self.HEIGHT))
            self.bg_photo = ImageTk.PhotoImage(bg_img)
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        except Exception as e:
            print("⚠️ Background image not found:", e)
            self.canvas.configure(bg="#84AEE3")  # fallback color

        # Bottom bar (clock + date)
        bottom_frame = tk.Frame(self, bg="#6689bd", height=50)
        bottom_frame.pack(side="bottom", fill="x")
        bottom_frame.lift()

        self.clock_label = tk.Label(bottom_frame, text="", font=("Arial", 10),
                                    bg="#6689bd", fg="white")
        self.clock_label.pack(side="left", padx=20)

        self.date_label = tk.Label(bottom_frame, text="", font=("Arial", 10),
                                   bg="#6689bd", fg="white")
        self.date_label.pack(side="right", padx=20)

        self.update_clock()

        # Start the process
        self.show_scan_screen()

    def show_scan_screen(self):
        """Start with empty bars and begin scanning"""
        self.canvas.delete("all")

        # Re-add background
        try:
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        except:
            self.canvas.configure(bg="#84AEE3")

        # Instruction
        self.canvas.create_text(self.WIDTH / 2, 60,
                                text="Please place your finger to the sensor for registration",
                                font=("Arial", 14),
                                fill="black")

        # Fingerprint image (resized according to FP_WIDTH, FP_HEIGHT)
        try:
            fp_img = Image.open("fingerprint.png").resize((self.FP_WIDTH, self.FP_HEIGHT))
            self.fp_photo = ImageTk.PhotoImage(fp_img)
            self.canvas.create_image(self.WIDTH / 2, 200, image=self.fp_photo, anchor="center")
        except Exception as e:
            self.canvas.create_text(self.WIDTH / 2, 200,
                                    text="[Fingerprint Image]",
                                    font=("Arial", 12), fill="black")
            print("⚠️ Fingerprint image not found:", e)

        # --- Progress bar (two halves) ---
        self.half_w, self.pb_h = 200, 25
        gap = 2
        total_w = self.half_w * 2 + gap
        self.pb_x = (self.WIDTH - total_w) // 2
        self.pb_y = 350

        # Borders
        self.canvas.create_rectangle(self.pb_x, self.pb_y,
                                     self.pb_x + self.half_w, self.pb_y + self.pb_h,
                                     outline="white", width=2)
        self.canvas.create_rectangle(self.pb_x + self.half_w + gap, self.pb_y,
                                     self.pb_x + 2*self.half_w + gap, self.pb_y + self.pb_h,
                                     outline="white", width=2)

        # Fill both bars black initially
        self.first_fill = self.canvas.create_rectangle(
            self.pb_x, self.pb_y,
            self.pb_x + self.half_w, self.pb_y + self.pb_h,
            fill="black", width=0
        )
        self.second_fill = self.canvas.create_rectangle(
            self.pb_x + self.half_w + gap, self.pb_y,
            self.pb_x + 2*self.half_w + gap, self.pb_y + self.pb_h,
            fill="black", width=0
        )
        self.green_first_fill = None
        self.green_second_fill = None
        self.gap = gap

        # Start animation
        self.progress_step = 0
        self.animate_first_scan()

    def animate_first_scan(self):
        """Turn first bar green gradually"""
        if self.green_first_fill:
            self.canvas.delete(self.green_first_fill)

        fill_width = int(self.half_w * (self.progress_step / 20))
        self.green_first_fill = self.canvas.create_rectangle(
            self.pb_x, self.pb_y,
            self.pb_x + fill_width, self.pb_y + self.pb_h,
            fill="#4CAF50", width=0
        )

        if self.progress_step < 20:
            self.progress_step += 1
            self.after(100, self.animate_first_scan)
        else:
            self.progress_step = 0
            self.after(500, self.animate_second_scan)

    def animate_second_scan(self):
        """Turn second bar green gradually"""
        if self.green_second_fill:
            self.canvas.delete(self.green_second_fill)

        fill_width = int(self.half_w * (self.progress_step / 20))
        self.green_second_fill = self.canvas.create_rectangle(
            self.pb_x + self.half_w + self.gap, self.pb_y,
            self.pb_x + self.half_w + self.gap + fill_width, self.pb_y + self.pb_h,
            fill="#4CAF50", width=0
        )

        if self.progress_step < 20:
            self.progress_step += 1
            self.after(100, self.animate_second_scan)
        else:
            self.after(2000, self.show_success_message)

    def show_success_message(self):
        x1, y1, x2, y2 = 300, 150, 600, 190
        r = 20
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r,
            x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1
        ]
        self.canvas.create_polygon(points, smooth=True, fill="#d2ffd8", outline="")

        cx, cy = x1 + 40, (y1 + y2) // 
        r_circle = 15
        self.canvas.create_oval(cx - r_circle, cy - r_circle,
                                cx + r_circle, cy + r_circle,
                                fill="#4CAF50", outline="")
        self.canvas.create_line(cx - 6, cy, cx - 2, cy + 5, fill="white", width=3)
        self.canvas.create_line(cx - 2, cy + 5, cx + 8, cy - 6, fill="white", width=3)

        self.canvas.create_text(cx + 25, cy,
                                text="Biometrics scanned successfully.",
                                font=("Arial", 12),
                                fill="black", anchor="w")

    def update_clock(self):
        now = time.strftime("%I:%M %p").lstrip("0")
        today = time.strftime("%A, %B %d, %Y")
        self.clock_label.config(text=now)
        self.date_label.config(text=today)
        self.after(1000, self.update_clock)


if __name__ == "__main__":
    app = FingerprintRegistration()
    app.mainloop()
