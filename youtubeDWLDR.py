import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import os
import sys
import subprocess
import time

def ensure_yt_dlp():
    try:
        import yt_dlp
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'yt-dlp'])

class DownloadManager:
    def __init__(self):
        self.process = None
        self.is_paused = False
        self.is_stopped = False
        self.progress = 0

    def download_video(self, url, folder, progress_callback, status_callback):
        try:
            status_callback("Downloading...")
            # Output template to save file in folder
            command = [
                sys.executable, '-m', 'yt_dlp',
                '--no-playlist',
                '--progress',
                '-o', os.path.join(folder, '%(title)s.%(ext)s'),
                url
            ]
            self.is_paused = False
            self.is_stopped = False

            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in self.process.stdout:
                if self.is_stopped:
                    self.process.terminate()
                    status_callback("Download stopped.")
                    progress_callback(0)
                    return
                while self.is_paused:
                    status_callback("Download paused.")
                    time.sleep(0.5)
                # Parse progress (yt-dlp outputs percentage as "XX.XX%")
                if '%' in line:
                    try:
                        percent = line.split('%')[0].split()[-1]
                        percent_float = float(percent)
                        progress_callback(percent_float)
                    except Exception:
                        pass
                status_callback(line.strip())
            self.process.wait()
            if self.process.returncode == 0 and not self.is_stopped:
                status_callback("Download completed!")
                progress_callback(100)
            elif not self.is_stopped:
                status_callback("Error during download.")
                messagebox.showerror("Error", "An error occurred during download.")
        except Exception as e:
            status_callback("Error during download.")
            messagebox.showerror("Error", str(e))
        finally:
            self.process = None

    def stop(self):
        self.is_stopped = True
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

download_manager = DownloadManager()

def start_download_thread():
    url = url_entry.get()
    folder = folder_var.get()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube video URL.")
        return
    if not folder:
        messagebox.showerror("Error", "Please select a download folder.")
        return

    progress_bar['value'] = 0
    enable_buttons(downloading=True)
    threading.Thread(target=download_manager.download_video, args=(
        url,
        folder,
        update_progress,
        update_status,
    ), daemon=True).start()

def update_progress(value):
    progress_bar['value'] = value
    root.update_idletasks()

def update_status(text):
    status_var.set(text)
    root.update_idletasks()

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def stop_download():
    download_manager.stop()
    enable_buttons(downloading=False)

def pause_download():
    download_manager.pause()
    status_var.set("Download paused.")
    enable_buttons(paused=True)

def resume_download():
    download_manager.resume()
    status_var.set("Resuming download...")
    enable_buttons(downloading=True)

def enable_buttons(downloading=False, paused=False):
    if downloading:
        download_btn.config(state="disabled")
        stop_btn.config(state="normal")
        cancel_btn.config(state="normal")
        pause_btn.config(state="normal")
        resume_btn.config(state="disabled")
    elif paused:
        download_btn.config(state="disabled")
        stop_btn.config(state="normal")
        cancel_btn.config(state="normal")
        pause_btn.config(state="disabled")
        resume_btn.config(state="normal")
    else:
        download_btn.config(state="normal")
        stop_btn.config(state="disabled")
        cancel_btn.config(state="disabled")
        pause_btn.config(state="disabled")
        resume_btn.config(state="disabled")

ensure_yt_dlp()

root = tk.Tk()
root.title("YouTube Video Downloader (yt-dlp)")
root.geometry("470x320")
root.resizable(False, False)

tk.Label(root, text="YouTube Video URL:").pack(pady=(15, 5))
url_entry = tk.Entry(root, width=55)
url_entry.pack(pady=5)

folder_var = tk.StringVar()
tk.Label(root, text="Download Folder:").pack(pady=(10, 5))
folder_frame = tk.Frame(root)
folder_frame.pack()
tk.Entry(folder_frame, textvariable=folder_var, width=40, state="readonly").pack(side=tk.LEFT)
tk.Button(folder_frame, text="Browse", command=choose_folder).pack(side=tk.LEFT, padx=5)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=(18, 5))

status_var = tk.StringVar()
status_label = tk.Label(root, textvariable=status_var, fg="blue")
status_label.pack(pady=(10, 5))

button_frame = tk.Frame(root)
button_frame.pack(pady=10)

download_btn = tk.Button(button_frame, text="Download", command=start_download_thread, width=15)
download_btn.grid(row=0, column=0, padx=4)

pause_btn = tk.Button(button_frame, text="Pause", command=pause_download, width=15, state="disabled")
pause_btn.grid(row=0, column=1, padx=4)

resume_btn = tk.Button(button_frame, text="Resume", command=resume_download, width=15, state="disabled")
resume_btn.grid(row=0, column=2, padx=4)

stop_btn = tk.Button(button_frame, text="Stop", command=stop_download, width=15, state="disabled")
stop_btn.grid(row=1, column=0, padx=4, pady=5)

cancel_btn = tk.Button(button_frame, text="Cancel", command=stop_download, width=15, state="disabled")
cancel_btn.grid(row=1, column=1, padx=4, pady=5)

enable_buttons(downloading=False)

def on_close():
    download_manager.stop()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

if __name__ == "__main__":
    root.mainloop()