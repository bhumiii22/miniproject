import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import sys
import os
import webbrowser

class QuizAppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Application Launcher")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", padding=6, relief="flat", background="#0d6efd")
        self.style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 11))
        self.style.configure("Header.TLabel", font=("Helvetica", 18, "bold"))
        
        # Main frame
        self.main_frame = ttk.Frame(root, padding="20 20 20 20", style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = ttk.Label(self.main_frame, text="Student-Teacher Quiz Application", style="Header.TLabel")
        header_label.pack(pady=(0, 20))
        
        # Description
        desc_text = "This application allows teachers to create quizzes and students to take them.\n"
        desc_text += "Teachers can upload quizzes from Excel and view student results.\n"
        desc_text += "Students can take quizzes with a timer and see their scores."
        desc_label = ttk.Label(self.main_frame, text=desc_text, wraplength=500, justify="center")
        desc_label.pack(pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.main_frame, style="TFrame")
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Start server button
        self.start_button = ttk.Button(buttons_frame, text="Start Django Server", command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Open browser button
        self.browser_button = ttk.Button(buttons_frame, text="Open in Browser", command=self.open_browser)
        self.browser_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Stop server button
        self.stop_button = ttk.Button(buttons_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Status frame
        status_frame = ttk.Frame(self.main_frame, style="TFrame")
        status_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Status label
        self.status_label = ttk.Label(status_frame, text="Server Status: Not Running", foreground="red")
        self.status_label.pack(side=tk.LEFT)
        
        # Console output
        console_label = ttk.Label(self.main_frame, text="Server Console:")
        console_label.pack(anchor=tk.W, pady=(20, 5))
        
        self.console = tk.Text(self.main_frame, height=8, width=70, bg="#f8f9fa", fg="#212529")
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.config(state=tk.DISABLED)
        
        # Add scrollbar to console
        scrollbar = ttk.Scrollbar(self.console, command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scrollbar.set)
        
        # Server process
        self.process = None
        
    def start_server(self):
        if self.process is None:
            try:
                # Update UI
                self.update_console("Starting Django server...\n")
                self.status_label.config(text="Server Status: Starting...", foreground="orange")
                self.root.update()
                
                # Start Django server
                cmd = [sys.executable, "manage.py", "runserver"]
                self.process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Update buttons
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                
                # Start reading output
                self.root.after(100, self.read_output)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start server: {str(e)}")
                self.status_label.config(text="Server Status: Error", foreground="red")
    
    def read_output(self):
        if self.process:
            # Read a line from the process output
            line = self.process.stdout.readline()
            if line:
                self.update_console(line)
                
                # Check if server is running
                if "Starting development server at" in line:
                    self.status_label.config(text="Server Status: Running", foreground="green")
                
                # Schedule next read
                self.root.after(100, self.read_output)
            else:
                # Check if process has terminated
                if self.process.poll() is not None:
                    self.update_console("Server stopped.\n")
                    self.status_label.config(text="Server Status: Stopped", foreground="red")
                    self.process = None
                    self.start_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                else:
                    # No output but process still running
                    self.root.after(100, self.read_output)
    
    def stop_server(self):
        if self.process:
            self.update_console("Stopping server...\n")
            self.process.terminate()
            self.process = None
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Server Status: Stopped", foreground="red")
    
    def open_browser(self):
        webbrowser.open("http://127.0.0.1:8000")
    
    def update_console(self, text):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, text)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizAppLauncher(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_server(), root.destroy()))
    root.mainloop()