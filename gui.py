# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import threading
import queue
import json
import uuid

from agent_core import Agent
from llm_interface import load_provider_configs, save_provider_configs, get_provider

class ThreadSafeLogger:
    """A logger that safely sends messages from a worker thread to the GUI."""
    def __init__(self, log_queue: queue.Queue):
        self.queue = log_queue

    def __call__(self, message: str):
        self.queue.put(message)

class ThreadSafeInput:
    """A mechanism to get user input from the GUI for a worker thread."""
    def __init__(self, root: tk.Tk, title: str):
        self.root = root
        self.title = title
        self.input_queue = queue.Queue(maxsize=1)
        self.response_queue = queue.Queue(maxsize=1)

    def __call__(self, prompt: str) -> str:
        # Signal the GUI to ask for input
        self.input_queue.put(prompt)
        # Wait for the GUI to provide the input
        return self.response_queue.get()

    def check_for_input_request(self):
        try:
            prompt = self.input_queue.get_nowait()
            # This runs in the GUI thread
            response = simpledialog.askstring(self.title, prompt, parent=self.root)
            self.response_queue.put(response or "")
        except queue.Empty:
            pass # No input request

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MCAA-Phase1 Agent")
        self.geometry("1200x800")

        self.tasks = {} # Using a dictionary {task_id: task_instance}
        self.log_queue = queue.Queue()
        self.input_handler = ThreadSafeInput(self, "Agent Input Required")

        self._init_ui()
        self.refresh_provider_list()
        self.process_log_queue()

    def _init_ui(self):
        # Main layout with PanedWindow
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_pane = ttk.Frame(main_pane, width=350)
        main_pane.add(left_pane, weight=1)

        right_pane = ttk.Frame(main_pane)
        main_pane.add(right_pane, weight=3)
        
        # --- Left Pane: Providers and Tasks ---
        self._create_provider_frame(left_pane)
        self._create_task_frame(left_pane)
        
        # --- Right Pane: Logs ---
        log_frame = ttk.LabelFrame(right_pane, text="Task Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def _create_provider_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="API Providers")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.provider_listbox = tk.Listbox(frame, exportselection=False)
        self.provider_listbox.pack(fill=tk.X, padx=5, pady=5)
        self.provider_listbox.bind("<<ListboxSelect>>", self.on_provider_select)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Add/Edit", command=self.add_edit_provider).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Delete", command=self.delete_provider).pack(side=tk.LEFT, expand=True, fill=tk.X)

    def _create_task_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Tasks")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="New Task", command=self.new_task).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Task List (Treeview for more details)
        self.task_tree = ttk.Treeview(frame, columns=("Status",), show="headings")
        self.task_tree.heading("#0", text="Goal") # This is a hidden column used for the main text
        self.task_tree.heading("Status", text="Status")
        self.task_tree.column("#0", width=180)
        self.task_tree.column("Status", width=70, anchor=tk.CENTER)
        
        self.task_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_select)

    # --- Provider Management ---
    def refresh_provider_list(self):
        self.provider_listbox.delete(0, tk.END)
        for p in load_provider_configs():
            self.provider_listbox.insert(tk.END, p['name'])

    def on_provider_select(self, event=None):
        # This can be used to pre-fill the "New Task" dialog if needed
        pass

    def add_edit_provider(self):
        # A simple dialog for now. A dedicated window would be better for complex edits.
        # For simplicity, we'll just open the JSON file for the user to edit.
        messagebox.showinfo("Edit Providers", f"Please edit the 'api_config.json' file directly.\n\nAfter saving the file, you might need to restart the application for changes to take full effect in running tasks.")
    
    def delete_provider(self):
        selections = self.provider_listbox.curselection()
        if not selections:
            messagebox.showwarning("No Selection", "Please select a provider to delete.")
            return

        provider_name = self.provider_listbox.get(selections[0])
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the provider '{provider_name}'?"):
            configs = load_provider_configs()
            configs = [p for p in configs if p['name'] != provider_name]
            save_provider_configs(configs)
            self.refresh_provider_list()

    # --- Task Management ---
    def new_task(self):
        selections = self.provider_listbox.curselection()
        if not selections:
            messagebox.showerror("Error", "Please select an API provider first.")
            return
        
        provider_name = self.provider_listbox.get(selections[0])
        goal = simpledialog.askstring("New Task", "Enter the task goal:", parent=self)
        
        if goal:
            task_id = str(uuid.uuid4())
            llm_provider = get_provider(provider_name)
            if not llm_provider:
                messagebox.showerror("Error", f"Failed to load provider '{provider_name}'.")
                return

            task = {
                "id": task_id,
                "goal": goal,
                "provider": llm_provider,
                "status": "Pending",
                "log": [],
                "thread": None
            }
            self.tasks[task_id] = task
            
            # Add to treeview and start it
            tree_id = self.task_tree.insert("", tk.END, text=goal, values=("Pending",), iid=task_id)
            self.start_task(task_id)
            
    def start_task(self, task_id):
        task = self.tasks[task_id]
        if task['status'] == "Running":
            return

        self.update_task_status(task_id, "Running")
        
        # The agent needs a logger and an input function
        thread_logger = ThreadSafeLogger(self.log_queue)
        
        agent = Agent(
            goal=task['goal'],
            llm_provider=task['provider'],
            log_func=thread_logger,
            input_func=self.input_handler
        )

        def agent_runner():
            try:
                agent.run()
                self.update_task_status(task_id, "Completed")
            except Exception as e:
                thread_logger(f"💥 AGENT CRASHED: {e}")
                self.update_task_status(task_id, "Failed")
        
        task['thread'] = threading.Thread(target=agent_runner, daemon=True)
        task['thread'].start()

    def update_task_status(self, task_id, status):
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = status
            self.task_tree.item(task_id, values=(status,))

    def on_task_select(self, event=None):
        selections = self.task_tree.selection()
        if not selections:
            return
        
        task_id = selections[0]
        task = self.tasks.get(task_id)
        if task:
            self.display_log_for_task(task)

    # --- Logging ---
    def process_log_queue(self):
        # Check for input requests from the worker thread
        self.input_handler.check_for_input_request()
        
        try:
            while True:
                message = self.log_queue.get_nowait()
                
                # Find which task is currently running to associate the log message
                current_task_id = None
                for tid, t in self.tasks.items():
                    if t['status'] == 'Running':
                        current_task_id = tid
                        break
                
                if current_task_id:
                    self.tasks[current_task_id]['log'].append(message)
                
                # If the message belongs to the currently selected task, display it
                selections = self.task_tree.selection()
                if selections and selections[0] == current_task_id:
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
