import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps, ImageSequence, ImageTk
import os
import sys
import subprocess
import platform

# Simple YAML parser since no external deps allowed beyond PIL
def load_yaml(file_path):
    config = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        # Convert types
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '', 1).isdigit():
                            value = float(value)
                        config[key] = value
    except Exception:
        pass
    return config

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
        if P == "":
            return True
        try:
            val = int(P)
            return val >= 0
        except ValueError:
            return False
    
    def validate_quality(self, P):
        """Validate quality 1-100."""
        if P == "":
            return True
        try:
            val = int(P)
            return 1 <= val <= 100
        except ValueError:
            return False
    
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
        
        # GIF frame (>=0)
        gif_frame = tk.Frame(left_frame)
        gif_frame.pack(pady=5, fill="x")
        tk.Label(gif_frame, text="GIF Frame to Extract (0-based):", anchor="w").pack(side=tk.LEFT)
        tk.Entry(gif_frame, textvariable=self.gif_frame, width=5, validate="key", validatecommand=vcmd_pos).pack(side=tk.LEFT, padx=10)
        
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
                self.show_preview(self.input_paths[index])
    
    def browse_output(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir.set(dir_path)
    
    def show_preview(self, file_path):
        try:
            # Load original
            img = Image.open(file_path)
            
            # Apply current transformations for live preview (same as convert logic)
            # Handle GIF (extract frame)
            if file_path.lower().endswith('.gif'):
                frame_index = max(0, self.gif_frame.get())
                frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                if frame_index < len(frames):
                    img = frames[frame_index]
                else:
                    img = frames[0] if frames else img
            
            # Resize if enabled
            if self.enable_resize.get():
                width = max(1, self.resize_width.get())
                height = max(1, self.resize_height.get())
                if width > 0 and height > 0:
                    if self.maintain_aspect.get():
                        img.thumbnail((width, height), Image.Resampling.LANCZOS)
                    else:
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Rotate (clamp 0-360)
            degrees = max(0, min(360, self.rotate_degrees.get()))
            if degrees != 0:
                img = img.rotate(degrees, expand=True)
            
            # Grayscale
            if self.grayscale.get():
                img = ImageOps.grayscale(img)
            
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
            
            # Show frame count for GIFs
            if file_path.lower().endswith('.gif'):
                try:
                    frame_count = len(frames) if 'frames' in locals() else 0
                    self.frame_info_label.config(text=f"GIF Frames: {frame_count} (use 0-{frame_count-1} in GIF Frame field)")
                except:
                    self.frame_info_label.config(text="GIF Frames: Unknown")
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
                # Open image
                img = Image.open(input_path)
                
                # Handle GIF
                if input_path.lower().endswith('.gif'):
                    frame_index = max(0, self.gif_frame.get())
                    frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                    if frame_index < len(frames):
                        img = frames[frame_index]
                    else:
                        img = frames[0]  # default to first
                
                # Apply transformations
                # Resize (optional - if disabled, preserve original dimensions)
                if self.enable_resize.get():
                    width = max(1, self.resize_width.get())
                    height = max(1, self.resize_height.get())
                    if width > 0 and height > 0:
                        if self.maintain_aspect.get():
                            img.thumbnail((width, height), Image.Resampling.LANCZOS)
                        else:
                            img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Rotate (clamp 0-360)
                degrees = max(0, min(360, self.rotate_degrees.get()))
                if degrees != 0:
                    img = img.rotate(degrees, expand=True)
                
                # Grayscale
                if self.grayscale.get():
                    img = ImageOps.grayscale(img)
                
                # Save with quality if applicable (clamp 1-100)
                save_kwargs = {}
                quality = max(1, min(100, self.quality.get()))
                if output_format in ['jpg', 'jpeg', 'webp']:
                    save_kwargs['quality'] = quality
                if output_format == 'webp':
                    save_kwargs['method'] = 6  # for better compression
                
                # Generate output path
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(output_dir, f"{base_name}.{output_format}")
                
                img.save(output_path, format=output_format.upper() if output_format != 'jpg' else 'JPEG', **save_kwargs)
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
            with open(config_file, 'w') as f:
                f.write("# Image Converter Configuration\n")
                input_format = os.path.splitext(self.input_paths[0])[1][1:] if self.input_paths else 'jpg'
                f.write(f"input_format: {input_format}\n")
                f.write(f"output_format: {self.output_format.get()}\n")
                f.write(f"resize_width: {self.resize_width.get()}\n")
                f.write(f"resize_height: {self.resize_height.get()}\n")
                f.write(f"maintain_aspect_ratio: {str(self.maintain_aspect.get()).lower()}\n")
                f.write(f"enable_resize: {str(self.enable_resize.get()).lower()}\n")
                f.write(f"rotate_degrees: {self.rotate_degrees.get()}\n")
                f.write(f"grayscale: {str(self.grayscale.get()).lower()}\n")
                f.write(f"quality: {self.quality.get()}\n")
                f.write(f"gif_frame: {self.gif_frame.get()}\n")
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
