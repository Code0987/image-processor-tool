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
        self.root.geometry("800x600")
        
        # Load config
        self.config = load_yaml('config.yaml')
        self.default_config = self.config.copy()
        
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.output_format = tk.StringVar(value=self.config.get('output_format', 'png'))
        self.resize_width = tk.IntVar(value=self.config.get('resize_width', 800))
        self.resize_height = tk.IntVar(value=self.config.get('resize_height', 600))
        self.maintain_aspect = tk.BooleanVar(value=self.config.get('maintain_aspect_ratio', True))
        self.rotate_degrees = tk.IntVar(value=self.config.get('rotate_degrees', 0))
        self.grayscale = tk.BooleanVar(value=self.config.get('grayscale', False))
        self.quality = tk.IntVar(value=self.config.get('quality', 85))
        self.gif_frame = tk.IntVar(value=self.config.get('gif_frame', 0))
        
        self.create_widgets()
    
    def create_widgets(self):
        # Input section
        tk.Label(self.root, text="Input Image:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.input_path, width=50).pack()
        tk.Button(self.root, text="Browse", command=self.browse_input).pack(pady=5)
        
        # Format selection
        format_frame = tk.Frame(self.root)
        format_frame.pack(pady=10)
        tk.Label(format_frame, text="Output Format:").grid(row=0, column=0)
        formats = ['jpg', 'jpeg', 'png', 'webp']
        format_combo = ttk.Combobox(format_frame, textvariable=self.output_format, values=formats, state="readonly")
        format_combo.grid(row=0, column=1, padx=5)
        
        # Resize
        resize_frame = tk.LabelFrame(self.root, text="Resize")
        resize_frame.pack(pady=10, padx=20, fill="x")
        tk.Label(resize_frame, text="Width:").grid(row=0, column=0, padx=5)
        tk.Entry(resize_frame, textvariable=self.resize_width, width=10).grid(row=0, column=1)
        tk.Label(resize_frame, text="Height:").grid(row=0, column=2, padx=5)
        tk.Entry(resize_frame, textvariable=self.resize_height, width=10).grid(row=0, column=3)
        tk.Checkbutton(resize_frame, text="Maintain Aspect Ratio", variable=self.maintain_aspect).grid(row=1, column=0, columnspan=4, pady=5)
        
        # Rotate
        rotate_frame = tk.Frame(self.root)
        rotate_frame.pack(pady=5)
        tk.Label(rotate_frame, text="Rotate (degrees):").pack(side=tk.LEFT)
        tk.Entry(rotate_frame, textvariable=self.rotate_degrees, width=10).pack(side=tk.LEFT, padx=5)
        
        # Options
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=10)
        tk.Checkbutton(options_frame, text="Grayscale (Remove Colors)", variable=self.grayscale).pack(side=tk.LEFT, padx=10)
        
        quality_frame = tk.Frame(self.root)
        quality_frame.pack(pady=5)
        tk.Label(quality_frame, text="Quality (1-100):").pack(side=tk.LEFT)
        tk.Scale(quality_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.quality).pack(side=tk.LEFT, padx=5)
        
        # GIF frame
        gif_frame = tk.Frame(self.root)
        gif_frame.pack(pady=5)
        tk.Label(gif_frame, text="GIF Frame to Extract (0-based):").pack(side=tk.LEFT)
        tk.Entry(gif_frame, textvariable=self.gif_frame, width=5).pack(side=tk.LEFT, padx=5)
        
        # Output section
        tk.Label(self.root, text="Output Path:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.output_path, width=50).pack()
        tk.Button(self.root, text="Browse Output", command=self.browse_output).pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Convert", command=self.convert_image, bg="green", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Save Config", command=self.save_config, bg="blue", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Load Config", command=self.load_config, bg="blue", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Reset", command=self.reset_settings, bg="gray", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        
        # Preview area (optional, simple)
        self.preview_label = tk.Label(self.root, text="Preview will appear here after loading input")
        self.preview_label.pack(pady=10)
    
    def browse_input(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.gif")]
        )
        if file_path:
            self.input_path.set(file_path)
            self.show_preview(file_path)
    
    def browse_output(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{self.output_format.get()}",
            filetypes=[("Image files", f"*.{self.output_format.get()}")]
        )
        if file_path:
            self.output_path.set(file_path)
    
    def show_preview(self, file_path):
        try:
            img = Image.open(file_path)
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # keep reference
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))
    
    def convert_image(self):
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select input and output paths")
            return
        
        try:
            # Open image
            img = Image.open(input_path)
            
            # Handle GIF
            output_format = self.output_format.get().lower()
            if input_path.lower().endswith('.gif'):
                frame_index = self.gif_frame.get()
                frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                if frame_index < len(frames):
                    img = frames[frame_index]
                else:
                    img = frames[0]  # default to first
            
            # Apply transformations
            # Resize
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
            
            # Ensure correct extension
            if not output_path.lower().endswith(f'.{output_format}'):
                output_path += f'.{output_format}'
            
            img.save(output_path, format=output_format.upper() if output_format != 'jpg' else 'JPEG', **save_kwargs)
            messagebox.showinfo("Success", f"Image converted and saved to {output_path}")
        except Exception as e:
            messagebox.showerror("Conversion Error", str(e))
    
    def save_config(self):
        try:
            with open('config.yaml', 'w') as f:
                f.write("# Image Converter Configuration\n")
                f.write(f"input_format: {os.path.splitext(self.input_path.get())[1][1:] if self.input_path.get() else 'jpg'}\n")
                f.write(f"output_format: {self.output_format.get()}\n")
                f.write(f"resize_width: {self.resize_width.get()}\n")
                f.write(f"resize_height: {self.resize_height.get()}\n")
                f.write(f"maintain_aspect_ratio: {str(self.maintain_aspect.get()).lower()}\n")
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
rotate_degrees: 0
grayscale: false
quality: 85
gif_frame: 0
""")
    root = tk.Tk()
    app = ImageConverterApp(root)
    root.mainloop()
