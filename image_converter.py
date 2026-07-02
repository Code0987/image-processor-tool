import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import subprocess
import platform

from image_ops import (
    load_yaml,
    is_positive_int_or_empty,
    is_valid_quality,
    extract_gif_frame,
    count_gif_frames,
    apply_transforms,
    convert_single_image,
    save_config_file,
)


class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Converter")
        self.root.geometry("1250x850")
        self.root.minsize(1100, 700)
        
        # Config file handling (user selectable for multiple configs)
        self.config_path = tk.StringVar(value='config.yaml')
        # Load initial config
        self.config = load_yaml(self.config_path.get())
        self.default_config = self.config.copy()
        
        self.input_paths = []
        self.output_dir = tk.StringVar()
        self.output_format = tk.StringVar(value=self.config.get('output_format', 'png'))
        self.resize_width = tk.IntVar(value=self.config.get('resize_width', 800))
        self.resize_height = tk.IntVar(value=self.config.get('resize_height', 600))
        self.maintain_aspect = tk.BooleanVar(value=self.config.get('maintain_aspect_ratio', True))
        self.enable_resize = tk.BooleanVar(value=self.config.get('enable_resize', False))
        self.rotate_degrees = tk.IntVar(value=self.config.get('rotate_degrees', 0))
        self.grayscale = tk.BooleanVar(value=self.config.get('grayscale', False))
        self.quality = tk.IntVar(value=self.config.get('quality', 85))
        self.gif_frame = tk.IntVar(value=self.config.get('gif_frame', 0))
        
        # Traces for live preview updates when transformations change
        for var in [self.enable_resize, self.resize_width, self.resize_height, self.maintain_aspect,
                    self.rotate_degrees, self.grayscale, self.quality, self.gif_frame]:
            var.trace('w', self._update_preview_if_image_selected)
        
        self.create_widgets()
    
    def validate_positive_int(self, P):
        """Validate positive int or empty for entries."""
        return is_positive_int_or_empty(P)
    
    def validate_quality(self, P):
        """Validate quality 1-100."""
        return is_valid_quality(P)
    
    def create_widgets(self):
        # Main layout: left controls, right preview
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: controls (aligned vertically in single column)
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        # Config selection section (for multiple reusable configs)
        config_frame = tk.LabelFrame(left_frame, text="Config File")
        config_frame.pack(pady=5, fill="x")
        tk.Entry(config_frame, textvariable=self.config_path, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(config_frame, text="Browse Config", command=self.browse_config).pack(side=tk.LEFT, padx=5)
        tk.Button(config_frame, text="Load", command=self.load_config).pack(side=tk.LEFT, padx=5)
        tk.Button(config_frame, text="Save", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        # Input section
        tk.Label(left_frame, text="Input Images (multiple supported):", anchor="w").pack(pady=5, fill="x")
        self.input_listbox = tk.Listbox(left_frame, height=5, width=50)
        self.input_listbox.pack(pady=5, fill="x")
        # Bind selection change to update preview
        self.input_listbox.bind('<<ListboxSelect>>', self.on_list_select)
        input_btn_frame = tk.Frame(left_frame)
        input_btn_frame.pack(fill="x")
        tk.Button(input_btn_frame, text="Browse Images", command=self.browse_input).pack(side=tk.LEFT, padx=5)
        tk.Button(input_btn_frame, text="Clear List", command=self.clear_inputs).pack(side=tk.LEFT, padx=5)
        
        # Format selection
        format_frame = tk.Frame(left_frame)
        format_frame.pack(pady=10, fill="x")
        tk.Label(format_frame, text="Output Format:", anchor="w").pack(side=tk.LEFT)
        formats = ['jpg', 'jpeg', 'png', 'webp']
        format_combo = ttk.Combobox(format_frame, textvariable=self.output_format, values=formats, state="readonly")
        format_combo.pack(side=tk.LEFT, padx=10)
        
        # Resize
        resize_frame = tk.LabelFrame(left_frame, text="Resize")
        resize_frame.pack(pady=10, fill="x")
        tk.Label(resize_frame, text="Width:").grid(row=0, column=0, padx=5, sticky="w")
        vcmd_pos = (self.root.register(self.validate_positive_int), '%P')
        tk.Entry(resize_frame, textvariable=self.resize_width, width=10, validate="key", validatecommand=vcmd_pos).grid(row=0, column=1, padx=5)
        tk.Label(resize_frame, text="Height:").grid(row=0, column=2, padx=5, sticky="w")
        tk.Entry(resize_frame, textvariable=self.resize_height, width=10, validate="key", validatecommand=vcmd_pos).grid(row=0, column=3, padx=5)
        tk.Checkbutton(resize_frame, text="Maintain Aspect Ratio", variable=self.maintain_aspect).grid(row=1, column=0, columnspan=4, pady=5, sticky="w")
        tk.Checkbutton(resize_frame, text="Enable Resize (leave unchecked to preserve original dimensions)", variable=self.enable_resize).grid(row=2, column=0, columnspan=4, pady=5, sticky="w")
        
        # Rotate (0-360)
        rotate_frame = tk.Frame(left_frame)
        rotate_frame.pack(pady=5, fill="x")
        tk.Label(rotate_frame, text="Rotate (degrees):", anchor="w").pack(side=tk.LEFT)
        vcmd_rot = (self.root.register(self.validate_positive_int), '%P')
        tk.Entry(rotate_frame, textvariable=self.rotate_degrees, width=10, validate="key", validatecommand=vcmd_rot).pack(side=tk.LEFT, padx=10)
        
        # Options
        options_frame = tk.Frame(left_frame)
        options_frame.pack(pady=10, fill="x")
        tk.Checkbutton(options_frame, text="Grayscale (Remove Colors)", variable=self.grayscale).pack(side=tk.LEFT, padx=10)
        
        quality_frame = tk.Frame(left_frame)
        quality_frame.pack(pady=5, fill="x")
        tk.Label(quality_frame, text="Quality (1-100):", anchor="w").pack(side=tk.LEFT)
        vcmd_qual = (self.root.register(self.validate_quality), '%P')
        # Note: Scale doesn't need, but entry could; here use scale bound
        tk.Scale(quality_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.quality).pack(side=tk.LEFT, padx=10)
        
        # GIF frame slider (dynamic based on selected GIF)
        self.gif_frame = tk.IntVar(value=0)
        gif_frame = tk.Frame(left_frame)
        gif_frame.pack(pady=5, fill="x")
        tk.Label(gif_frame, text="GIF Frame to Extract (0-based):", anchor="w").pack(side=tk.LEFT)
        self.gif_slider = tk.Scale(gif_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.gif_frame, length=200)
        self.gif_slider.pack(side=tk.LEFT, padx=10)
        self.gif_max_label = tk.Label(gif_frame, text="(max: auto)")
        self.gif_max_label.pack(side=tk.LEFT, padx=5)
        
        # Output section
        tk.Label(left_frame, text="Output Directory:", anchor="w").pack(pady=5, fill="x")
        tk.Entry(left_frame, textvariable=self.output_dir, width=50).pack(fill="x")
        tk.Button(left_frame, text="Browse Output Dir", command=self.browse_output).pack(pady=5, anchor="w")
        
        # Buttons
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(pady=20, fill="x")
        tk.Button(btn_frame, text="Convert Batch", command=self.convert_images, bg="green", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Reset", command=self.reset_settings, bg="gray", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        
        # Right: preview
        right_frame = tk.Frame(main_frame, width=450)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        right_frame.pack_propagate(False)
        tk.Label(right_frame, text="Preview").pack(pady=5)
        # Use Canvas for fixed-size preview (prevents shrinking)
        self.preview_canvas = tk.Canvas(right_frame, width=400, height=400, bg="lightgray")
        self.preview_canvas.pack(pady=10, padx=10)
        # Frame info label (for GIFs)
        self.frame_info_label = tk.Label(right_frame, text="", fg="blue")
        self.frame_info_label.pack(pady=5)
    
    def browse_input(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.gif")]
        )
        if file_paths:
            for path in file_paths:
                if path not in self.input_paths:
                    self.input_paths.append(path)
                    self.input_listbox.insert(tk.END, os.path.basename(path))
            if self.input_paths:
                self.show_preview(self.input_paths[0])
    
    def clear_inputs(self):
        self.input_paths = []
        self.input_listbox.delete(0, tk.END)
    
    def browse_config(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")],
            initialdir=".",
            defaultextension=".yaml"
        )
        if file_path:
            self.config_path.set(file_path)
    
    def _update_preview_if_image_selected(self, *args):
        """Live update preview when transformation settings change."""
        if self.input_paths:
            # Use first selected or current list selection
            selection = self.input_listbox.curselection()
            idx = selection[0] if selection else 0
            if idx < len(self.input_paths):
                try:
                    self.show_preview(self.input_paths[idx])
                except:
                    # Ignore temp invalid during typing
                    pass
    
    def open_output_folder(self, folder_path):
        """Open output folder in file explorer (cross-platform)."""
        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", folder_path])
            else:  # Linux and others
                subprocess.Popen(["xdg-open", folder_path])
        except Exception:
            # Fallback: just show message, don't crash
            pass
    
    def on_list_select(self, event):
        selection = self.input_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.input_paths):
                path = self.input_paths[index]
                self.show_preview(path)
                # Update GIF slider range if GIF
                if path.lower().endswith('.gif'):
                    try:
                        frame_count = count_gif_frames(path)
                        self.gif_slider.config(to=max(0, frame_count - 1))
                        self.gif_max_label.config(text=f"(max: {frame_count-1})")
                    except Exception:
                        self.gif_slider.config(to=100)
                        self.gif_max_label.config(text="(max: 100)")
                else:
                    self.gif_slider.config(to=100)
                    self.gif_max_label.config(text="(max: N/A)")
    
    def browse_output(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir.set(dir_path)
    
    def show_preview(self, file_path):
        try:
            img = Image.open(file_path)

            # Apply current transformations for live preview (same as convert logic)
            if file_path.lower().endswith('.gif'):
                frame_count = count_gif_frames(file_path)
                img = extract_gif_frame(img, self.gif_frame.get())
            else:
                frame_count = None

            img = apply_transforms(
                img,
                enable_resize=self.enable_resize.get(),
                resize_width=self.resize_width.get(),
                resize_height=self.resize_height.get(),
                maintain_aspect=self.maintain_aspect.get(),
                rotate_degrees=self.rotate_degrees.get(),
                grayscale=self.grayscale.get(),
            )

            # Generate thumbnail for display
            display_img = img.copy()
            display_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(display_img)

            # Clear and draw on canvas
            self.preview_canvas.delete("all")
            canvas_w = self.preview_canvas.winfo_width() or 400
            canvas_h = self.preview_canvas.winfo_height() or 400
            x = (canvas_w - photo.width()) // 2
            y = (canvas_h - photo.height()) // 2
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=photo)
            self.preview_canvas.image = photo  # keep reference

            if frame_count is not None:
                self.frame_info_label.config(
                    text=f"GIF Frames: {frame_count} (use 0-{frame_count-1} in GIF Frame field)"
                )
            else:
                self.frame_info_label.config(text="")
        except Exception:
            # Silent fail for temp invalid states during typing; real errors logged internally
            self.frame_info_label.config(text="Preview unavailable (check inputs)")
            # Do not show popup for transient errors
    
    def convert_images(self):
        if not self.input_paths:
            messagebox.showerror("Error", "Please select at least one input image")
            return
        output_dir = self.output_dir.get()
        if not output_dir:
            messagebox.showerror("Error", "Please select output directory")
            return
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception:
                messagebox.showerror("Error", "Invalid output directory")
                return
        
        output_format = self.output_format.get().lower()
        success_count = 0
        errors = []
        
        for input_path in self.input_paths:
            try:
                convert_single_image(
                    input_path,
                    output_dir,
                    output_format,
                    enable_resize=self.enable_resize.get(),
                    resize_width=self.resize_width.get(),
                    resize_height=self.resize_height.get(),
                    maintain_aspect=self.maintain_aspect.get(),
                    rotate_degrees=self.rotate_degrees.get(),
                    grayscale=self.grayscale.get(),
                    quality=self.quality.get(),
                    gif_frame=self.gif_frame.get(),
                )
                success_count += 1
            except Exception as e:
                errors.append(f"{os.path.basename(input_path)}: {str(e)}")
        
        if success_count > 0:
            msg = f"Successfully converted {success_count} image(s) to {output_dir}"
            if errors:
                msg += f"\n\nErrors: {len(errors)}"
            messagebox.showinfo("Batch Success", msg)
            # Open output folder for user to see results
            self.open_output_folder(output_dir)
        else:
            messagebox.showerror("Conversion Error", "\n".join(errors) if errors else "No images converted")
    
    def save_config(self):
        config_file = self.config_path.get()
        try:
            input_format = os.path.splitext(self.input_paths[0])[1][1:] if self.input_paths else 'jpg'
            settings = {
                'output_format': self.output_format.get(),
                'resize_width': self.resize_width.get(),
                'resize_height': self.resize_height.get(),
                'maintain_aspect_ratio': self.maintain_aspect.get(),
                'enable_resize': self.enable_resize.get(),
                'rotate_degrees': self.rotate_degrees.get(),
                'grayscale': self.grayscale.get(),
                'quality': self.quality.get(),
                'gif_frame': self.gif_frame.get(),
            }
            save_config_file(config_file, settings, input_format=input_format)
            messagebox.showinfo("Success", f"Config saved to {config_file}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
    
    def load_config(self):
        config_file = self.config_path.get()
        self.config = load_yaml(config_file)
        if self.config:
            self.output_format.set(self.config.get('output_format', 'png'))
            self.resize_width.set(self.config.get('resize_width', 800))
            self.resize_height.set(self.config.get('resize_height', 600))
            self.maintain_aspect.set(self.config.get('maintain_aspect_ratio', True))
            self.enable_resize.set(self.config.get('enable_resize', False))
            self.rotate_degrees.set(self.config.get('rotate_degrees', 0))
            self.grayscale.set(self.config.get('grayscale', False))
            self.quality.set(self.config.get('quality', 85))
            self.gif_frame.set(self.config.get('gif_frame', 0))
            messagebox.showinfo("Success", f"Config loaded from {config_file}")
            # Update default_config for reset
            self.default_config = self.config.copy()
        else:
            messagebox.showwarning("Load Warning", f"Could not load config from {config_file}")
    
    def reset_settings(self):
        self.output_format.set(self.default_config.get('output_format', 'png'))
        self.resize_width.set(self.default_config.get('resize_width', 800))
        self.resize_height.set(self.default_config.get('resize_height', 600))
        self.maintain_aspect.set(self.default_config.get('maintain_aspect_ratio', True))
        self.enable_resize.set(self.default_config.get('enable_resize', False))
        self.rotate_degrees.set(self.default_config.get('rotate_degrees', 0))
        self.grayscale.set(self.default_config.get('grayscale', False))
        self.quality.set(self.default_config.get('quality', 85))
        self.gif_frame.set(self.default_config.get('gif_frame', 0))
        messagebox.showinfo("Reset", "Settings reset to defaults")

if __name__ == "__main__":
    if not os.path.exists('config.yaml'):
        # Create default if not exists
        with open('config.yaml', 'w') as f:
            f.write("""# Default configuration for image converter
input_format: jpg
output_format: png
resize_width: 800
resize_height: 600
maintain_aspect_ratio: true
enable_resize: false
rotate_degrees: 0
grayscale: false
quality: 85
gif_frame: 0
""")
    root = tk.Tk()
    app = ImageConverterApp(root)
    root.mainloop()
