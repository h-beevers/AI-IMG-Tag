import os
import base64
import datetime
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from pathlib import Path
import unicodedata
import time

import ollama  # Requires: pip install ollama

class ImageTaggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Tagger")
        self.image_paths = []
        self.tag_suggestions = []
        self.timings = []
        self.current_index = 0
        self.exiftool_path = None
        self.model_name = tk.StringVar(value="qwen2.5vl:7b")
        self.avg_tag_time = 1.5  # seconds per image

        # Preview and tag entry
        self.preview_label = tk.Label(root)
        self.preview_label.pack(pady=10)

        self.tag_entry = tk.Entry(root, width=60)
        self.tag_entry.pack(pady=5)

        self.status_label = tk.Label(root, text="", fg="gray")
        self.status_label.pack(pady=2)

        # Progress bar for suggestion & review
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=5)

        # Load folder button at top
        self.load_btn = tk.Button(root, text="Load Folder", command=self.load_folder)
        self.load_btn.pack(pady=5)

        # Navigation frame: Prev and Next
        nav_frame = tk.Frame(root)
        nav_frame.pack(pady=5)
        self.prev_btn = tk.Button(nav_frame, text="<< Prev", command=self.prev_image)
        self.prev_btn.grid(row=0, column=0, padx=5)
        self.next_btn = tk.Button(nav_frame, text="Next >>", command=self.next_image)
        self.next_btn.grid(row=0, column=1, padx=5)

        # Suggest tags button
        self.suggest_btn = tk.Button(root, text="Suggest Tags", command=self.suggest_tags)
        self.suggest_btn.pack(pady=5)

        # Save tags button
        self.save_btn = tk.Button(root, text="Save Tags", command=self.save_tags)
        self.save_btn.pack(pady=5)

        # Batch review all button
        self.batch_btn = tk.Button(root, text="Batch Review All", command=self.batch_review_all)
        self.batch_btn.pack(pady=5)

        # Model selection
        model_frame = tk.Frame(root)
        model_frame.pack(pady=5)
        tk.Label(model_frame, text="Model:").pack(side="left")
        tk.Entry(model_frame, textvariable=self.model_name, width=20).pack(side="left")

    def find_exiftool_gui(self):
        common_paths = [
            r"C:\ExifTool\exiftool.exe",
            r"C:\EXIFtool\exiftool-13.34_64\exiftool.exe",
            r"C:\Program Files\ExifTool\exiftool.exe",
            r"C:\Windows\exiftool.exe",
            r"C:\Users\Henry\Tools\ExifTool\exiftool.exe"
        ]
        for path in common_paths:
            if os.path.isfile(path):
                return path
        messagebox.showinfo("Locate ExifTool", "ExifTool not found. Please select exiftool.exe manually.")
        return filedialog.askopenfilename(
            title="Select exiftool.exe",
            filetypes=[("Executable", "*.exe")]
        )

    def load_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Images")
        if not folder:
            return

        self.load_btn.config(state="disabled")
        self.status_label.config(text="Scanning folder...", fg="blue")

        def threaded_preview():
            exts = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]
            found = [p for p in Path(folder).rglob("*") if p.suffix.lower() in exts]
            total = len(found)
            est = total * self.avg_tag_time

            def show():
                if total == 0:
                    messagebox.showwarning("No Images", "No supported image files found.")
                    self.status_label.config(text="No images found.", fg="red")
                    self.load_btn.config(state="normal")
                    return

                msg = (
                    f"📁 Folder: {folder}\n"
                    f"🖼️ Images found: {total}\n"
                    f"⏱️ Estimated tagging time: {est/60:.1f} minutes\n\n"
                    "Do you want to proceed with loading?"
                )
                proceed = messagebox.askyesno("Confirm Folder Load", msg)
                if proceed:
                    self.image_paths = found
                    self.current_index = 0
                    self.exiftool_path = self.find_exiftool_gui()
                    self.status_label.config(text=f"Loading {total} images...", fg="blue")
                    self.root.after(100, self.show_image)
                else:
                    self.status_label.config(text="Load cancelled.", fg="red")

                self.load_btn.config(state="normal")

            self.root.after(0, show)

        threading.Thread(target=threaded_preview, daemon=True).start()

    def show_image(self):
        if not self.image_paths:
            return
        img_path = self.image_paths[self.current_index]
        try:
            img = Image.open(img_path)
            img.thumbnail((400, 400))
            img_tk = ImageTk.PhotoImage(img)
            self.preview_label.config(image=img_tk)
            self.preview_label.image = img_tk
            self.root.title(f"Tagging: {img_path.name}")
            self.tag_entry.delete(0, tk.END)
            self.status_label.config(text="")
        except Exception as e:
            self.log_error(f"Failed to load image {img_path.name}: {e}")
            messagebox.showerror("Image Error", f"Could not load image: {img_path.name}")

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.show_image()

    def save_tags(self):
        if not self.exiftool_path:
            messagebox.showerror("ExifTool Missing", "ExifTool path not set.")
            return
        raw = self.tag_entry.get().strip()
        if not raw:
            messagebox.showwarning("No Tags", "Enter tags before saving.")
            return
        tags = self.clean_tags(raw)
        img_path = self.image_paths[self.current_index]
        try:
            subprocess.run([
                self.exiftool_path,
                "-overwrite_original",
                "-codedcharacterset=utf8",
                f"-XPKeywords={tags}",
                str(img_path)
            ], capture_output=True, text=True)
            messagebox.showinfo("Success", f"Tags saved to {img_path.name}")
        except Exception as e:
            self.log_error(f"ExifTool failed for {img_path.name}: {e}")
            messagebox.showerror("Error", f"Failed to tag image: {e}")

    def suggest_tags(self):
        if not self.image_paths:
            return
        self.status_label.config(text="Querying model...", fg="blue")
        threading.Thread(target=self._suggest_thread, daemon=True).start()

    def _suggest_thread(self):
        img_path = self.image_paths[self.current_index]
        suggestion = ""
        try:
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            resp = ollama.chat(
                model=self.model_name.get(),
                messages=[{
                    "role": "user",
                    "content": (
                        "Generate a concise, comma-separated list of 5–10 relevant keywords "
                        "for metadata tagging. Avoid repetition or stylistic elaboration."
                    ),
                    "images": [b64],
                }]
            )
            suggestion = resp["message"]["content"].strip()
        except Exception as e:
            self.log_error(f"Ollama API error: {e}")

        def ui_update():
            if suggestion:
                self.tag_entry.delete(0, tk.END)
                self.tag_entry.insert(0, suggestion)
            else:
                messagebox.showerror("LLM Error", "Failed to get suggestions.")
            self.status_label.config(text="", fg="gray")

        self.root.after(0, ui_update)

    def batch_review_all(self):
        if not self.exiftool_path:
            messagebox.showerror("ExifTool Missing", "ExifTool path not set.")
            return
        if not self.image_paths:
            messagebox.showwarning("No Images", "No images loaded.")
            return

        self.tag_suggestions.clear()
        self.timings.clear()
        self.progress["maximum"] = len(self.image_paths)
        self.progress["value"] = 0

        threading.Thread(target=self._batch_thread, daemon=True).start()

    def _batch_thread(self):
        for i, img_path in enumerate(self.image_paths):
            start = time.time()
            try:
                with open(img_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                resp = ollama.chat(
                    model=self.model_name.get(),
                    messages=[{
                        "role": "user",
                        "content": (
                            "Generate a concise, comma-separated list of 5–10 relevant keywords "
                            "for metadata tagging. Avoid repetition or stylistic elaboration."
                        ),
                        "images": [b64],
                    }]
                )
                raw = resp["message"]["content"].strip()
                tags = self.clean_tags(raw)
                thumb = Image.open(img_path)
                thumb.thumbnail((100, 100))
                self.tag_suggestions.append({"path": img_path, "tags": tags, "thumb": thumb})
            except Exception as e:
                self.log_error(f"Suggestion failed for {img_path.name}: {e}")

            elapsed = time.time() - start
            self.timings.append(elapsed)
            if len(self.timings) >= 3:
                avg = sum(self.timings) / len(self.timings)
                rem = int(avg * (len(self.image_paths) - i - 1))
                status = f"Processing {img_path.name} ({i+1}/{len(self.image_paths)}) — ~{rem}s left"
            else:
                status = f"Processing {img_path.name} ({i+1}/{len(self.image_paths)})"

            self.root.after(0, lambda v=i+1: self.progress.config(value=v))
            self.root.after(0, lambda s=status: self.status_label.config(text=s))

        self.root.after(0, self.review_all_tags)

    def review_all_tags(self):
        review_win = tk.Toplevel(self.root)
        review_win.title("Review Tag Suggestions")
        review_win.geometry("800x650")

        canvas = tk.Canvas(review_win)
        scrollbar = tk.Scrollbar(review_win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        )

        for item in self.tag_suggestions:
            frame = tk.Frame(scroll_frame, borderwidth=1, relief="solid", padx=5, pady=5)
            frame.pack(pady=2, fill="x")
            img_tk = ImageTk.PhotoImage(item["thumb"])
            lbl = tk.Label(frame, image=img_tk)
            lbl.image = img_tk
            lbl.grid(row=0, column=0, rowspan=2)
            tk.Label(frame, text=item["path"].name, font=("Arial", 10, "bold")).grid(
                row=0, column=1, sticky="w"
            )
            tag_box = tk.Text(frame, height=3, width=60, wrap="word")
            tag_box.insert("1.0", item["tags"])
            tag_box.grid(row=1, column=1, padx=5, sticky="ew")
            frame.columnconfigure(1, weight=1)
            var = tk.BooleanVar(value=True)
            tk.Checkbutton(frame, text="Apply", variable=var).grid(row=0, column=2)
            item["apply_var"] = var
            item["tag_box"] = tag_box

        apply_progress = ttk.Progressbar(review_win, orient="horizontal", length=400, mode="determinate")
        apply_progress.pack(pady=10)

        btn_frame = tk.Frame(review_win)
        btn_frame.pack(pady=5)
        apply_sel_btn = tk.Button(btn_frame, text="Apply Selected")
        apply_sel_btn.pack(side="left", padx=10)
        apply_all_btn = tk.Button(btn_frame, text="Apply All")
        apply_all_btn.pack(side="left", padx=10)

        def apply_thread(items):
            apply_sel_btn.config(state="disabled")
            apply_all_btn.config(state="disabled")
            total = len(items)
            apply_progress.config(maximum=total, value=0)
            for idx, itm in enumerate(items):
                tags = self.clean_tags(itm["tag_box"].get("1.0", "end").strip())
                try:
                    subprocess.run([
                        self.exiftool_path,
                        "-overwrite_original",
                        "-codedcharacterset=utf8",
                        f"-XPKeywords={tags}",
                        str(itm["path"])
                    ], capture_output=True, text=True)
                except Exception as e:
                    self.log_error(f"Metadata write failed for {itm['path'].name}: {e}")
                review_win.after(0, lambda v=idx+1: apply_progress.config(value=v))
            review_win.after(0, lambda: [review_win.destroy(), messagebox.showinfo("Done", "Images tagged.")])

        def on_apply_selected():
            to_apply = [itm for itm in self.tag_suggestions if itm["apply_var"].get()]
            threading.Thread(target=lambda: apply_thread(to_apply), daemon=True).start()

        def on_apply_all():
            threading.Thread(target=lambda: apply_thread(self.tag_suggestions), daemon=True).start()

        apply_sel_btn.config(command=on_apply_selected)
        apply_all_btn.config(command=on_apply_all)

    def clean_tags(self, tag_string):
        tags = [t.strip() for t in tag_string.replace(",", ";").split(";")]
        seen = set()
        deduped = []
        for tag in tags:
            ascii_tag = self.normalize_ascii(tag)
            if ascii_tag and ascii_tag.lower() not in seen:
                seen.add(ascii_tag.lower())
                deduped.append(ascii_tag)
        return "; ".join(deduped)

    def normalize_ascii(self, text):
        return ''.join(
            c for c in unicodedata.normalize('NFKD', text)
            if not unicodedata.combining(c) and ord(c) < 128
        )

    def log_error(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("tagger_errors.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageTaggerApp(root)
    root.mainloop()