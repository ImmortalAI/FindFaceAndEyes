import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
from PIL import Image, ImageTk
import pytesseract
import os

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Text Recognition")
        self.root.geometry("900x800")
        self.root.configure(bg="#f0f0f0")
        
        self.image_path = None
        self.original_image = None
        
        # Language mapping for Tesseract
        self.languages = {
            "English": "eng",
            "Russian": "rus",
            "Japanese": "jpn",
            "English + Russian": "eng+rus",
            "English + Japanese": "eng+jpn",
            "All Three": "eng+rus+jpn"
        }
        self.selected_language = tk.StringVar(value="English")
        
        # Title
        title_label = tk.Label(
            root, 
            text="Просто OCR", 
            font=("Arial", 20, "bold"),
            bg="#f0f0f0",
            fg="#333"
        )
        title_label.pack(pady=15)
        
        # Upload button
        upload_btn = tk.Button(
            root,
            text="📁 Загрузка изображения",
            command=self.upload_image,
            font=("Arial", 12),
            bg="white",
            fg="black",
            padx=20,
            pady=10,
            cursor="hand2",
            relief=tk.RAISED,
            bd=3
        )
        upload_btn.pack(pady=10)
        
        # Language selection frame
        lang_frame = tk.Frame(root, bg="#f0f0f0")
        lang_frame.pack(pady=10)
        
        lang_label = tk.Label(
            lang_frame,
            text="Выбор языка изображения:",
            font=("Arial", 11),
            bg="#f0f0f0",
            fg="#333"
        )
        lang_label.pack(side=tk.LEFT, padx=(0, 10))
        
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.selected_language,
            values=list(self.languages.keys()),
            state="readonly",
            font=("Arial", 10),
            width=20
        )
        lang_combo.pack(side=tk.LEFT)
        
        # Frame for image and text
        content_frame = tk.Frame(root, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Image preview
        left_frame = tk.LabelFrame(
            content_frame,
            text="Предпросмотр изображения",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            fg="#333",
            padx=10,
            pady=10
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.image_label = tk.Label(
            left_frame,
            text="Изображение не загружено",
            bg="white",
            relief=tk.SUNKEN,
            bd=2
        )
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Right side - Extracted text
        right_frame = tk.LabelFrame(
            content_frame,
            text="Извлеченный текст",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            fg="#333",
            padx=10,
            pady=10
        )
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.text_area = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="white",
            relief=tk.SUNKEN,
            bd=2,
            fg="black"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Extract button
        extract_btn = tk.Button(
            root,
            text="🔍 ИЗВЛЕЧЬ БУКАВЫ",
            command=self.extract_text,
            font=("Arial", 12),
            bg="white",
            fg="black",
            padx=20,
            pady=10,
            cursor="hand2",
            relief=tk.RAISED,
            bd=3,
            state=tk.DISABLED
        )
        extract_btn.pack(pady=10)
        self.extract_btn = extract_btn
        
        # Status label
        self.status_label = tk.Label(
            root,
            text="Готов к труду и обороне!",
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="#666"
        )
        self.status_label.pack(pady=5)
    
    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="Выбери картиночку",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.image_path = file_path
                self.original_image = Image.open(file_path)
                
                # Display image
                self.display_image(self.original_image)
                
                # Enable extract button
                self.extract_btn.config(state=tk.NORMAL)
                
                self.status_label.config(text=f"Загружено: {os.path.basename(file_path)}")
                self.text_area.delete(1.0, tk.END)
                
            except Exception as e:
                messagebox.showerror("Error", f"Не удалось загрузить пикчу:\n{str(e)}")
    
    def display_image(self, image):
        # Resize image to fit the label
        display_size = (350, 400)
        image.thumbnail(display_size, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo
    
    def extract_text(self):
        if not self.image_path:
            messagebox.showwarning("Warning", "Сначала пикча, потом букавы!")
            return
        
        try:
            self.status_label.config(text="Извлекаю...")
            self.root.update()
            
            # Get selected language code
            lang_name = self.selected_language.get()
            lang_code = self.languages[lang_name]
            
            # Perform OCR with selected language
            text = pytesseract.image_to_string(self.original_image, lang=lang_code)
            
            # Display extracted text
            self.text_area.delete(1.0, tk.END)
            if text.strip():
                self.text_area.insert(tk.END, text)
                self.status_label.config(text=f"Готово! (Язык: {lang_name})")
            else:
                self.text_area.insert(tk.END, "No text found in the image.")
                self.status_label.config(text="No text detected")
                
        except pytesseract.TesseractNotFoundError:
            messagebox.showerror("Error", "Tesseract is not installed or not in PATH.\nPlease install Tesseract OCR.")
            self.status_label.config(text="Tesseract not found")
        except Exception as e:
            error_msg = str(e)
            if "failed loading language" in error_msg.lower():
                messagebox.showerror("Error", f"Language data not installed.\nPlease install Tesseract language data for: {lang_name}\n\nError: {error_msg}")
            else:
                messagebox.showerror("Error", f"Failed to extract text:\n{error_msg}")
            self.status_label.config(text="Extraction failed")

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()