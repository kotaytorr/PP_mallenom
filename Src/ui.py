import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from image_processor import ImageProcessor

# Основной класс интерфейса
class ImageApp:
    def __init__(self):
        # drag & drop
        try:
            from tkinterdnd2 import TkinterDnD, DND_FILES
            self._dnd_mod = TkinterDnD
            self._dnd_const = DND_FILES
            self.root = TkinterDnD.Tk()
            self._dnd_enabled = True
        except ImportError:
            self.root = tk.Tk()
            self._dnd_enabled = False

        self.root.title("Утилита работы с изображениями, практикант: Панов Данил Александрович")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.processor = ImageProcessor()

        self.sel_start = None
        self.sel_end = None
        self.sel_rect_id = None
        self.display_scale = 1.0

        self._build_ui()
        self._bind_events()

        if self._dnd_enabled:
            self.canvas.drop_target_register(self._dnd_const)
            self.canvas.dnd_bind('<<Drop>>', self._on_drop)

    def _build_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Левая панель
        left = ttk.Frame(self.root, width=220, padding=(8,8))
        left.grid(row=0, column=0, sticky="ns")
        left.grid_propagate(False)

        ttk.Button(left, text="Загрузить фото", command=self.on_load).pack(fill="x", pady=4)
        ttk.Button(left, text="Обрезать фото", command=self.on_crop).pack(fill="x", pady=4)
        ttk.Button(left, text="Применить чёрно-белый фильтр", command=self.on_grayscale).pack(fill="x", pady=4)
        ttk.Button(left, text="Сбросить изменения", command=self.on_reset).pack(fill="x", pady=4)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(left, text="Resize:").pack(anchor="w")
        rf = ttk.Frame(left)
        rf.pack(fill="x", pady=4)
        ttk.Label(rf, text="W:").grid(row=0, column=0)
        self.entry_w = ttk.Entry(rf, width=6)
        self.entry_w.grid(row=0, column=1, padx=4)
        ttk.Label(rf, text="H:").grid(row=0, column=2)
        self.entry_h = ttk.Entry(rf, width=6)
        self.entry_h.grid(row=0, column=3, padx=4)
        self.keep_aspect = tk.BooleanVar(value=True)
        ttk.Button(left, text="Применить", command=self.on_resize).pack(fill="x", pady=6)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=8)
        ttk.Label(left, text="Логи / Инфо:").pack(anchor="w")
        self.log_text = tk.Text(left, height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True, pady=(4,0))

        # Канвас (область для выделения области обрезки)
        canvas_frame = ttk.Frame(self.root, padding=(4,4))
        canvas_frame.grid(row=0, column=1, sticky="nsew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg="#222222")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.hbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.vbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.vbar.grid(row=0, column=1, sticky="ns")

        # Правая панель
        right = ttk.Frame(self.root, width=260, padding=(8,8))
        right.grid(row=0, column=2, sticky="ns")
        right.grid_propagate(False)

        ttk.Label(right, text="Preview:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.preview_label = ttk.Label(right)
        self.preview_label.pack(fill="both", expand=True, pady=(8,8))

        ttk.Button(right, text="Сохранить предпросмотр", command=self.on_save).pack(fill="x", pady=4)
        ttk.Label(right, text="Параметры:").pack(anchor="w", pady=(8,0))
        self.params_text = tk.Text(right, height=8, wrap="word")
        self.params_text.pack(fill="both", pady=(4,0))

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-Button-1>", self._on_double)

# Загрузка изображения с диска
    def on_load(self):
        path = filedialog.askopenfilename(
            title="Открыть файл", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff"), ("All", "*.*")]
        )
        if path:
            try:
                self.processor.load_image(path)
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return
            self._display(self.processor.get_image())
            self._update_params()

# Загрузка изображения через DND
    def on_crop(self):
        if self.sel_start is None:
            messagebox.showinfo("Info", "Нет выделенной области")
            return
        img = self.processor.get_image()
        bbox = self.canvas.bbox("IMG")
        if not bbox:
            x0, y0 = 0, 0
        else:
            x0, y0 = bbox[0], bbox[1]
        (x1, y1), (x2, y2) = self.sel_start, self.sel_end
        rel_x1 = (x1 - x0) / self.display_scale
        rel_y1 = (y1 - y0) / self.display_scale
        rel_x2 = (x2 - x0) / self.display_scale
        rel_y2 = (y2 - y0) / self.display_scale
        try:
            self.processor.crop(rel_x1, rel_y1, rel_x2, rel_y2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._display(self.processor.get_image())
        self._update_preview()
        self._update_params()
        self._clear_sel()

# Ч/Б фильтр
    def on_grayscale(self):
        try:
            self.processor.to_grayscale()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._display(self.processor.get_image())
        self._update_preview()
        self._update_params()

# Изменения разрешения
    def on_resize(self):
        w = self.entry_w.get().strip()
        h = self.entry_h.get().strip()
        if not w or not h:
            messagebox.showinfo("Info", "Введите W и H")
            return
        try:
            wi = int(w)
            hi = int(h)
            keep = bool(self.keep_aspect.get())
            self.processor.resize(wi, hi, keep_aspect=keep)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._display(self.processor.get_image())
        self._update_preview()
        self._update_params()

# Ресет изображения
    def on_reset(self):
        self.processor.reset_to_original()
        self._display(self.processor.get_image())
        self._update_preview()
        self._update_params()
        self._clear_sel()

    def on_save(self):
        img = self.processor.get_image()
        if img is None:
            messagebox.showinfo("Info", "Нет изображения для сохранения")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG","*.png"),("JPEG","*.jpg;*.jpeg"),("BMP","*.bmp")])
        if not path:
            return
        try:
            img.convert("RGB").save(path)
            messagebox.showinfo("Saved", f"Сохранено: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_press(self, event):
        if not self.processor.get_image():
            return
        self.sel_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self.sel_end = self.sel_start
        if self.sel_rect_id:
            self.canvas.delete(self.sel_rect_id)
        x, y = self.sel_start
        self.sel_rect_id = self.canvas.create_rectangle(x, y, x+1, y+1, outline="cyan", dash=(4,2), width=2)

    def _on_motion(self, event):
        if self.sel_start is None or not self.sel_rect_id:
            return
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.sel_end = (cx, cy)
        x0, y0 = self.sel_start
        self.canvas.coords(self.sel_rect_id, x0, y0, cx, cy)

    def _on_release(self, event):
        if self.sel_start is None:
            return
        self.sel_end = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        x0, y0 = self.sel_start
        x1, y1 = self.sel_end
        self.sel_start = (min(x0, x1), min(y0, y1))
        self.sel_end = (max(x0, x1), max(y0, y1))
        if abs(self.sel_end[0] - self.sel_start[0]) < 5 or abs(self.sel_end[1] - self.sel_start[1]) < 5:
            self._clear_sel()

    def _on_double(self, event):
        self._clear_sel()

    def _clear_sel(self):
        if self.sel_rect_id:
            self.canvas.delete(self.sel_rect_id)
        self.sel_start = None
        self.sel_end = None
        self.sel_rect_id = None

    def _display(self, pil_img):
        self.canvas.delete("all")
        if pil_img is None:
            return
        canvas_w = max(200, self.canvas.winfo_width() or 800)
        canvas_h = max(200, self.canvas.winfo_height() or 600)
        img_w, img_h = pil_img.size
        margin = 20
        avail_w = max(100, canvas_w - margin)
        avail_h = max(100, canvas_h - margin)
        scale = min(avail_w / img_w, avail_h / img_h, 1.0)
        self.display_scale = scale if scale > 0 else 1.0

        disp = pil_img.resize((int(img_w * scale), int(img_h * scale)), Image.LANCZOS)
        self._tk_img = ImageTk.PhotoImage(disp)
        self.canvas.create_image(margin//2, margin//2, anchor="nw", image=self._tk_img, tags=("IMG",))
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self._update_preview()
        self._update_params()

# Превью
    def _update_preview(self):
        img = self.processor.get_image()
        if img is None:
            self.preview_label.config(image="", text="(нет картинки)")
            return
        max_side = 240
        w, h = img.size
        scale = min(max_side / w, max_side / h, 1.0)
        disp = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        self._preview = ImageTk.PhotoImage(disp)
        self.preview_label.config(image=self._preview)

# Обновление параметров изображения
    def _update_params(self):
        info = self.processor.get_info()
        self.params_text.delete("1.0", tk.END)
        if info:
            lines = [
                f"Путь: {info.get('path')}",
                f"Формат: {info.get('format')}",
                f"Ширина: {info.get('width')} px",
                f"Высота: {info.get('height')} px",
                f"Режим: {info.get('mode')}",
                f"Размер файла: {self._human_size(info.get('filesize_bytes'))}"
            ]
            self.params_text.insert(tk.END, "\n".join(lines))
            self._log("Обновлены параметры: " + os.path.basename(info.get("path") or ""))
        else:
            self.params_text.insert(tk.END, "(нет изображения)")

    def _human_size(self, size):
        if size is None:
            return "N/A"
        for unit in ['B','KB','MB','GB']:
            if size < 1024:
                return f"{size:.0f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _on_drop(self, event):
        data = getattr(event, "data", None)
        if not data:
            return
        raw = data.strip()
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        path = raw.split()[0].strip("{}")
        if os.path.exists(path):
            try:
                self.processor.load_image(path)
                self._display(self.processor.get_image())
                self._update_params()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            self._log(f"DnD: файл не найден {path}")

    def run(self):
        self.root.mainloop()