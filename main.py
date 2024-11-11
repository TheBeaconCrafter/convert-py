import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import os
import threading
import yt_dlp as ytdlp
import re
import sys

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DARK_GRAY = "#2b2b2b"
TEXT_COLOR = "#ffffff"

# Supported formats for conversion by category
SUPPORTED_FORMATS = {
    "image": ["png", "jpeg", "jpg", "bmp", "gif", "tiff", "webp", "heif", "ico"],
    "audio": ["mp3", "wav", "ogg", "flac", "aac", "m4a", "opus"],
    "video": ["mp4", "avi", "mov", "webm", "flv", "mkv", "wmv"],
    "document": ["docx", "pdf"]
}

def clean_path(path):
    """Clean the file path by removing curly braces and handling spaces."""
    return path.strip('{}').strip('"').strip("'")

def detect_file_category(file_extension):
    """Return the category of the file based on its extension."""
    file_extension = file_extension.lower()
    for category, extensions in SUPPORTED_FORMATS.items():
        if file_extension in extensions:
            return category
    return None

def compress_image(input_path, output_path, quality):
    """Compress image files with the specified quality."""
    try:
        with Image.open(input_path) as img:
            img.save(output_path, quality=quality, optimize=True)
    except Exception as e:
        raise ValueError(f"Error compressing image: {str(e)}")

def compress_video(input_path, output_path, quality):
    """Compress video files by adjusting the bitrate."""
    try:
        clip = VideoFileClip(input_path)
        clip.write_videofile(output_path, codec="h264_nvenc", bitrate=f"{quality}k")
    except Exception as e:
        raise ValueError(f"Error compressing video: {str(e)}")

def compress_file(input_path, output_path, category, quality):
    """Compress the file based on category (image/video)."""
    try:
        if category == "image":
            compress_image(input_path, output_path, quality)
        elif category == "video":
            compress_video(input_path, output_path, quality)
        else:
            raise ValueError("Unsupported compression category.")
    except Exception as e:
        raise ValueError(f"Error during compression: {str(e)}")

def convert_image(input_path, output_path, output_format):
    """Convert image files to the specified format."""
    try:
        with Image.open(input_path) as img:
            img.convert("RGB").save(output_path, format=output_format.upper())
    except Exception as e:
        raise ValueError(f"Error converting image: {str(e)}")

def convert_audio(input_path, output_path, output_format):
    """Convert audio files to the specified format."""
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format=output_format)
    except Exception as e:
        raise ValueError(f"Error converting audio: {str(e)}")

def convert_video(input_path, output_path, output_format):
    """Convert video files to the specified format."""
    try:
        clip = VideoFileClip(input_path)
        clip.write_videofile(output_path, codec="h264_nvenc")
    except Exception as e:
        raise ValueError(f"Error converting video: {str(e)}")

def convert_file(input_path, output_path, category, output_format):
    """Convert the file based on category (image/audio/video)."""
    try:
        if category == "image":
            convert_image(input_path, output_path, output_format)
        elif category == "audio":
            convert_audio(input_path, output_path, output_format)
        elif category == "video":
            convert_video(input_path, output_path, output_format)
        else:
            raise ValueError("Unsupported conversion category.")
    except Exception as e:
        raise ValueError(f"Error during conversion: {str(e)}")

class FileConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TurboConvert")
        self.geometry("500x500")
        
        # Determine the correct path for the icon depending on whether the app is frozen or not
        if getattr(sys, 'frozen', False):
            # If running as a packaged app
            icon_path = os.path.join(sys._MEIPASS, 'resources', 'icon.ico')
        else:
            # If running as a script (for development)
            icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')

        try:
            self.iconbitmap(icon_path)
            print("Icon set successfully!")
        except Exception as e:
            print(f"Error setting icon: {e}")
        
        self.configure(bg=DARK_GRAY)
        self.main_frame = ctk.CTkFrame(self, fg_color=DARK_GRAY)
        self.main_frame.pack(fill="both", expand=True)

        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(pady=20, padx=20)

        # Conversion Tab
        self.tab_conversion = self.tab_view.add("Conversion")
        self.create_conversion_tab()

        # Compression Tab
        self.tab_compression = self.tab_view.add("Compression")
        self.create_compression_tab()
        
        # Toolbox Tab
        self.tab_toolbox = self.tab_view.add("YouTube")
        self.create_toolbox_tab()


        # Enable drag-and-drop (module breaks pyinstaller so disabled for now)
        #self.drop_target_register(DND_FILES)
        #self.dnd_bind('<<Drop>>', self.on_file_drop)
        
    
    def create_toolbox_tab(self):
        """Create the UI for the toolbox tab with YouTube downloader."""
        self.label_toolbox = ctk.CTkLabel(
            self.tab_toolbox,
            text="Download YouTube Video (WEBM/MP4/MP3)",
            font=("Arial", 18),
            text_color=TEXT_COLOR
        )
        self.label_toolbox.pack(pady=20)

        self.url_entry = ctk.CTkEntry(
            self.tab_toolbox,
            width=400,
            fg_color=DARK_GRAY,
            text_color=TEXT_COLOR,
            placeholder_text="Enter YouTube URL"
        )
        self.url_entry.pack(pady=10)

        self.download_button = ctk.CTkButton(
            self.tab_toolbox,
            text="Download",
            command=self.download_video,
            fg_color="#3b3b3b",
            hover_color="#4b4b4b"
        )
        self.download_button.pack(pady=10)

        self.progress_bar_toolbox = ctk.CTkProgressBar(
            self.tab_toolbox,
            width=400,
            height=20,
            fg_color="#3b3b3b",
            progress_color="#4b4b4b"
        )
        self.progress_bar_toolbox.pack(pady=10)

        self.format_tabs = ctk.CTkTabview(self.tab_toolbox)
        self.format_tabs.pack(pady=10)
        self.format_tabs.add("WEBM")
        self.format_tabs.add("MP4")
        self.format_tabs.add("MP3")
        self.format_tabs.set("WEBM")  # Default to WEBM

    def create_conversion_tab(self):
        """Create the UI for the conversion tab."""
        self.label_conversion = ctk.CTkLabel(
            self.tab_conversion,
            text="Drop a file or select to convert",
            font=("Arial", 18),
            text_color=TEXT_COLOR
        )
        self.label_conversion.pack(pady=20)

        self.file_entry_conversion = ctk.CTkEntry(
            self.tab_conversion,
            width=400,
            fg_color=DARK_GRAY,
            text_color=TEXT_COLOR
        )
        self.file_entry_conversion.pack(pady=10)

        self.browse_button_conversion = ctk.CTkButton(
            self.tab_conversion,
            text="Browse",
            command=self.browse_file_conversion,
            fg_color="#3b3b3b",
            hover_color="#4b4b4b"
        )
        self.browse_button_conversion.pack(pady=5)

        self.format_label_conversion = ctk.CTkLabel(
            self.tab_conversion,
            text="Select Output Format:",
            text_color=TEXT_COLOR
        )
        self.format_label_conversion.pack(pady=5)
        
        self.format_var_conversion = ctk.StringVar(value="Select Format")
        self.format_menu_conversion = ctk.CTkOptionMenu(
            self.tab_conversion,
            variable=self.format_var_conversion,
            values=[],
            fg_color="#3b3b3b",
            button_color="#4b4b4b",
            button_hover_color="#5b5b5b"
        )
        self.format_menu_conversion.pack(pady=5)

        self.convert_button = ctk.CTkButton(
            self.tab_conversion,
            text="Convert",
            command=self.convert,
            fg_color="#3b3b3b",
            hover_color="#4b4b4b"
        )
        self.convert_button.pack(pady=20)

        self.progress_bar_conversion = ctk.CTkProgressBar(
            self.tab_conversion,
            width=400,
            height=20,
            fg_color="#3b3b3b",
            progress_color="#4b4b4b"
        )
        self.progress_bar_conversion.pack(pady=20)
        self.progress_bar_conversion.set(0)

    def create_compression_tab(self):
        """Create the UI for the compression tab."""
        self.label_compression = ctk.CTkLabel(
            self.tab_compression,
            text="Drop a file or select to compress",
            font=("Arial", 18),
            text_color=TEXT_COLOR
        )
        self.label_compression.pack(pady=20)

        self.file_entry_compression = ctk.CTkEntry(
            self.tab_compression,
            width=400,
            fg_color=DARK_GRAY,
            text_color=TEXT_COLOR
        )
        self.file_entry_compression.pack(pady=10)

        self.browse_button_compression = ctk.CTkButton(
            self.tab_compression,
            text="Browse",
            command=self.browse_file_compression,
            fg_color="#3b3b3b",
            hover_color="#4b4b4b"
        )
        self.browse_button_compression.pack(pady=5)

        self.quality_label = ctk.CTkLabel(
            self.tab_compression,
            text="Select Compression Quality (1-100):",
            text_color=TEXT_COLOR
        )
        self.quality_label.pack(pady=5)
        
        self.quality_slider = ctk.CTkSlider(
            self.tab_compression,
            from_=1,
            to=100,
            number_of_steps=100,
            command=self.update_quality_label
        )
        self.quality_slider.set(75)  # Default quality
        self.quality_slider.pack(pady=10)

        self.compress_button = ctk.CTkButton(
            self.tab_compression,
            text="Compress",
            command=self.compress,
            fg_color="#3b3b3b",
            hover_color="#4b4b4b"
        )
        self.compress_button.pack(pady=20)

        self.progress_bar_compression = ctk.CTkProgressBar(
        self.tab_compression,
        width=400,
        height=20,
        fg_color="#3b3b3b",
        progress_color="blue"
        )
        self.progress_bar_compression.pack(pady=20)
        self.progress_bar_compression.set(0)


    def browse_file_conversion(self):
        """Open file dialog to select a file for conversion."""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry_conversion.delete(0, tk.END)
            self.file_entry_conversion.insert(0, clean_path(file_path))
            self.update_format_options(file_path, "conversion")

    def browse_file_compression(self):
        """Open file dialog to select a file for compression."""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry_compression.delete(0, tk.END)
            self.file_entry_compression.insert(0, clean_path(file_path))
            self.update_format_options(file_path, "compression")

    def update_format_options(self, file_path, tab):
        """Update format options based on the file selected."""
        try:
            file_extension = os.path.splitext(file_path)[1][1:].lower()
            category = detect_file_category(file_extension)

            if category:
                if tab == "conversion":
                    formats = SUPPORTED_FORMATS[category]
                    self.format_menu_conversion.configure(values=formats)
                elif tab == "compression":
                    self.category_compression = category
            else:
                messagebox.showerror("Error", "Unsupported file type.")
        except Exception as e:
            messagebox.showerror("Error", f"Error updating format options: {e}")
            
    def convert_to_mp4(self, input_file):
        """Convert downloaded WEBM file to MP4 using moviepy."""
        output_file = input_file.replace('.webm', '.mp4')
        
        try:
            clip = VideoFileClip(input_file)
            clip.write_videofile(output_file, codec="h264_nvenc")  # Save as MP4 with H.264 codec
            clip.close()
            print(f"Converted to MP4: {output_file}")
            self.progress_bar_toolbox.set(0.5)
        except Exception as e:
            print(f"Error converting to MP4: {e}")

    def convert_to_mp3(self, file_path, output_dir):
        """Convert downloaded video to MP3 format."""
        mp3_path = os.path.join(output_dir, os.path.splitext(os.path.basename(file_path))[0] + ".mp3")
        try:
            audio = AudioSegment.from_file(file_path)
            audio.export(mp3_path, format="mp3")
        except Exception as e:
            messagebox.showerror("Conversion Error", f"Error converting to MP3: {str(e)}")

    def update_progress(self, status):
        # Clean the string of escape sequences
        progress_str = status["_percent_str"].strip("%")
        progress_str_clean = re.sub(r'\x1b\[[0-9;]*m', '', progress_str)  # Remove ANSI escape sequences

        # Add a check for empty or invalid progress string
        if not progress_str_clean:
            print("Empty or invalid progress string")
            return

        try:
            progress = float(progress_str_clean)
            progress_percentage = progress / 100
            print(f"Progress: {progress_percentage * 100}%")
        except ValueError:
            # Handle cases where conversion fails
            print(f"Error parsing progress value: {progress_str_clean}")


    def convert(self):
        """Handle file conversion."""
        filepath = self.file_entry_conversion.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a file to convert.")
            return

        output_format = self.format_var_conversion.get()
        if output_format == "Select Format":
            messagebox.showerror("Error", "Please select a valid output format.")
            return
        
        try:
            output_path = os.path.splitext(filepath)[0] + f"_converted.{output_format.lower()}"
            category = detect_file_category(os.path.splitext(filepath)[1][1:])
            convert_file(filepath, output_path, category, output_format)
            messagebox.showinfo("Success", f"File converted to {output_format}!")
        except Exception as e:
            messagebox.showerror("Error", f"Error during conversion: {e}")

    def compress(self):
        """Handle file compression."""
        filepath = self.file_entry_compression.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a file to compress.")
            return

        quality = int(self.quality_slider.get())
        output_path = os.path.splitext(filepath)[0] + "_compressed" + os.path.splitext(filepath)[1]
        category = self.category_compression

        try:
            self.progress_bar_compression.set(0)
            threading.Thread(target=self._compress_file, args=(filepath, output_path, category, quality)).start()
        except Exception as e:
            messagebox.showerror("Error", f"Error during compression: {e}")

    def _compress_file(self, filepath, output_path, category, quality):
        """Handle compression in a separate thread."""
        try:
            compress_file(filepath, output_path, category, quality)
            self.progress_bar_compression.set(1)
            messagebox.showinfo("Success", f"File compressed successfully: {output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error during compression: {e}")

    def update_quality_label(self, value):
        """Update quality label with the selected value."""
        self.quality_label.configure(text=f"Compression Quality ({int(value)}):")

    def on_file_drop(self, event):
        """Handle file drop event."""
        file_path = event.data
        if file_path:
            self.file_entry_conversion.delete(0, tk.END)
            self.file_entry_conversion.insert(0, clean_path(file_path))
            self.update_format_options(file_path, "conversion")

    def run_download(self, url):
        """Run the download process in a separate thread to keep the GUI responsive."""
        download_path = self.get_download_path()
        if not download_path:
            messagebox.showerror("Error", "Unable to determine the download path.")
            return

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.update_progress],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'merge_output_format': 'mp4',  # Ensure merging to MP4 format
            'postprocessor_args': [
                '-c:v', 'h264_nvenc',  # hardware accelerated h264_nvenc (NVIDIA GPU)
                '-b:v', '5M',
                '-c:a', 'aac',
                '-b:a', '192k' # Audio bitrate
            ]
        }

        try:
            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Success", "Video downloaded and processed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {str(e)}")

    def download_video(self):
        """Download YouTube video in selected format (WEBM, MP3, or MP4 with NVENC GPU acceleration)."""
        url = self.url_entry.get()
        download_format = self.format_tabs.get()  # Retrieve selected format

        def download_thread():
            output_dir = filedialog.askdirectory(title="Select Download Folder")
            if not output_dir:
                return

            options = {
                "outtmpl": os.path.join(output_dir, "%(title)s" + ".%(ext)s"),
                "format": "bestvideo+bestaudio/best" if download_format == "MP4" else "bestaudio" if download_format != "WEBM" else "bestaudio+bestaudio[ext=webm]+bestvideo[ext=webm]",
                "progress_hooks": [self.update_progress],
            }
            with ytdlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

                if download_format == "MP3":  # Convert to MP3 if selected
                    self.convert_to_mp3(file_path, output_dir)
                elif download_format == "MP4":  # Convert to MP4 with NVENC
                    self.convert_to_mp4_with_nvenc(file_path, output_dir)

            self.progress_bar_toolbox.set(0)

        threading.Thread(target=download_thread).start()

    def convert_to_mp4_with_nvenc(self, file_path, output_dir):
        """Convert downloaded video to MP4 using NVENC (GPU acceleration)."""
        try:
            # Get the base file name without extension
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            output_file = os.path.join(output_dir, base_filename + "_gpu.mp4")
            
            # Ensure the file path is properly quoted
            file_path = f'"{file_path}"'
            output_file = f'"{output_file}"'

            ffmpeg_command = [
                'ffmpeg', '-i', file_path, 
                '-c:v', 'h264_nvenc',
                '-preset', 'fast',  # Use a fast encoding preset
                output_file
            ]
            
            os.system(' '.join(ffmpeg_command))
            
            messagebox.showinfo("Success", "MP4 Conversion completed with GPU acceleration.")
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            
    def update_download_format(self):
        """Update the download format based on the selected tab."""
        selected_tab = self.format_tabs.get()
        self.selected_format = selected_tab
        print(f"Selected download format: {self.selected_format}")
    
    def get_download_path(self):
        if os.name == 'nt':  # Windows
            return os.path.join(os.environ['USERPROFILE'], 'Downloads')
        elif os.name == 'posix':  # macOS / Linux
            return os.path.join(os.environ['HOME'], 'Downloads')
        return ''

    def ytdlp_progress_hook(self, d):
        """Progress hook for yt-dlp."""
        if d["status"] == "downloading":
            percent = d.get("percent", 0)
            self.progress_bar_toolbox.set(percent / 100)
        elif d["status"] == "finished":
            self.progress_bar_toolbox.set(1)
            messagebox.showinfo("Download Complete", "Download complete!")

    def progress_hook(self, d):
        """Progress hook to update download progress."""
        if d['status'] == 'downloading':
            progress = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1)
            self.progress_bar_toolbox.set(progress)

if __name__ == "__main__":
    app = FileConverterApp()
    app.mainloop()
