# gui_provider_editor.py
import tkinter as tk
from tkinter import ttk, messagebox

class ProviderEditor(tk.Toplevel):
    """A dedicated window for adding/editing API providers."""
    def __init__(self, parent, provider_data=None):
        super().__init__(parent)
        self.transient(parent)
        self.title("API提供者编辑器")
        self.parent = parent
        self.result = None
        self.provider_data = provider_data or {}

        self.name_var = tk.StringVar(value=self.provider_data.get("name", ""))
        self.type_var = tk.StringVar(value=self.provider_data.get("type", "openai"))
        self.api_key_var = tk.StringVar(value=self.provider_data.get("api_key", ""))
        self.base_url_var = tk.StringVar(value=self.provider_data.get("base_url", ""))
        self.models_var = tk.StringVar(value=",".join(self.provider_data.get("models", [])))

        self.create_widgets()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.wait_window(self)

    def create_widgets(self):
        form = ttk.Frame(self, padding="10")
        form.grid(row=0, column=0, sticky=tk.NSEW)

        ttk.Label(form, text="提供者名称:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(form, text="类型:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(form, textvariable=self.type_var, values=["openai", "google"]).grid(row=1, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(form, text="API密钥:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.api_key_var, show="*", width=40).grid(row=2, column=1, sticky=tk.EW, pady=2)

        ttk.Label(form, text="基础URL(可选):").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.base_url_var, width=40).grid(row=3, column=1, sticky=tk.EW, pady=2)

        ttk.Label(form, text="模型列表(逗号分隔):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.models_var, width=40).grid(row=4, column=1, sticky=tk.EW, pady=2)

        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.grid(row=1, column=0, sticky=tk.E)
        ttk.Button(btn_frame, text="保存", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side=tk.LEFT)

    def save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("错误", "必须填写提供者名称。", parent=self)
            return

        self.result = {
            "name": name,
            "type": self.type_var.get(),
            "api_key": self.api_key_var.get().strip(),
            "base_url": self.base_url_var.get().strip(),
            "models": [m.strip() for m in self.models_var.get().split(',') if m.strip()]
        }
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()