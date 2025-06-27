# gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import queue

from llm_interface import load_provider_configs, get_provider
from agent_core import Agent


class AgentThread(threading.Thread):
    def __init__(self, goal: str, provider_name: str, log_queue: queue.Queue, done_callback):
        super().__init__(daemon=True)
        self.goal = goal
        self.provider_name = provider_name
        self.log_queue = log_queue
        self.done_callback = done_callback

    def run(self):
        provider = get_provider(self.provider_name)
        if not provider:
            self.log_queue.put(f"Provider '{self.provider_name}' not found.\n")
            self.done_callback(False)
            return

        def log(msg: str):
            self.log_queue.put(msg + "\n")

        def user_input(prompt: str) -> str:
            # For GUI, we do a simple dialog
            return simpledialog.askstring("Input", prompt)

        agent = Agent(self.goal, provider, log, user_input)
        agent.run()
        self.done_callback(True)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MCAA-Phase1 GUI")
        self.geometry("900x600")

        self.log_queue = queue.Queue()
        self.current_thread = None

        self._create_widgets()
        self._load_providers()
        self.after(200, self._process_log_queue)

    def _create_widgets(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left pane - provider and new task
        left_frame = ttk.Frame(paned, width=200)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Providers").pack(anchor=tk.W, padx=5, pady=5)
        self.provider_list = ttk.Combobox(left_frame, state="readonly")
        self.provider_list.pack(fill=tk.X, padx=5)

        ttk.Label(left_frame, text="New Task").pack(anchor=tk.W, padx=5, pady=(15,5))
        self.goal_entry = ttk.Entry(left_frame)
        self.goal_entry.pack(fill=tk.X, padx=5)

        self.start_btn = ttk.Button(left_frame, text="Start", command=self.start_task)
        self.start_btn.pack(padx=5, pady=10, fill=tk.X)

        # Middle pane - tasks list
        middle_frame = ttk.Frame(paned, width=200)
        paned.add(middle_frame, weight=1)

        ttk.Label(middle_frame, text="Tasks").pack(anchor=tk.W, padx=5, pady=5)
        self.task_list = tk.Listbox(middle_frame)
        self.task_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right pane - logs
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        ttk.Label(right_frame, text="Logs").pack(anchor=tk.W, padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(right_frame, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _load_providers(self):
        configs = load_provider_configs()
        names = [c['name'] for c in configs]
        self.provider_list['values'] = names
        if names:
            self.provider_list.current(0)

    def _process_log_queue(self):
        while True:
            try:
                msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.log_text.configure(state='normal')
                self.log_text.insert(tk.END, msg)
                self.log_text.see(tk.END)
                self.log_text.configure(state='disabled')
        self.after(200, self._process_log_queue)

    def start_task(self):
        if self.current_thread and self.current_thread.is_alive():
            messagebox.showwarning("Running", "A task is already running.")
            return
        goal = self.goal_entry.get().strip()
        if not goal:
            messagebox.showinfo("Input", "Please enter a task goal.")
            return
        provider_name = self.provider_list.get()
        if not provider_name:
            messagebox.showinfo("Input", "Please select a provider.")
            return
        self.task_list.insert(tk.END, goal)
        index = self.task_list.size() - 1

        def done_callback(success: bool):
            status = "✅" if success else "❌"
            self.task_list.delete(index)
            self.task_list.insert(index, f"{status} {goal}")

        self.current_thread = AgentThread(goal, provider_name, self.log_queue, done_callback)
        self.current_thread.start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
