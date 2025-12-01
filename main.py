import cv2

# Загрузка предобученных каскадов Хаара для детекции лиц и глаз
# GitHub OpenCV: https://github.com/opencv/opencv/tree/master/data/haarcascades
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye_tree_eyeglasses.xml')


# Функция для детекции лиц и глаз на кадре
def detect_faces_and_eyes(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Синий прямоугольник вокруг лица
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)

        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)  # Зеленый прямоугольник вокруг глаз

    return frame


def main():
    # Инициализация веб-камеры (0 - встроенная камера)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Ошибка: Не удалось открыть веб-камеру.")
        return

    print("Нажмите 'q' для выхода.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Ошибка: Не удалось захватить кадр.")
            break

        # Детекция и отрисовка
        processed_frame = detect_faces_and_eyes(frame)

        # Отображение в окне
        cv2.imshow('Детекция лиц и глаз', processed_frame)

        # Выход по нажатию 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Освобождение ресурсов
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()