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
        self.title("MCAA-Phase4 觉醒")
        self.geometry("1200x800")
        self.tasks = {}
        self.log_queue = queue.Queue()
        self.status_display_map = {
            "Initializing": "初始化",
            "Running": "运行中",
            "Completed": "已完成",
            "Failed": "失败",
            "User Action Required": "需要用户操作",
        }
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
        
        log_frame = ttk.LabelFrame(right_pane, text="任务日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10))
        self.log_area.pack(fill=tk.BOTH, expand=True)

    # --- ALL FOLLOWING METHODS MUST BE AT THIS INDENTATION LEVEL ---

    def _create_provider_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="API提供者")
        frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        
        self.provider_listbox = tk.Listbox(frame, exportselection=False)
        self.provider_listbox.pack(fill=tk.X, padx=5, pady=5)
        self.provider_listbox.bind("<<ListboxSelect>>", self.on_provider_selected)

        ttk.Label(frame, text="选择模型:").pack(fill=tk.X, padx=5, pady=(5,0))
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(frame, textvariable=self.model_var, state="readonly")
        self.model_combobox.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5)
        ttk.Button(btn_frame, text="新增", command=self.add_provider).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="编辑", command=self.edit_provider).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="删除", command=self.delete_provider).pack(side=tk.LEFT, expand=True, fill=tk.X)

    def _create_task_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="任务")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(frame, text="新建任务", command=self.new_task).pack(fill=tk.X, padx=5, pady=5)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_tasks)
        search_entry = ttk.Entry(frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.task_tree = ttk.Treeview(frame, columns=("Status",), show="tree headings")
        self.task_tree.heading("#0", text="任务")
        self.task_tree.heading("Status", text="状态")
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

    def on_provider_selected(self, event=None):
        selections = self.provider_listbox.curselection()
        if not selections:
            self.model_combobox['values'] = []
            self.model_var.set('')
            return

        provider_name = self.provider_listbox.get(selections[0])
        provider = get_provider(provider_name)
        if provider:
            models = provider.get_available_models()
            self.model_combobox['values'] = models
            if models:
                # Set to current selected model of provider, or first if not set/invalid
                if provider.selected_model and provider.selected_model in models:
                    self.model_var.set(provider.selected_model)
                else:
                    self.model_var.set(models[0])
            else:
                self.model_var.set('')
        else:
            self.model_combobox['values'] = []
            self.model_var.set('')

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
            self.task_menu.add_command(label="重新运行任务", command=lambda: self.rerun_task(row_id))
            self.task_menu.add_command(label="迭代/修改...", command=lambda: self.iterate_task(row_id))
            self.task_menu.add_separator()
        self.task_menu.add_command(label="删除任务", command=lambda: self.delete_task(row_id))
        self.task_menu.post(event.x_root, event.y_root)

    def rerun_task(self, task_id):
        task_data = self.tasks.get(task_id)
        if not task_data: return
        self.start_task(task_id, task_data, None)

    def iterate_task(self, task_id):
        task_data = self.tasks.get(task_id)
        if not task_data: return
        modification_request = simpledialog.askstring(
            "迭代任务",
            f"正在修改任务: '{task_data['title']}'\n\n请输入新的需求:",
            parent=self
        )
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
            messagebox.showerror("错误", "请先选择一个API提供者。")
            return
        provider_name = self.provider_listbox.get(selections[0])

        selected_model_id = self.model_var.get()
        if not selected_model_id:
            messagebox.showerror("错误", "请为选定的提供者选择一个模型。")
            return

        goal = simpledialog.askstring("新建任务", "请输入任务目标:", parent=self)
        if not goal: return
        verify = messagebox.askyesno("自我验证", "是否启用自我验证模式?", parent=self)

        llm_provider = get_provider(provider_name)
        if not llm_provider:
            messagebox.showerror("错误", f"无法初始化提供者 '{provider_name}'。")
            return

        # Set the selected model on the provider instance
        if selected_model_id in llm_provider.get_available_models():
            llm_provider.selected_model = selected_model_id
        else:
            messagebox.showerror("错误", f"模型 '{selected_model_id}' 对于提供者 '{provider_name}' 无效。")
            return

        task_id = str(uuid.uuid4())
        placeholder_title = goal[:40] + '...' if len(goal) > 40 else goal
        task_data = { "id": task_id, "title": placeholder_title, "goal": goal, "provider": llm_provider, 
                      "verify": verify, "status": "Initializing", "log": [], "thread": None, "agent_instance": None }
        self.tasks[task_id] = task_data
        display_status = self.status_display_map.get("Initializing", "Initializing")
        self.task_tree.insert("", tk.END, text=placeholder_title, values=(display_status,), iid=task_id)
        threading.Thread(target=self._get_title_and_start_agent, args=(task_id,), daemon=True).start()

    def _get_title_and_start_agent(self, task_id):
        task_data = self.tasks.get(task_id)
        if not task_data: return
        try:
            title_prompt = f"请将以下用户目标概括成3-5个词的简短标题:\n\n用户目标: '{task_data['goal']}'"
            title = task_data['provider'].ask("You are a helpful assistant that creates short, descriptive titles.", title_prompt)
            self.after(0, lambda: self.task_tree.item(task_id, text=title))
            task_data['title'] = title
        except Exception as e:
            log_msg = f"⚠️ 无法生成标题: {e}."
            self.log_queue.put({"task_id": task_id, "message": log_msg})
        self.start_task(task_id, task_data, None)

    def start_task(self, task_id, task_data, previous_context):
        task_data['log'].clear()
        self.update_task_status(task_id, "Running")
        if self.task_tree.selection() and self.task_tree.selection()[0] == task_id:
             self.on_task_select()

        from datetime import datetime
        def thread_logger(message: str):
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3] # Include milliseconds
            formatted_message = f"[{timestamp}] {message}"
            self.log_queue.put({"task_id": task_id, "message": formatted_message})

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
        if messagebox.askyesno("确认删除", f"删除任务 '{task_title}'?"):
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
                current_selection = selected_index[0]
                self.provider_listbox.selection_set(current_selection)
                self.provider_listbox.see(current_selection) # Ensure it's visible
                self.on_provider_selected() # Update model list
            except tk.TclError: # Selection might be invalid if list changed
                self.model_combobox['values'] = []
                self.model_var.set('')
        else:
            self.model_combobox['values'] = []
            self.model_var.set('')


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
        if messagebox.askyesno("确认删除", f"删除提供者 '{provider_name}'?"):
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
                display_status = self.status_display_map.get(status, status)
                if self.task_tree.exists(task_id):
                    self.task_tree.item(task_id, values=(display_status,), tags=(status,))
        self.after(0, _update)

if __name__ == "__main__":
    try:
        from gui_provider_editor import ProviderEditor
    except ImportError:
        print("Fatal: 无法找到 'gui_provider_editor.py'，请确认文件存在。")
        exit(1)
        
    app = App()
    app.mainloop()