import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os

class SiftMatcherApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # --- Параметры SIFT и Матчинга ---
        self.min_match_count = 10  # Минимум точек для отрисовки прямоугольника
        # Инициализация SIFT
        self.sift = cv2.SIFT_create()
        
        # Настройка FLANN для быстрого поиска совпадений
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(index_params, search_params)

        # --- Переменные состояния ---
        self.ref_image = None       # Исходное изображение (шаблон)
        self.ref_kp = None          # Ключевые точки шаблона
        self.ref_des = None         # Дескрипторы шаблона
        
        self.cap = None             # Объект видеозахвата
        self.is_running = False     # Флаг работы видео
        self.video_source_type = None # 'cam' или 'file'

        # --- Элементы GUI ---
        # Верхняя панель управления
        self.control_frame = tk.Frame(window)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.btn_load_img = tk.Button(self.control_frame, text="1. Загрузить объект (Фото)", command=self.load_reference_image)
        self.btn_load_img.pack(side=tk.LEFT, padx=5)

        self.btn_load_video = tk.Button(self.control_frame, text="2. Выбрать Видео файл", command=self.open_video_file)
        self.btn_load_video.pack(side=tk.LEFT, padx=5)

        self.btn_cam = tk.Button(self.control_frame, text="2. Включить Камеру", command=self.start_camera)
        self.btn_cam.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(self.control_frame, text="Стоп", command=self.stop_video, bg="#ffcccc")
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.lbl_status = tk.Label(self.control_frame, text="Ожидание загрузки...", fg="gray")
        self.lbl_status.pack(side=tk.RIGHT, padx=5)

        # Основная область отображения (Canvas)
        self.canvas_frame = tk.Frame(window)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="black", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Обработка закрытия окна
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.delay = 15 # Задержка между кадрами в мс
        self.update()

    def load_reference_image(self):
        """Загрузка статического изображения-шаблона"""
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                messagebox.showerror("Ошибка", "Не удалось прочитать изображение")
                return
            
            # Для ускорения можно уменьшить шаблон, если он огромный
            h, w = img.shape[:2]
            if w > 500:
                scale = 500 / w
                img = cv2.resize(img, (int(w*scale), int(h*scale)))

            self.ref_image = img
            # Вычисляем SIFT сразу при загрузке
            self.ref_kp, self.ref_des = self.sift.detectAndCompute(self.ref_image, None)
            
            self.lbl_status.config(text=f"Объект загружен: {len(self.ref_kp)} точек", fg="green")
            
            # Показываем загруженное изображение на холсте, пока видео не запущено
            self.show_static_preview(img)

    def show_static_preview(self, img_gray):
        """Отображение превью загруженного объекта"""
        if not self.is_running:
            img_rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
            self.display_image(img_rgb)

    def open_video_file(self):
        """Выбор видеофайла"""
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mov")])
        if path:
            self.stop_video()
            self.cap = cv2.VideoCapture(path)
            self.is_running = True
            self.video_source_type = 'file'
            self.lbl_status.config(text="Воспроизведение файла", fg="blue")

    def start_camera(self):
        """Запуск веб-камеры"""
        self.stop_video()
        self.cap = cv2.VideoCapture(0) # 0 - обычно индекс веб-камеры
        if not self.cap.isOpened():
             messagebox.showerror("Ошибка", "Не удалось открыть камеру")
             return
        self.is_running = True
        self.video_source_type = 'cam'
        self.lbl_status.config(text="Камера включена", fg="blue")

    def stop_video(self):
        """Остановка видеопотока"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.lbl_status.config(text="Остановлено", fg="black")

    def update(self):
        """Главный цикл обработки кадров"""
        if self.is_running and self.cap is not None:
            ret, frame = self.cap.read()
            
            if ret:
                # Если видеофайл закончился, можно пустить по кругу или остановить
                # Здесь просто обрабатываем кадр
                processed_image = self.process_frame(frame)
                self.display_image(processed_image)
            else:
                # Конец видеофайла
                if self.video_source_type == 'file':
                    self.stop_video()
                    messagebox.showinfo("Инфо", "Видео закончилось")

        # Планируем следующий вызов через self.delay мс
        self.window.after(self.delay, self.update)

    def process_frame(self, frame):
        """
        Основная логика компьютерного зрения:
        1. Найти точки на кадре.
        2. Сопоставить с точками шаблона.
        3. Найти гомографию и нарисовать прямоугольник.
        4. Нарисовать линии совпадений.
        """
        # Если шаблон не загружен, просто возвращаем кадр
        if self.ref_image is None or self.ref_des is None:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Конвертируем кадр в оттенки серого для SIFT
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Находим точки на текущем кадре
        frame_kp, frame_des = self.sift.detectAndCompute(frame_gray, None)

        # Если на кадре нет дескрипторов (темный экран и т.д.)
        if frame_des is None:
             return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Сопоставление (KNN Match)
        matches = self.flann.knnMatch(self.ref_des, frame_des, k=2)

        # Отбор хороших совпадений по тесту Лоу (Lowe's ratio test)
        good_matches = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)

        # Рисование прямоугольника обнаружения
        detected_frame = frame.copy()
        
        if len(good_matches) >= self.min_match_count:
            # Получаем координаты точек из совпадений
            src_pts = np.float32([self.ref_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([frame_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            # Находим матрицу гомографии
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            if M is not None:
                # Берем размеры исходного изображения-шаблона
                h, w = self.ref_image.shape
                # Определяем углы изображения-шаблона
                pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                # Трансформируем углы согласно найденной перспективе на новом кадре
                dst = cv2.perspectiveTransform(pts, M)

                # Рисуем зеленый многоугольник (прямоугольник) на кадре
                # frame - это BGR изображение (стандарт OpenCV)
                detected_frame = cv2.polylines(detected_frame, [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)
                self.lbl_status.config(text=f"Объект найден! Совпадений: {len(good_matches)}", fg="green")
            else:
                 self.lbl_status.config(text=f"Не удалось построить проекцию. Совпадений: {len(good_matches)}", fg="orange")
        else:
            self.lbl_status.config(text=f"Мало совпадений: {len(good_matches)}/{self.min_match_count}", fg="red")

        # Рисуем линии совпадений (Sided-by-side)
        # drawMatches создает новое изображение: [Ref Image] [Video Frame]
        img_matches = cv2.drawMatches(
            self.ref_image, self.ref_kp, 
            detected_frame, frame_kp, 
            good_matches, None, 
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
            matchColor=(0, 255, 0), # Зеленые линии
            singlePointColor=None
        )

        # Конвертация BGR -> RGB для Tkinter
        img_rgb = cv2.cvtColor(img_matches, cv2.COLOR_BGR2RGB)
        return img_rgb

    def display_image(self, img_array):
        """Конвертация numpy array в Tkinter Image и отрисовка"""
        # Ресайз для отображения, если картинка слишком большая для окна
        display_width = self.canvas.winfo_width()
        display_height = self.canvas.winfo_height()
        
        # Защита от нулевых размеров при инициализации
        if display_width < 10 or display_height < 10:
            display_width = 800
            display_height = 600

        h, w = img_array.shape[:2]
        
        # Простейшее масштабирование "по ширине", чтобы влезло
        scale = min(display_width/w, display_height/h)
        # Если картинка меньше экрана, можно не увеличивать (по желанию)
        # scale = min(scale, 1.0) 
        
        new_w, new_h = int(w * scale), int(h * scale)
        if new_w > 0 and new_h > 0:
            img_resized = cv2.resize(img_array, (new_w, new_h))
        else:
            img_resized = img_array

        image = Image.fromarray(img_resized)
        self.photo = ImageTk.PhotoImage(image=image)
        
        # Очистка и отрисовка по центру
        self.canvas.delete("all")
        self.canvas.create_image(display_width//2, display_height//2, image=self.photo, anchor=tk.CENTER)

    def on_close(self):
        self.stop_video()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # Установка геометрии окна
    root.geometry("1000x700")
    app = SiftMatcherApp(root, "OpenCV SIFT Object Detector")
    root.mainloop()