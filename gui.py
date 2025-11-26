import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import config
import data_processor
import os

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Growth Automation Tool v2.0")
        self.root.geometry("420x280")
        self.root.resizable(False, False)
        
        try:
            self.root.iconbitmap("folder_icon.ico")
        except tk.TclError:
            pass

        # Title
        self.label = tk.Label(root, text="Campaign Data Processor", font=("Arial", 14, "bold"))
        self.label.pack(pady=15)

        # Dropdown for Mode Selection
        self.mode_label = tk.Label(root, text="Select Operation Mode:", font=("Arial", 10))
        self.mode_label.pack(pady=(5, 5))

        self.modes = {
            "Enrich EB with Clay (Standard)": "enrich",
            "Clean Clay List (Remove DNC)": "dnc"
        }
        
        self.mode_var = tk.StringVar()
        self.mode_combo = ttk.Combobox(root, textvariable=self.mode_var, state="readonly", width=35)
        self.mode_combo['values'] = list(self.modes.keys())
        self.mode_combo.current(0) # Default to first option
        self.mode_combo.pack(pady=5)

        # Run Button
        self.process_button = tk.Button(root, text="Select Campaign Folder & Run", font=("Arial", 11), command=self.start_processing, bg="#0078D7", fg="white", height=2)
        self.process_button.pack(pady=25, padx=20, fill='x')

    def start_processing(self):
        # Get selected mode
        selected_text = self.mode_var.get()
        mode_key = self.modes[selected_text]

        campaign_path = filedialog.askdirectory(
            initialdir=config.DEFAULT_PATH,
            title="Select Campaign Folder"
        )
        if not campaign_path:
            return

        self.process_button.config(state="disabled", text="Processing... Please wait")
        self.root.update()

        try:
            result_message = ""
            if mode_key == "enrich":
                result_message = data_processor.run_enrichment_eb(campaign_path)
            elif mode_key == "dnc":
                result_message = data_processor.run_dnc_suppression(campaign_path)
            
            messagebox.showinfo("Done", result_message)
            
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
        finally:
            self.process_button.config(state="normal", text="Select Campaign Folder & Run")