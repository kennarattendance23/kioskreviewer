import smbus2
import tkinter as tk
from PIL import Image, ImageTk
import time

# MLX90614 I2C settings
MLX90614_I2C_ADDR = 0x5A
MLX90614_TOBJ1 = 0x07  # Object temperature register
MLX90614_TA = 0x06     # Ambient temperature register


class MLX90614:
    def __init__(self, address=MLX90614_I2C_ADDR, bus=1):
        self.bus = smbus2.SMBus(bus)
        self.address = address

    def read_temp(self, reg):
        data = self.bus.read_word_data(self.address, reg)
        temp = (data * 0.02) - 273.15
        return temp

    def get_object_temp(self):
        return self.read_temp(MLX90614_TOBJ1)

    def get_ambient_temp(self):
        return self.read_temp(MLX90614_TA)


# ✅ CALIBRATION OFFSET
CALIBRATION_OFFSET = 4


def get_temperature():
    """Reads actual temperature from MLX90614, returns float in °C (with calibration)."""
    try:
        sensor = MLX90614()
        raw_temp = sensor.get_object_temp()
        calibrated_temp = raw_temp + CALIBRATION_OFFSET
        return calibrated_temp
    except Exception as e:
        print(f"[Temperature] Sensor error: {e}")
        return None


# ✅ Fullscreen Temperature Check Screen
class TemperatureScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Temperature Check")
        self.attributes('-fullscreen', True)

        self.screen_w = self.winfo_screenwidth()
        self.screen_h = self.winfo_screenheight()

        # Canvas background
        self.canvas = tk.Canvas(self, width=self.screen_w, height=self.screen_h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        try:
            bg_img = Image.open("Time-In.png").resize((self.screen_w, self.screen_h))
            self.bg_photo = ImageTk.PhotoImage(bg_img)
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        except Exception:
            self.canvas.configure(bg="#87b3e6")

        # Title
        self.canvas.create_text(
            self.screen_w // 2, 80,
            text="Temperature Check",
            font=("Arial", 24, "bold"),
            fill="#000000"
        )

        # Wrist image
        try:
            wrist_img = Image.open("Wrist.png").resize((300, 220))
            self.wrist_photo = ImageTk.PhotoImage(wrist_img)
            self.canvas.create_image(self.screen_w // 2, self.screen_h // 2 - 80, image=self.wrist_photo)
        except Exception:
            self.canvas.create_text(
                self.screen_w // 2, self.screen_h // 2 - 80,
                text="[Wrist Image Missing]",
                font=("Arial", 14),
                fill="#000000"
            )

        # Instructions
        self.instr_text = self.canvas.create_text(
            self.screen_w // 2, self.screen_h // 2 + 80,
            text="Please place your wrist near the scanner...",
            font=("Arial", 14),
            fill="#000000"
        )

        # Result
        self.result_text = self.canvas.create_text(
            self.screen_w // 2, self.screen_h // 2 + 140,
            text="Waiting to scan...",
            font=("Arial", 16, "bold"),
            fill="#000000"
        )

        # Initialize scanning
        self.readings = []
        self.stable_threshold = 5
        self.after(2000, self.start_scanning)

    def start_scanning(self):
        temp = get_temperature()

        if temp is not None and 30.0 <= temp <= 42.0:
            self.readings.append(temp)
            if len(self.readings) > 20:
                self.readings.pop(0)

            if len(self.readings) >= self.stable_threshold:
                avg_temp = sum(self.readings) / len(self.readings)
                diffs = [abs(t - avg_temp) for t in self.readings]
                if max(diffs) < 0.3:
                    self.show_result(avg_temp)
                    return

        self.canvas.itemconfig(self.result_text, text="Scanning wrist...", fill="#000000")
        self.after(500, self.start_scanning)

    def show_result(self, temp):
        if temp > 37.5:
            text = f"❌ Temperature Alert: {temp:.1f} °C"
            color = "red"
        else:
            text = f"✅ Normal Temperature: {temp:.1f} °C"
            color = "green"

        self.canvas.itemconfig(self.result_text, text=text, fill=color)
        self.canvas.itemconfig(self.instr_text, text="Scan complete ✅")


# Test window
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = TemperatureScreen(root)
    app.mainloop()
