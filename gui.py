import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import threading

import api_manager
from main import run_agent


class Task:
    def __init__(self, goal: str, provider: str, model: str):
        self.goal = goal
        self.provider = provider
        self.model = model
        self.log_text = ""
        self.thread: threading.Thread | None = None
        self.running = False

    def append_log(self, msg: str):
        self.log_text += msg + "\n"

    def run(self):
        self.running = True
        run_agent(self.goal, self.provider, self.model, self.append_log)
        self.running = False


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MCAA-Phase1")
        self.geometry("900x600")

        self.tasks: list[Task] = []
        self.current_task: Task | None = None

        self.create_provider_frame()
        self.create_task_frame()

        self.refresh_providers()

    # ---------- Provider management ----------
    def create_provider_frame(self):
        frame = tk.LabelFrame(self, text="Providers")
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.provider_list = tk.Listbox(frame, width=20)
        self.provider_list.pack(fill=tk.Y)
        self.provider_list.bind('<<ListboxSelect>>', self.on_provider_select)

        form = tk.Frame(frame)
        form.pack(pady=5)
        tk.Label(form, text="Name").grid(row=0, column=0)
        tk.Label(form, text="Type").grid(row=1, column=0)
        tk.Label(form, text="Base URL").grid(row=2, column=0)
        tk.Label(form, text="Models(comma)").grid(row=3, column=0)
        tk.Label(form, text="API Key").grid(row=4, column=0)

        self.name_var = tk.StringVar()
        self.type_var = tk.StringVar(value="openai")
        self.base_var = tk.StringVar()
        self.models_var = tk.StringVar()
        self.key_var = tk.StringVar()

        tk.Entry(form, textvariable=self.name_var).grid(row=0, column=1)
        tk.Entry(form, textvariable=self.type_var).grid(row=1, column=1)
        tk.Entry(form, textvariable=self.base_var).grid(row=2, column=1)
        tk.Entry(form, textvariable=self.models_var).grid(row=3, column=1)
        tk.Entry(form, textvariable=self.key_var, show='*').grid(row=4, column=1)

        btns = tk.Frame(frame)
        btns.pack(pady=5)
        tk.Button(btns, text="Add/Update", command=self.save_provider).pack(side=tk.LEFT)
        tk.Button(btns, text="Delete", command=self.delete_provider).pack(side=tk.LEFT)

    def refresh_providers(self):
        self.provider_list.delete(0, tk.END)
        for p in api_manager.load_providers():
            self.provider_list.insert(tk.END, p['name'])

    def on_provider_select(self, event=None):
        if not self.provider_list.curselection():
            return
        idx = self.provider_list.curselection()[0]
        provider = api_manager.load_providers()[idx]
        self.name_var.set(provider['name'])
        self.type_var.set(provider['type'])
        self.base_var.set(provider.get('base_url', ''))
        self.models_var.set(','.join(provider.get('models', [])))
        self.key_var.set(provider.get('api_key', ''))

    def save_provider(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Name required")
            return
        api_manager.add_or_update_provider(
            name,
            self.type_var.get().strip() or 'openai',
            self.base_var.get().strip(),
            self.key_var.get().strip(),
            [m.strip() for m in self.models_var.get().split(',') if m.strip()]
        )
        self.refresh_providers()

    def delete_provider(self):
        if not self.provider_list.curselection():
            return
        idx = self.provider_list.curselection()[0]
        name = self.provider_list.get(idx)
        if messagebox.askyesno("Confirm", f"Delete provider '{name}'?"):
            api_manager.delete_provider(name)
            self.refresh_providers()

    # ---------- Task management ----------
    def create_task_frame(self):
        frame = tk.LabelFrame(self, text="Tasks")
        frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        top = tk.Frame(frame)
        top.pack(side=tk.TOP, fill=tk.X)
        tk.Button(top, text="New Task", command=self.new_task).pack(side=tk.LEFT)
        tk.Button(top, text="Start", command=self.start_task).pack(side=tk.LEFT)

        self.task_list = tk.Listbox(frame)
        self.task_list.pack(side=tk.LEFT, fill=tk.Y)
        self.task_list.bind('<<ListboxSelect>>', self.on_task_select)

        self.log_area = ScrolledText(frame)
        self.log_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def new_task(self):
        goal = simpledialog.askstring("Goal", "任务目标:")
        if not goal:
            return
        if not self.provider_list.curselection():
            messagebox.showerror("Error", "请选择一个提供商")
            return
        p_idx = self.provider_list.curselection()[0]
        provider = self.provider_list.get(p_idx)
        models = api_manager.get_provider(provider).get('models', [])
        model = models[0] if models else ''
        task = Task(goal, provider, model)
        self.tasks.append(task)
        self.task_list.insert(tk.END, goal)

    def on_task_select(self, event=None):
        idxs = self.task_list.curselection()
        if not idxs:
            return
        task = self.tasks[idxs[0]]
        self.current_task = task
        self.log_area.delete('1.0', tk.END)
        self.log_area.insert(tk.END, task.log_text)

    def start_task(self):
        idxs = self.task_list.curselection()
        if not idxs:
            messagebox.showerror("Error", "选择任务")
            return
        task = self.tasks[idxs[0]]
        if task.running:
            messagebox.showinfo("Info", "任务已在运行")
            return

        def runner():
            task.run()
            self.log_area.insert(tk.END, "\n[任务结束]\n")
        task.thread = threading.Thread(target=runner, daemon=True)
        task.thread.start()

        self.after(100, self.refresh_log)

    def refresh_log(self):
        if self.current_task and self.current_task.running:
            self.log_area.delete('1.0', tk.END)
            self.log_area.insert(tk.END, self.current_task.log_text)
            self.after(500, self.refresh_log)
        elif self.current_task:
            self.log_area.delete('1.0', tk.END)
            self.log_area.insert(tk.END, self.current_task.log_text)


if __name__ == '__main__':
    app = App()
    app.mainloop()
