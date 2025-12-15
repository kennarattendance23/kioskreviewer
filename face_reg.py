# face_reg.py
import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time

class FaceRegistrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Registration")
        self.root.attributes("-fullscreen", True)  # Fullscreen
        self.root.configure(bg="white")

        # Instruction label
        self.label = tk.Label(root, text="Please scan your face for registration",
                              font=("Arial", 20, "bold"), fg="black", bg="white")
        self.label.pack(pady=30)

        # Camera frame
        self.video_frame = tk.Label(root, bd=0, bg="white")
        self.video_frame.pack(pady=20)

        # Capture button styled (pill-shaped)
        self.capture_button = tk.Button(root, text="Capture",
                                        font=("Arial", 14, "bold"),
                                        bg="white", fg="black",
                                        relief="flat", bd=0,
                                        activebackground="#e6e6e6",
                                        command=self.capture_face)
        self.capture_button.pack(pady=30, ipadx=20, ipady=10)

        # Status Label
        self.status_label = tk.Label(root, text="", font=("Arial", 16),
                                     fg="green", bg="white")
        self.status_label.pack(pady=10)

        # Open camera
        self.cap = cv2.VideoCapture(0)
        self.update_video()

        # Exit with Esc key
        self.root.bind("<Escape>", lambda e: self.root.quit())

    def update_video(self):
        """Continuously update video feed with overlay scanning box."""
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)  # mirror effect

            # Draw scanning square in the middle
            h, w, _ = frame.shape
            box_size = 300
            x1, y1 = w//2 - box_size//2, h//2 - box_size//2
            x2, y2 = x1 + box_size, y1 + box_size
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)

            # Convert frame for Tkinter
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            screen_w = self.root.winfo_screenwidth() // 2
            img = img.resize((screen_w, 400))  # resize to fit
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_frame.imgtk = imgtk
            self.video_frame.configure(image=imgtk)

        self.root.after(10, self.update_video)

    def capture_face(self):
        """Capture face and simulate processing with possible error."""
        ret, frame = self.cap.read()
        if ret:
            # Save captured image
            cv2.imwrite("captured_face.jpg", frame)

            # Show processing status
            self.status_label.config(text="Processing...", fg="blue")
            self.root.update()

            threading.Thread(target=self.process_face).start()

    def process_face(self):
        """Simulate processing delay and then show error message."""
        time.sleep(3)  # simulate analysis
        self.status_label.config(text="Error! Please try again.", fg="red")
        messagebox.showerror("Error", "Error! Please try again.\nFacial capture unsuccessful.")

    def __del__(self):
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRegistrationApp(root)
    root.mainloop()
