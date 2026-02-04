import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps, ImageSequence, ImageTk
import os
import sys

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
        self.root.geometry("1100x750")
        
        # Load config
        self.config = load_yaml('config.yaml')
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
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main layout: left controls, right preview
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: controls
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Input section
        tk.Label(left_frame, text="Input Images (multiple supported):").pack(pady=5)
        self.input_listbox = tk.Listbox(left_frame, height=5, width=50)
        self.input_listbox.pack(pady=5)
        # Bind selection change to update preview
        self.input_listbox.bind('<<ListboxSelect>>', self.on_list_select)
        input_btn_frame = tk.Frame(left_frame)
        input_btn_frame.pack()
        tk.Button(input_btn_frame, text="Browse Images", command=self.browse_input).pack(side=tk.LEFT, padx=5)
        tk.Button(input_btn_frame, text="Clear List", command=self.clear_inputs).pack(side=tk.LEFT, padx=5)
        
        # Format selection
        format_frame = tk.Frame(left_frame)
        format_frame.pack(pady=10)
        tk.Label(format_frame, text="Output Format:").grid(row=0, column=0)
        formats = ['jpg', 'jpeg', 'png', 'webp']
        format_combo = ttk.Combobox(format_frame, textvariable=self.output_format, values=formats, state="readonly")
        format_combo.grid(row=0, column=1, padx=5)
        
        # Resize
        resize_frame = tk.LabelFrame(left_frame, text="Resize")
        resize_frame.pack(pady=10, padx=20, fill="x")
        tk.Label(resize_frame, text="Width:").grid(row=0, column=0, padx=5)
        tk.Entry(resize_frame, textvariable=self.resize_width, width=10).grid(row=0, column=1)
        tk.Label(resize_frame, text="Height:").grid(row=0, column=2, padx=5)
        tk.Entry(resize_frame, textvariable=self.resize_height, width=10).grid(row=0, column=3)
        tk.Checkbutton(resize_frame, text="Maintain Aspect Ratio", variable=self.maintain_aspect).grid(row=1, column=0, columnspan=4, pady=5)
        tk.Checkbutton(resize_frame, text="Enable Resize (leave unchecked to preserve original dimensions)", variable=self.enable_resize).grid(row=2, column=0, columnspan=4, pady=5)
        
        # Rotate
        rotate_frame = tk.Frame(left_frame)
        rotate_frame.pack(pady=5)
        tk.Label(rotate_frame, text="Rotate (degrees):").pack(side=tk.LEFT)
        tk.Entry(rotate_frame, textvariable=self.rotate_degrees, width=10).pack(side=tk.LEFT, padx=5)
        
        # Options
        options_frame = tk.Frame(left_frame)
        options_frame.pack(pady=10)
        tk.Checkbutton(options_frame, text="Grayscale (Remove Colors)", variable=self.grayscale).pack(side=tk.LEFT, padx=10)
        
        quality_frame = tk.Frame(left_frame)
        quality_frame.pack(pady=5)
        tk.Label(quality_frame, text="Quality (1-100):").pack(side=tk.LEFT)
        tk.Scale(quality_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.quality).pack(side=tk.LEFT, padx=5)
        
        # GIF frame
        gif_frame = tk.Frame(left_frame)
        gif_frame.pack(pady=5)
        tk.Label(gif_frame, text="GIF Frame to Extract (0-based):").pack(side=tk.LEFT)
        tk.Entry(gif_frame, textvariable=self.gif_frame, width=5).pack(side=tk.LEFT, padx=5)
        
        # Output section
        tk.Label(left_frame, text="Output Directory:").pack(pady=5)
        tk.Entry(left_frame, textvariable=self.output_dir, width=50).pack()
        tk.Button(left_frame, text="Browse Output Dir", command=self.browse_output).pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Convert Batch", command=self.convert_images, bg="green", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Save Config", command=self.save_config, bg="blue", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Load Config", command=self.load_config, bg="blue", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Reset", command=self.reset_settings, bg="gray", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        
        # Right: preview
        right_frame = tk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        right_frame.pack_propagate(False)
        tk.Label(right_frame, text="Preview").pack(pady=5)
        self.preview_label = tk.Label(right_frame, text="Preview will appear here\nafter loading input", bg="lightgray", width=40, height=20)
        self.preview_label.pack(pady=10, padx=10)
    
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
            img = Image.open(file_path)
            # Larger thumbnail for better visibility in right panel
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # keep reference
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))
    
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
                    frame_index = self.gif_frame.get()
                    frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                    if frame_index < len(frames):
                        img = frames[frame_index]
                    else:
                        img = frames[0]  # default to first
                
                # Apply transformations
                # Resize (optional - if disabled, preserve original dimensions)
                if self.enable_resize.get():
                    width = self.resize_width.get()
                    height = self.resize_height.get()
                    if width > 0 and height > 0:
                        if self.maintain_aspect.get():
                            img.thumbnail((width, height), Image.Resampling.LANCZOS)
                        else:
                            img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Rotate
                degrees = self.rotate_degrees.get()
                if degrees != 0:
                    img = img.rotate(degrees, expand=True)
                
                # Grayscale
                if self.grayscale.get():
                    img = ImageOps.grayscale(img)
                
                # Save with quality if applicable
                save_kwargs = {}
                if output_format in ['jpg', 'jpeg', 'webp']:
                    save_kwargs['quality'] = self.quality.get()
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
        else:
            messagebox.showerror("Conversion Error", "\n".join(errors) if errors else "No images converted")
    
    def save_config(self):
        try:
            with open('config.yaml', 'w') as f:
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
            messagebox.showinfo("Success", "Config saved to config.yaml")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
    
    def load_config(self):
        self.config = load_yaml('config.yaml')
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
            messagebox.showinfo("Success", "Config loaded")
        else:
            messagebox.showwarning("Load Warning", "Could not load config")
    
    def reset_settings(self):
        self.output_format.set(self.default_config.get('output_format', 'png'))
        self.resize_width.set(self.default_config.get('resize_width', 800))
        self.resize_height.set(self.default_config.get('resize_height', 600))
        self.maintain_aspect.set(self.default_config.get('maintain_aspect_ratio', True))
        self.enable_resize.set(False)
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
