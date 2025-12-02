import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

class FaceEyeDetectorApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        
        # Задаём начальный размер окна
        self.window_width = 640
        self.window_height = 540
        self.window.geometry(f"{self.window_width}x{self.window_height}")
        self.window.resizable(False, False)   # запрещаем менять размер окна (по желанию)

        # Загружаем Haar-каскады
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')

        # Открываем веб-камеру
        self.vid = cv2.VideoCapture(0)
        # Задаём разрешение камеры
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Canvas для отображения видео
        self.canvas = tk.Canvas(window, width=self.window_width, height=480, bg="black")
        self.canvas.pack(pady=5)

        # Кнопки "Сделать скриншот" и "Выход"
        btn_frame = tk.Frame(window)
        btn_frame.pack(pady=5)

        self.btn_screenshot = tk.Button(btn_frame, text="Сделать скриншот", width=20, command=self.screenshot)
        self.btn_screenshot.pack(side=tk.LEFT, padx=10)

        self.btn_exit = tk.Button(btn_frame, text="Выход", width=15, command=self.exit_app)
        self.btn_exit.pack(side=tk.LEFT, padx=10)

        self.delay = 15  # миллисекунд
        self.update()

        self.window.mainloop()

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            # Обнаружение лиц и глаз
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=10)
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)

            # Масштабируем кадр под размер canvas 
            frame_resized = cv2.resize(frame, (self.window_width, 480), interpolation=cv2.INTER_AREA)

            # Конвертируем для Tkinter
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update)

    def screenshot(self):
        ret, frame = self.vid.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)

            # Сохраняем в оригинальном разрешении камеры
            filename = "screenshot.png"
            i = 1
            while os.path.exists(filename):
                filename = f"screenshot_{i}.png"
                i += 1
            cv2.imwrite(filename, frame)
            messagebox.showinfo("Скриншот", f"Сохранён как {filename}")

    def exit_app(self):
        if messagebox.askokcancel("Выход", "Закрыть приложение?"):
            self.vid.release()
            self.window.destroy()


if __name__ == "__main__":
    FaceEyeDetectorApp(tk.Tk(), "Детектор лиц и глаз")