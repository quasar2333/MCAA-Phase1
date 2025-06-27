import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import threading
import subprocess

import api_manager


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MCAA-Phase1 GUI")
        self.geometry("700x500")

        self.provider_list = tk.Listbox(self)
        self.provider_list.pack(side=tk.LEFT, fill=tk.Y)
        self.provider_list.bind('<<ListboxSelect>>', self.on_select)

        form = tk.Frame(self)
        form.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        tk.Label(form, text="Name").grid(row=0, column=0)
        tk.Label(form, text="Type(openai/google)").grid(row=1, column=0)
        tk.Label(form, text="Model ID").grid(row=2, column=0)
        tk.Label(form, text="API Key").grid(row=3, column=0)

        self.name_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.key_var = tk.StringVar()

        tk.Entry(form, textvariable=self.name_var).grid(row=0, column=1)
        tk.Entry(form, textvariable=self.type_var).grid(row=1, column=1)
        tk.Entry(form, textvariable=self.model_var).grid(row=2, column=1)
        tk.Entry(form, textvariable=self.key_var, show='*').grid(row=3, column=1)

        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10)
        tk.Button(btn_frame, text="Add/Update", command=self.save_provider).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Delete", command=self.delete_provider).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Run", command=self.run_agent).pack(side=tk.LEFT)

        self.log_area = ScrolledText(self)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        self.refresh_list()

    def refresh_list(self):
        self.provider_list.delete(0, tk.END)
        for p in api_manager.load_providers():
            self.provider_list.insert(tk.END, p['name'])

    def on_select(self, event=None):
        if not self.provider_list.curselection():
            return
        idx = self.provider_list.curselection()[0]
        provider = api_manager.load_providers()[idx]
        self.name_var.set(provider['name'])
        self.type_var.set(provider['type'])
        self.model_var.set(provider['model_id'])
        self.key_var.set(provider['api_key'])

    def save_provider(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Name required")
            return
        api_manager.add_or_update_provider(
            name,
            self.type_var.get().strip() or 'openai',
            self.model_var.get().strip(),
            self.key_var.get().strip()
        )
        self.refresh_list()

    def delete_provider(self):
        if not self.provider_list.curselection():
            return
        idx = self.provider_list.curselection()[0]
        name = self.provider_list.get(idx)
        if messagebox.askyesno("Confirm", f"Delete provider '{name}'?"):
            api_manager.delete_provider(name)
            self.refresh_list()

    def run_agent(self):
        if not self.provider_list.curselection():
            messagebox.showerror("Error", "Select a provider to run")
            return
        idx = self.provider_list.curselection()[0]
        provider = self.provider_list.get(idx)
        self.log_area.delete('1.0', tk.END)

        def target():
            process = subprocess.Popen(
                ['python', 'main.py', '--provider', provider],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in process.stdout:
                self.log_area.insert(tk.END, line)
                self.log_area.see(tk.END)
            process.wait()

        threading.Thread(target=target, daemon=True).start()


if __name__ == '__main__':
    app = App()
    app.mainloop()
