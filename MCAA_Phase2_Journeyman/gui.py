# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import threading
import queue
import uuid
import json

from agent_core import Agent
from llm_interface import load_provider_configs, save_provider_configs, get_provider

class ProviderEditor(tk.Toplevel):
    """A dedicated window for adding/editing API providers."""
    def __init__(self, parent, provider_data=None):
        super().__init__(parent)
        self.transient(parent)
        self.title("Provider Editor")
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

        ttk.Label(form, text="Provider Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(form, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(form, textvariable=self.type_var, values=["openai", "google"]).grid(row=1, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(form, text="API Key:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.api_key_var, show="*", width=40).grid(row=2, column=1, sticky=tk.EW, pady=2)

        ttk.Label(form, text="Base URL (optional):").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.base_url_var, width=40).grid(row=3, column=1, sticky=tk.EW, pady=2)

        ttk.Label(form, text="Models (comma-separated):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.models_var, width=40).grid(row=4, column=1, sticky=tk.EW, pady=2)

        btn_frame = ttk.Frame(self, padding="10")
        btn_frame.grid(row=1, column=0, sticky=tk.E)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT)

    def save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Provider Name is required.", parent=self)
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

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MCAA-Phase2 Journeyman")
        self.geometry("1200x800")
        self.tasks = {}
        self.log_queue = queue.Queue()
        self._init_ui()
        self.refresh_provider_list()
        self.process_log_queue()

    def _init_ui(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)
        left_pane = ttk.Frame(main_pane, width=350)
        main_pane.add(left_pane, weight=1)
        right_pane = ttk.Frame(main_pane)
        main_pane.add(right_pane, weight=3)
        
        self._create_provider_frame(left_pane)
        self._create_task_frame(left_pane)
        
        log_frame = ttk.LabelFrame(right_pane, text="Task Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def _create_provider_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="API Providers")
        frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        
        self.provider_listbox = tk.Listbox(frame, exportselection=False)
        self.provider_listbox.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5)
        ttk.Button(btn_frame, text="Add", command=self.add_provider).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Edit", command=self.edit_provider).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Delete", command=self.delete_provider).pack(side=tk.LEFT, expand=True, fill=tk.X)

    def _create_task_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Tasks")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(frame, text="New Task", command=self.new_task).pack(fill=tk.X, padx=5, pady=5)
        
        self.task_tree = ttk.Treeview(frame, columns=("Status",), show="tree headings")
        self.task_tree.heading("#0", text="Task")
        self.task_tree.heading("Status", text="Status")
        self.task_tree.column("#0", width=200, anchor=tk.W)
        self.task_tree.column("Status", width=80, anchor=tk.CENTER)
        
        self.task_tree.tag_configure("Running", foreground="orange")
        self.task_tree.tag_configure("Completed", foreground="green")
        self.task_tree.tag_configure("Failed", foreground="red")
        
        self.task_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_select)

    def refresh_provider_list(self):
        selected_index = self.provider_listbox.curselection()
        self.provider_listbox.delete(0, tk.END)
        for p in load_provider_configs():
            self.provider_listbox.insert(tk.END, p['name'])
        if selected_index:
            self.provider_listbox.selection_set(selected_index[0])

    def add_provider(self):
        editor = ProviderEditor(self)
        if editor.result:
            configs = load_provider_configs()
            configs.append(editor.result)
            save_provider_configs(configs)
            self.refresh_provider_list()

    def edit_provider(self):
        selections = self.provider_listbox.curselection()
        if not selections: return
        
        configs = load_provider_configs()
        provider_name = self.provider_listbox.get(selections[0])
        provider_data = next((p for p in configs if p['name'] == provider_name), None)

        if provider_data:
            editor = ProviderEditor(self, provider_data)
            if editor.result:
                # Update the config
                for i, p in enumerate(configs):
                    if p['name'] == provider_name:
                        configs[i] = editor.result
                        break
                save_provider_configs(configs)
                self.refresh_provider_list()

    def delete_provider(self):
        selections = self.provider_listbox.curselection()
        if not selections: return

        provider_name = self.provider_listbox.get(selections[0])
        if messagebox.askyesno("Confirm Deletion", f"Delete provider '{provider_name}'?"):
            configs = load_provider_configs()
            save_provider_configs([p for p in configs if p['name'] != provider_name])
            self.refresh_provider_list()

    def new_task(self):
        selections = self.provider_listbox.curselection()
        if not selections:
            messagebox.showerror("Error", "Please select an API provider first.")
            return
        
        provider_name = self.provider_listbox.get(selections[0])
        goal = simpledialog.askstring("New Task", "Enter the task goal:", parent=self)
        if not goal: return

        verify = messagebox.askyesno("Self-Verification", "Enable self-verification mode for this task?", parent=self)

        llm_provider = get_provider(provider_name)
        if not llm_provider:
            messagebox.showerror("Error", f"Failed to load provider '{provider_name}'.")
            return

        # Use LLM to summarize the goal into a short title
        try:
            title = llm_provider.ask("Summarize the following user goal into a short title of 3-5 words.", goal)
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not summarize goal: {e}. Using full goal as title.")
            title = goal[:50] + '...' if len(goal) > 50 else goal

        task_id = str(uuid.uuid4())
        task = {
            "id": task_id, "title": title, "goal": goal, "provider": llm_provider,
            "verify": verify, "status": "Pending", "log": [], "thread": None
        }
        self.tasks[task_id] = task
        
        self.task_tree.insert("", tk.END, text=title, values=("Pending",), iid=task_id)
        self.start_task(task_id)

    def start_task(self, task_id):
        task = self.tasks[task_id]
        if task['status'] == "Running": return

        self.update_task_status(task_id, "Running")
        
        def thread_logger(message: str):
            self.log_queue.put({"task_id": task_id, "message": message})
        
        agent = Agent(goal=task['goal'], llm_provider=task['provider'], log_func=thread_logger, verify=task['verify'])

        def agent_runner():
            success = agent.run()
            self.update_task_status(task_id, "Completed" if success else "Failed")
        
        task['thread'] = threading.Thread(target=agent_runner, daemon=True)
        task['thread'].start()

    def update_task_status(self, task_id, status):
        def _update():
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = status
                self.task_tree.item(task_id, values=(status,), tags=(status,))
        self.after(0, _update)

    def on_task_select(self, event=None):
        selections = self.task_tree.selection()
        if not selections: return
        
        task = self.tasks.get(selections[0])
        if task: self.display_log_for_task(task)

    def process_log_queue(self):
        try:
            while True:
                log_item = self.log_queue.get_nowait()
                task_id, message = log_item["task_id"], log_item["message"]
                
                if task_id in self.tasks:
                    self.tasks[task_id]['log'].append(message)
                
                selections = self.task_tree.selection()
                if selections and selections[0] == task_id:
                    self.append_log_message(message)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_log_queue)

    def display_log_for_task(self, task):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        for msg in task['log']:
            self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def append_log_message(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = App()
    app.mainloop()
