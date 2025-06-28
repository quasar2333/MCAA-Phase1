# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import threading
import queue
import uuid

from agent_core import Agent
from llm_interface import get_provider, load_provider_configs, save_provider_configs
from gui_provider_editor import ProviderEditor

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MCAA-Phase4 Awakening")
        self.geometry("1200x800")
        self.tasks = {} 
        self.log_queue = queue.Queue()
        self._init_ui()
        self.refresh_provider_list()
        self.process_gui_events()

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
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10))
        self.log_area.pack(fill=tk.BOTH, expand=True)

    # --- ALL FOLLOWING METHODS MUST BE AT THIS INDENTATION LEVEL ---

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

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_tasks)
        search_entry = ttk.Entry(frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.task_tree = ttk.Treeview(frame, columns=("Status",), show="tree headings")
        self.task_tree.heading("#0", text="Task")
        self.task_tree.heading("Status", text="Status")
        self.task_tree.column("#0", width=200, anchor=tk.W)
        self.task_tree.column("Status", width=80, anchor=tk.CENTER)
        
        self.task_tree.tag_configure("Running", foreground="#FFA500")
        self.task_tree.tag_configure("Completed", foreground="#008000")
        self.task_tree.tag_configure("Failed", foreground="#FF0000")
        self.task_tree.tag_configure("User Action Required", foreground="#800080")
        
        self.task_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.task_menu = tk.Menu(self, tearoff=0)
        self.task_tree.bind("<Button-3>", self.show_task_menu)
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_select)

    def process_gui_events(self):
        try:
            while True:
                log_item = self.log_queue.get_nowait()
                task_id, message = log_item["task_id"], log_item["message"]
                
                if task_id in self.tasks:
                    self.tasks[task_id]['log'].append(message)
                
                selections = self.task_tree.selection()
                if selections and selections[0] == task_id:
                    self._append_log_message(message)

        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_gui_events)

    def on_task_select(self, event=None):
        selections = self.task_tree.selection()
        if not selections:
            self._clear_log_area()
            return
        
        task_id = selections[0]
        task = self.tasks.get(task_id)
        if task:
            self._display_full_log_for_task(task)

    def _display_full_log_for_task(self, task):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        for msg in task['log']:
            self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def _append_log_message(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def _clear_log_area(self):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

    def show_task_menu(self, event):
        row_id = self.task_tree.identify_row(event.y)
        if not row_id: return
        self.task_tree.selection_set(row_id)
        task = self.tasks.get(row_id)
        if not task: return
        self.task_menu.delete(0, tk.END)
        status = task.get("status")
        if status not in ["Running", "Initializing"]:
            self.task_menu.add_command(label="Rerun Task", command=lambda: self.rerun_task(row_id))
            self.task_menu.add_command(label="Iterate/Modify...", command=lambda: self.iterate_task(row_id))
            self.task_menu.add_separator()
        self.task_menu.add_command(label="Delete Task", command=lambda: self.delete_task(row_id))
        self.task_menu.post(event.x_root, event.y_root)

    def rerun_task(self, task_id):
        task_data = self.tasks.get(task_id)
        if not task_data: return
        self.start_task(task_id, task_data, None)

    def iterate_task(self, task_id):
        task_data = self.tasks.get(task_id)
        if not task_data: return
        modification_request = simpledialog.askstring("Iterate Task", 
            f"Modifying task: '{task_data['title']}'\n\nEnter your new requirements:", parent=self)
        if modification_request:
            agent_instance = task_data.get("agent_instance")
            previous_context = {
                "original_goal": task_data['goal'],
                "modification_request": modification_request,
                "last_code": agent_instance.final_code_for_step.get(1) if agent_instance else "",
                "failure_reason": getattr(agent_instance, 'failure_reason', 'N/A') if agent_instance else "N/A"
            }
            self.start_task(task_id, task_data, previous_context)
    
    def new_task(self):
        selections = self.provider_listbox.curselection()
        if not selections:
            messagebox.showerror("Error", "Please select an API provider first.")
            return
        provider_name = self.provider_listbox.get(selections[0])
        goal = simpledialog.askstring("New Task", "Enter the task goal:", parent=self)
        if not goal: return
        verify = messagebox.askyesno("Self-Verification", "Enable self-verification mode?", parent=self)
        llm_provider = get_provider(provider_name)
        if not llm_provider: 
            messagebox.showerror("Error", f"Could not initialize provider '{provider_name}'.")
            return
        task_id = str(uuid.uuid4())
        placeholder_title = goal[:40] + '...' if len(goal) > 40 else goal
        task_data = { "id": task_id, "title": placeholder_title, "goal": goal, "provider": llm_provider, 
                      "verify": verify, "status": "Initializing", "log": [], "thread": None, "agent_instance": None }
        self.tasks[task_id] = task_data
        self.task_tree.insert("", tk.END, text=placeholder_title, values=("Initializing",), iid=task_id)
        threading.Thread(target=self._get_title_and_start_agent, args=(task_id,), daemon=True).start()

    def _get_title_and_start_agent(self, task_id):
        task_data = self.tasks.get(task_id)
        if not task_data: return
        try:
            title_prompt = f"Summarize the following user goal into a short title of 3-5 words.\n\nUser Goal: '{task_data['goal']}'"
            title = task_data['provider'].ask("You are a helpful assistant that creates short, descriptive titles.", title_prompt)
            self.after(0, lambda: self.task_tree.item(task_id, text=title))
            task_data['title'] = title
        except Exception as e:
            log_msg = f"⚠️ Could not summarize goal: {e}."
            self.log_queue.put({"task_id": task_id, "message": log_msg})
        self.start_task(task_id, task_data, None)

    def start_task(self, task_id, task_data, previous_context):
        task_data['log'].clear()
        self.update_task_status(task_id, "Running")
        if self.task_tree.selection() and self.task_tree.selection()[0] == task_id:
             self.on_task_select()
        def thread_logger(message: str):
            self.log_queue.put({"task_id": task_id, "message": message})
        agent = Agent(task_data['goal'], task_data['provider'], thread_logger, task_data['verify'], previous_context)
        task_data['agent_instance'] = agent
        def agent_runner():
            final_status = "Completed"
            try:
                agent_instance = self.tasks[task_id]['agent_instance']
                success = agent_instance.run()
                if not success:
                    if "need your help" in getattr(agent_instance, 'failure_reason', ''):
                        final_status = "User Action Required"
                    else:
                        final_status = "Failed"
            except Exception:
                final_status = "Failed"
            self.update_task_status(task_id, final_status)
        task_data['thread'] = threading.Thread(target=agent_runner, daemon=True)
        task_data['thread'].start()
        
    def delete_task(self, task_id):
        if not task_id in self.tasks: return
        task_title = self.tasks[task_id]['title']
        if messagebox.askyesno("Confirm Deletion", f"Delete task '{task_title}'?"):
            if self.task_tree.exists(task_id):
                self.task_tree.delete(task_id)
            del self.tasks[task_id]
            self._clear_log_area()
            
    def refresh_provider_list(self):
        selected_index = self.provider_listbox.curselection()
        self.provider_listbox.delete(0, tk.END)
        for p in load_provider_configs():
            self.provider_listbox.insert(tk.END, p['name'])
        if selected_index:
            try:
                self.provider_listbox.selection_set(selected_index[0])
            except tk.TclError:
                pass

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
    
    def filter_tasks(self, *args):
        search_term = self.search_var.get().lower()
        
        # Detach all items first
        all_children = self.task_tree.get_children()
        for item in all_children:
            self.task_tree.detach(item)

        # Re-attach items that match the search term
        for task_id, task_data in self.tasks.items():
            if not search_term or search_term in task_data['title'].lower() or search_term in task_data['goal'].lower():
                 # Move the item back to the root
                 self.task_tree.move(task_id, '', 'end')

    def update_task_status(self, task_id, status):
        def _update():
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = status
                if self.task_tree.exists(task_id):
                    self.task_tree.item(task_id, values=(status,), tags=(status,))
        self.after(0, _update)

if __name__ == "__main__":
    try:
        from gui_provider_editor import ProviderEditor
    except ImportError:
        print("Fatal: Could not find 'gui_provider_editor.py'. Please ensure it exists.")
        exit(1)
        
    app = App()
    app.mainloop()