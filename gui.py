import tkinter as tk
from tkinter import filedialog, messagebox
import config
import data_processor

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Enrichment Tool v1.0")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Установка иконки
        try:
            self.root.iconbitmap("folder_icon.ico")
        except tk.TclError:
            print("Иконка 'folder_icon.ico' не найдена. Убедитесь, что она в той же папке.")

        self.label = tk.Label(root, text="Инструмент для обогащения данных Clay/EB", font=("Arial", 12))
        self.label.pack(pady=20)
        
        self.process_button = tk.Button(root, text="Выбрать папку кампании и запустить", font=("Arial", 12, "bold"), command=self.start_processing, bg="#4CAF50", fg="white")
        self.process_button.pack(pady=20, padx=20, ipadx=10, ipady=10)

    def start_processing(self):
        campaign_path = filedialog.askdirectory(
            initialdir=config.DEFAULT_PATH,
            title="Выберите папку кампании для обработки"
        )
        if not campaign_path:
            messagebox.showwarning("Отмена", "Операция отменена. Папка не была выбрана.")
            return

        self.process_button.config(state="disabled", text="Идет обработка...")
        self.root.update()

        try:
            result_message = data_processor.run_processing(campaign_path)
            messagebox.showinfo("Готово!", result_message)
        except Exception as e:
            messagebox.showerror("Критическая ошибка!", f"Произошла непредвиденная ошибка:\n{e}")
        finally:
            self.process_button.config(state="normal", text="Выбрать папку кампании и запустить")