import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
import os
import urllib.request
import sys
import platform


def resource_path(relative_path):
    # 获取用户文档文件夹路径
    documents_folder = os.path.expanduser("~/Documents")
    
    # 拼接 prompts 子目录
    prompts_folder = os.path.join(documents_folder, "prompts")
    
    # 如果目录不存在，则创建它
    if not os.path.exists(prompts_folder):
        os.makedirs(prompts_folder)
    
    # 返回完整的文件路径
    return os.path.join(prompts_folder, relative_path)

class PromptCombinerApp:
    def __init__(self, root):
        """
        初始化AI Prompt生成器的图形用户界面和相关数据结构。
    
        参数:
        root: Tkinter的主窗口对象。
    
        返回值:
        无
        """
        self.root = root
        self.root.title("AI Prompt生成器")
    
        # 设置窗口图标
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"无法设置窗口图标: {e}")
    
        # 设置窗口大小和位置
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
    
        # 检查系统平台并设置适当的字体
        if platform.system() == "Windows":
            default_font = ("Microsoft YaHei UI", 10)
        elif platform.system() == "Darwin":  # macOS
            default_font = ("Arial Unicode MS", 10)
        else:  # Linux 等其他系统
            default_font = ("SimHei", 10)
    
        # 配置默认字体
        self.root.option_add("*Font", default_font)
    
        # 初始化数据结构
        self.prompt_type_dict = {}  # 类型字典
        self.current_selected_type_dict = {}  # 当前选中类型的提示词
        self.preset_dict = {}  # 预设字典
    
        # 创建数据库连接
        db_path = resource_path('prompts.db')
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
        # 创建TabControl
        self.tab_control = ttk.Notebook(root)
    
        # Prompt生成Tab
        self.prompt_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.prompt_tab, text="提示词生成")
        self.create_prompt_tab()
    
        # 增删改查Tab
        self.crud_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.crud_tab, text="提示词管理")
        self.create_crud_tab()
    
        # 导入导出Tab
        self.import_export_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.import_export_tab, text="数据管理")
        self.create_import_export_tab()
    
        self.tab_control.pack(expand=1, fill="both")
    
        # 初始化数据
        self.initialize_prompt_type_dict()
        self.initialize_prompt_type_combobox()
        self.initialize_presets()

    def create_tables(self):
        """
        创建所需的数据库表结构。
        
        本函数负责根据数据库连接属性self.conn，创建三个主要的数据库表：
        1. prompt_types：存储提示类型信息。
        2. prompts：存储提示信息，包括提示的类型、名称、文本内容和介绍。
        3. presets：存储预设信息，包括预设名称、提示和负提示。
        
        每个表的创建都使用了SQL的CREATE TABLE IF NOT EXISTS语句，确保只有在表尚不存在的情况下才会创建，避免了重复创建表导致的错误。
        """
        # 初始化数据库游标
        cursor = self.conn.cursor()
        
        # 创建类型表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT UNIQUE
            )
        ''')
        
        # 创建提示词表，使用外键关联类型表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_id INTEGER,
                prompt_name TEXT,
                prompt_text TEXT,
                introduction TEXT,
                FOREIGN KEY (type_id) REFERENCES prompt_types (id)
            )
        ''')
        
        # 预设表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preset_name TEXT,
                prompt TEXT,
                negative_prompt TEXT
            )
        ''')
        
        # 提交事务，确保表创建成功
        self.conn.commit()

    def create_prompt_tab(self):
        """
        创建Prompt标签页的UI组件。
        该方法负责在prompt_tab标签页下构建所有必要的UI元素，包括类型选择、提示词选择、
        文本输入框、按钮以及预设配置的加载和保存功能。
        """
        # 创建主框架
        main_frame = ttk.Frame(self.prompt_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=5)
        
        # Prompt类型选择框
        ttk.Label(control_frame, text="类型:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prompt_type_combobox = ttk.Combobox(control_frame, width=15)
        self.prompt_type_combobox.bind("<<ComboboxSelected>>", self.prompt_type_combobox_selection_changed)
        self.prompt_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
        # Prompt选择框
        ttk.Label(control_frame, text="提示词:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.prompt_combobox = ttk.Combobox(control_frame, width=15)
        self.prompt_combobox.bind("<<ComboboxSelected>>", self.prompt_combobox_selection_changed)
        self.prompt_combobox.grid(row=0, column=3, padx=5, pady=5, sticky="w")
    
        # 添加到Prompt按钮
        self.add_to_prompt_button = ttk.Button(
            control_frame, 
            text="Positive Prompt", 
            command=self.add_to_prompt_button_click,
            style="Accent.TButton"
        )
        self.add_to_prompt_button.grid(row=0, column=4, padx=5, pady=5, sticky="w")
    
        # 添加到Negative按钮
        self.add_to_negative_button = ttk.Button(
            control_frame, 
            text="Negative Prompt", 
            command=self.add_to_negative_button_click,
            style="Accent.TButton"
        )
        self.add_to_negative_button.grid(row=0, column=5, padx=5, pady=5, sticky="w")
    
        # Prompt文本框
        ttk.Label(main_frame, text="Positive Prompt:").pack(anchor="w", padx=5, pady=5)
        self.prompt_textbox = tk.Text(main_frame, height=5, width=60)
        self.prompt_textbox.pack(fill="x", padx=5, pady=5)
    
        # Negative Prompt文本框
        ttk.Label(main_frame, text="Negative Prompt:").pack(anchor="w", padx=5, pady=5)
        self.negative_prompt_textbox = tk.Text(main_frame, height=3, width=60)
        self.negative_prompt_textbox.pack(fill="x", padx=5, pady=5)
    
        # 预设区域
        preset_frame = ttk.LabelFrame(main_frame, text="预设")
        preset_frame.pack(fill="x", padx=5, pady=5)
        
        # 预设选择框
        ttk.Label(preset_frame, text="选择预设:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.presets_combobox = ttk.Combobox(preset_frame, width=20)
        self.presets_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
        # 加载预设按钮
        self.load_config_button = ttk.Button(
            preset_frame, 
            text="加载预设", 
            command=self.load_config_button_click,
            style="Accent.TButton"
        )
        self.load_config_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
    
        # 保存预设按钮
        self.save_config_button = ttk.Button(
            preset_frame, 
            text="保存预设", 
            command=self.save_config_button_click,
            style="Accent.TButton"
        )
        self.save_config_button.grid(row=0, column=3, padx=5, pady=5, sticky="w")
    
        # 介绍标签
        ttk.Label(main_frame, text="介绍:").pack(anchor="w", padx=5, pady=5)
        self.introduction_label = tk.Label(
            main_frame, 
            text="", 
            borderwidth=1, 
            relief="solid", 
            width=60, 
            height=3,
            wraplength=580,
            justify="left"
        )
        self.introduction_label.pack(fill="x", padx=5, pady=5)

    def create_crud_tab(self):
            """
            创建CRUD（创建、读取、更新、删除）选项卡的UI组件。
            
            该方法负责构建和组织CRUD操作相关的用户界面元素，包括类型和提示词的选择、
            类型和提示词的管理操作按钮，以及相关的文本输入和显示区域。
            """
            # 创建主框架
            main_frame = ttk.Frame(self.crud_tab)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # 类型和提示词选择区域
            select_frame = ttk.LabelFrame(main_frame, text="选择类型和提示词")
            select_frame.pack(fill="x", padx=5, pady=5)
            
            # 提示词类型选择框
            ttk.Label(select_frame, text="类型:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.crud_type_combobox = ttk.Combobox(select_frame, width=15)
            self.crud_type_combobox.bind("<<ComboboxSelected>>", self.crud_type_combobox_selection_changed)
            self.crud_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
            # 提示词选择框
            ttk.Label(select_frame, text="提示词:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
            self.crud_prompt_combobox = ttk.Combobox(select_frame, width=15)
            self.crud_prompt_combobox.bind("<<ComboboxSelected>>", self.crud_prompt_combobox_selection_changed)
            self.crud_prompt_combobox.grid(row=0, column=3, padx=5, pady=5, sticky="w")
    
            # 类型管理区域
            type_frame = ttk.LabelFrame(main_frame, text="类型管理")
            type_frame.pack(fill="x", padx=5, pady=5)
            
            # 类型名称输入框
            ttk.Label(type_frame, text="类型名称:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.type_name_entry = ttk.Entry(type_frame, width=15)
            self.type_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
            # 类型操作按钮
            type_button_frame = ttk.Frame(type_frame)
            type_button_frame.grid(row=0, column=2, padx=5, pady=5)
            
            # 新增类型按钮
            self.add_type_button = ttk.Button(
                type_button_frame, 
                text="新增类型", 
                command=self.add_type,
                style="Accent.TButton"
            )
            self.add_type_button.pack(side="left", padx=2)
            
            # 修改类型按钮
            self.update_type_button = ttk.Button(
                type_button_frame, 
                text="修改类型", 
                command=self.update_type,
                style="Accent.TButton"
            )
            self.update_type_button.pack(side="left", padx=2)
    
            # 删除类型按钮
            self.delete_type_button = ttk.Button(
                type_button_frame, 
                text="删除类型", 
                command=self.delete_type,
                style="Destructive.TButton"
            )
            self.delete_type_button.pack(side="left", padx=2)
    
            # 提示词管理区域
            prompt_frame = ttk.LabelFrame(main_frame, text="提示词管理")
            prompt_frame.pack(fill="x", padx=5, pady=5)
            
            # 提示词名称输入框
            ttk.Label(prompt_frame, text="提示词名称:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.crud_prompt_name_entry = ttk.Entry(prompt_frame, width=15)
            self.crud_prompt_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            # 提示词文本框
            ttk.Label(main_frame, text="提示词文本:").pack(anchor="w", padx=5, pady=5)
            self.crud_prompt_textbox = tk.Text(main_frame, height=5, width=60)
            self.crud_prompt_textbox.pack(fill="x", padx=5, pady=5)
            
            # 提示词操作按钮
            button_frame = ttk.Frame(prompt_frame)
            button_frame.grid(row=0, column=4, rowspan=2, padx=5, pady=5)
            
            # 新增提示词按钮
            self.add_prompt_button = ttk.Button(
                button_frame, 
                text="新增提示词", 
                command=self.add_prompt,
                style="Accent.TButton"
            )
            self.add_prompt_button.pack(side="left", padx=2)
    
            # 修改提示词按钮
            self.update_prompt_button = ttk.Button(
                button_frame, 
                text="修改提示词", 
                command=self.update_prompt,
                style="Accent.TButton"
            )
            self.update_prompt_button.pack(side="left", padx=2)
    
            # 删除提示词按钮
            self.delete_prompt_button = ttk.Button(
                button_frame, 
                text="删除提示词", 
                command=self.delete_prompt,
                style="Destructive.TButton"
            )
            self.delete_prompt_button.pack(side="left", padx=2)
    
            # 介绍文本框
            ttk.Label(main_frame, text="介绍:").pack(anchor="w", padx=5, pady=5)
            self.crud_introduction_textbox = tk.Text(main_frame, height=3, width=60)
            self
    def create_import_export_tab(self):
        # 创建主框架
        main_frame = ttk.Frame(self.import_export_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 远程数据区域
        remote_frame = ttk.LabelFrame(main_frame, text="远程数据")
        remote_frame.pack(fill="x", padx=5, pady=5)
        
        # 远程plist文件地址文本框
        ttk.Label(remote_frame, text="远程PLIST地址:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.remote_prompt_url_textbox = ttk.Entry(remote_frame, width=40)
        self.remote_prompt_url_textbox.insert(0, "https://raw.githubusercontent.com/luzamm/PromptCombiner/master/default.plist")
        self.remote_prompt_url_textbox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # 应用远程prompt按钮
        self.apply_remote_prompt_button = ttk.Button(
            remote_frame, 
            text="应用远程prompt", 
            command=self.apply_remote_prompt_button_click,
            style="Accent.TButton"
        )
        self.apply_remote_prompt_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # 导入导出区域
        io_frame = ttk.LabelFrame(main_frame, text="导入导出")
        io_frame.pack(fill="x", padx=5, pady=5)
        
        # 导出按钮
        self.export_button = ttk.Button(
            io_frame, 
            text="导出为JSON", 
            command=self.export_to_json,
            style="Accent.TButton"
        )
        self.export_button.grid(row=0, column=0, padx=5, pady=5)

        # 导入按钮
        self.import_button = ttk.Button(
            io_frame, 
            text="从JSON/PLIST导入", 
            command=self.import_from_json,
            style="Accent.TButton"
        )
        self.import_button.grid(row=0, column=1, padx=5, pady=5)

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="准备就绪", width=40)
        self.status_label.pack(padx=5, pady=5)

    def initialize_prompt_type_dict(self):
        self.prompt_type_dict.clear()
        cursor = self.conn.cursor()
    
        try:
            # 获取所有类型
            cursor.execute("SELECT id, type_name FROM prompt_types")
            types = cursor.fetchall()
    
            # 获取所有提示词
            cursor.execute("SELECT id, type_id, prompt_name, prompt_text, introduction FROM prompts")
            prompts = cursor.fetchall()
    
            # 构建类型字典及 type_id 到 type_name 的映射
            type_id_to_name = {}
            for type_id, type_name in types:
                self.prompt_type_dict[type_name] = {
                    'id': type_id,
                    'prompts': {}
                }
                type_id_to_name[type_id] = type_name
    
            # 将提示词添加到对应类型
            for prompt_id, type_id, prompt_name, prompt_text, introduction in prompts:
                type_name = type_id_to_name.get(type_id)
                if type_name:
                    self.prompt_type_dict[type_name]['prompts'][prompt_name] = (prompt_id, prompt_text, introduction)
    
        except Exception as e:
            # 可根据实际项目替换为 logging.error(e)
            print(f"Error initializing prompt type dict: {e}")
        finally:
            cursor.close()

    def initialize_presets(self):
        """
        初始化预设参数。
    
        从数据库中加载预设参数，并更新界面组合框以显示这些预设参数。
        这个方法还会清空现有的预设参数字典，以确保数据的最新和一致性。
        """
        # 清空现有的预设参数字典，准备加载新的预设参数。
        self.preset_dict.clear()
        
        # 设置预设参数组合框的值为空列表，准备后续填充从数据库中获取的预设参数名称。
        self.presets_combobox['values'] = []
        
        # 创建数据库连接的游标对象，用于执行SQL查询。
        cursor = self.conn.cursor()
        
        # 执行SQL查询，获取所有预设参数的名称、提示和负提示。
        cursor.execute("SELECT preset_name, prompt, negative_prompt FROM presets")
        
        # 获取查询结果的所有行。
        rows = cursor.fetchall()
        
        # 遍历查询结果，将预设参数名称、提示和负提示保存到预设参数字典中。
        for row in rows:
            preset_name, prompt, negative_prompt = row
            self.preset_dict[preset_name] = (prompt, negative_prompt)
        
        # 更新预设参数组合框的值为预设参数字典中的所有键（即预设参数名称）。
        self.presets_combobox['values'] = list(self.preset_dict.keys())

    def initialize_prompt_type_combobox(self):
        """
        初始化提示类型和CRUD类型组合框的值。
        
        该方法将提示类型组合框和CRUD类型组合框的值设置为提示类型字典的键。
        这样做是为了确保用户界面组件可以正确地显示所有可用的提示和CRUD类型。
        """
        # 设置提示类型组合框的值为提示类型字典的键
        self.prompt_type_combobox['values'] = list(self.prompt_type_dict.keys())
        # 设置CRUD类型组合框的值为提示类型字典的键
        self.crud_type_combobox['values'] = list(self.prompt_type_dict.keys())

    def prompt_type_combobox_selection_changed(self, event):
        """
        当prompt类型组合框的选中项发生变化时调用此函数。
    
        参数:
        - event: 事件对象，由绑定的事件触发时自动传递。
    
        此函数更新当前选中的prompt类型，并刷新prompt组合框的选项。
        如果选中的类型存在于预定义的字典中，则更新当前选中类型的字典，
        并设置prompt组合框的值为当前选中类型的所有prompts。
        最后，清除prompt组合框的当前选中项和介绍标签的文本。
        """
        # 获取当前选中的prompt类型
        selected_type = self.prompt_type_combobox.get()
        
        # 检查选中的类型是否在预定义的字典中
        if selected_type in self.prompt_type_dict:
            # 更新当前选中类型的字典
            self.current_selected_type_dict = self.prompt_type_dict[selected_type]['prompts']
            # 设置prompt组合框的值为当前选中类型的所有prompts
            self.prompt_combobox['values'] = list(self.current_selected_type_dict.keys())
        
        # 清除prompt组合框的当前选中项
        self.prompt_combobox.set('')
        # 清除介绍标签的文本
        self.introduction_label.config(text="")

    def prompt_combobox_selection_changed(self, event):
        """
        当提示词组合框的选中项发生变化时调用此函数。
        
        参数:
        - event: 事件对象，由绑定的事件触发时自动传递。
        
        功能:
        - 获取当前选中的提示词。
        - 检查该提示词是否存在于当前选中的类型字典中。
        - 如果存在，获取对应的介绍信息，并更新介绍标签的文本。
        """
        # 获取当前选中的提示词
        selected_prompt = self.prompt_combobox.get()
        
        # 检查该提示词是否存在于当前选中的类型字典中
        if selected_prompt and selected_prompt in self.current_selected_type_dict:
            # 获取该提示词对应的介绍信息
            introduction = self.current_selected_type_dict[selected_prompt][2]
            
            # 更新介绍标签的文本
            self.introduction_label.config(text=introduction)

    def add_to_prompt_button_click(self):
        """
        当用户点击 "Positive Prompt" 按钮时，将当前选中的提示词添加到正向提示文本框中。
        
        功能描述:
        - 获取 prompt_combobox 中当前选中的提示词名称。
        - 检查该提示词是否存在于当前选中的类型字典中。
        - 如果存在，从字典中获取对应的提示词文本内容。
        - 将提示词文本内容插入到 prompt_textbox 的末尾，并在后面加上逗号和空格。

        参数:
        无直接参数。通过 self 对象访问以下属性:
        - self.prompt_combobox: 提示词选择下拉框。
        - self.current_selected_type_dict: 当前选中类型的提示词字典。
        - self.prompt_textbox: 存放正向提示词的文本框。
        
        返回值:
        无返回值。操作结果反映在界面上的文本框中。
        """
        selected_prompt = self.prompt_combobox.get()
        if selected_prompt and selected_prompt in self.current_selected_type_dict:
            prompt = self.current_selected_type_dict[selected_prompt][1]
            self.prompt_textbox.insert(tk.END, prompt + ', ')

    def add_to_negative_button_click(self):
        selected_prompt = self.prompt_combobox.get()
        if selected_prompt and selected_prompt in self.current_selected_type_dict:
            prompt = self.current_selected_type_dict[selected_prompt][1]
            self.negative_prompt_textbox.insert(tk.END, prompt + ', ')

    def save_config_button_click(self):
        prompt = self.prompt_textbox.get("1.0", tk.END).strip()
        negative_prompt = self.negative_prompt_textbox.get("1.0", tk.END).strip()

        def save_preset():
            save_name = save_name_entry.get().strip()
            if save_name:
                cursor = self.conn.cursor()
                # 检查预设名称是否已存在
                cursor.execute("SELECT id FROM presets WHERE preset_name = ?", (save_name,))
                existing_preset = cursor.fetchone()
                
                if existing_preset:
                    # 更新现有预设
                    cursor.execute(
                        "UPDATE presets SET prompt = ?, negative_prompt = ? WHERE preset_name = ?",
                        (prompt, negative_prompt, save_name)
                    )
                else:
                    # 插入新预设
                    cursor.execute(
                        "INSERT INTO presets (preset_name, prompt, negative_prompt) VALUES (?,?,?)",
                        (save_name, prompt, negative_prompt)
                    )
                
                self.conn.commit()
                save_window.destroy()
                self.initialize_presets()
                messagebox.showinfo("成功", f"预设 '{save_name}' 已保存")
            else:
                messagebox.showerror("错误", "请输入预设名称")

        save_window = tk.Toplevel(self.root)
        save_window.title("保存预设")
        save_window.geometry("300x150")
        save_window.resizable(False, False)
        save_window.transient(self.root)
        save_window.grab_set()
        
        # 设置窗口样式
        save_frame = ttk.Frame(save_window)
        save_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        save_name_label = ttk.Label(save_frame, text="预设名称:")
        save_name_label.pack(pady=10)

        save_name_entry = ttk.Entry(save_frame, width=25)
        save_name_entry.pack(pady=5)
        save_name_entry.focus_set()

        save_confirm_button = ttk.Button(
            save_frame, 
            text="保存", 
            command=save_preset,
            style="Accent.TButton"
        )
        save_confirm_button.pack(pady=10)

    def load_config_button_click(self):
        selected_preset = self.presets_combobox.get()
        if selected_preset and selected_preset in self.preset_dict:
            prompt, negative_prompt = self.preset_dict[selected_preset]
            self.prompt_textbox.delete("1.0", tk.END)
            self.prompt_textbox.insert(tk.END, prompt)
            self.negative_prompt_textbox.delete("1.0", tk.END)
            self.negative_prompt_textbox.insert(tk.END, negative_prompt)

    def apply_remote_prompt_button_click(self):
        url = self.remote_prompt_url_textbox.get()
        if url:
            try:
                # 创建保存目录
                if not os.path.exists("prompts"):
                    os.makedirs("prompts")
                
                file_name = "default.plist"
                file_path = os.path.join("prompts", file_name)
                
                # 下载文件
                with urllib.request.urlopen(url) as response, open(file_path, 'wb') as out_file:
                    data = response.read()
                    out_file.write(data)
                
                cursor = self.conn.cursor()
                
                # 清空现有数据
                cursor.execute("DELETE FROM prompts")
                cursor.execute("DELETE FROM prompt_types")
                
                # 重新导入数据
                type_map = {}  # 用于映射类型名称到ID
                
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        fields = line.strip().split('^')
                        if len(fields) == 4:
                            prompt_type, prompt_name, prompt_text, introduction = fields
                            
                            # 如果类型不存在，创建新类型
                            if prompt_type not in type_map:
                                cursor.execute("INSERT INTO prompt_types (type_name) VALUES (?)", (prompt_type,))
                                type_id = cursor.lastrowid
                                type_map[prompt_type] = type_id
                            else:
                                type_id = type_map[prompt_type]
                            
                            # 插入提示词
                            cursor.execute(
                                "INSERT INTO prompts (type_id, prompt_name, prompt_text, introduction) VALUES (?,?,?,?)",
                                (type_id, prompt_name, prompt_text, introduction)
                            )
                
                self.conn.commit()

                self.initialize_prompt_type_dict()
                self.initialize_prompt_type_combobox()
                messagebox.showinfo("成功", "远程prompt应用成功")
            except Exception as e:
                messagebox.showerror("错误", f"下载失败: {str(e)}")

    def crud_type_combobox_selection_changed(self, event):
        selected_type = self.crud_type_combobox.get()
        if selected_type in self.prompt_type_dict:
            self.current_selected_type_dict = self.prompt_type_dict[selected_type]['prompts']
            self.crud_prompt_combobox['values'] = list(self.current_selected_type_dict.keys())
            self.type_name_entry.delete(0, tk.END)
            self.type_name_entry.insert(0, selected_type)
        self.crud_prompt_combobox.set('')
        self.crud_prompt_textbox.delete("1.0", tk.END)
        self.crud_introduction_textbox.delete("1.0", tk.END)
        self.crud_prompt_name_entry.delete(0, tk.END)

    def crud_prompt_combobox_selection_changed(self, event):
        selected_prompt = self.crud_prompt_combobox.get()
        if selected_prompt and selected_prompt in self.current_selected_type_dict:
            prompt_id, prompt_text, introduction = self.current_selected_type_dict[selected_prompt]
            self.crud_prompt_textbox.delete("1.0", tk.END)
            self.crud_prompt_textbox.insert(tk.END, prompt_text)
            self.crud_introduction_textbox.delete("1.0", tk.END)
            self.crud_introduction_textbox.insert(tk.END, introduction)
            self.crud_prompt_name_entry.delete(0, tk.END)
            self.crud_prompt_name_entry.insert(0, selected_prompt)

    def add_prompt(self):
        selected_type = self.crud_type_combobox.get()
        prompt_name = self.crud_prompt_name_entry.get().strip()
        prompt_text = self.crud_prompt_textbox.get("1.0", tk.END).strip()
        introduction = self.crud_introduction_textbox.get("1.0", tk.END).strip()

        if selected_type and prompt_name and prompt_text :
            type_id = self.prompt_type_dict[selected_type]['id']
            cursor = self.conn.cursor()
            
            # 检查提示词是否已存在
            cursor.execute(
                "SELECT id FROM prompts WHERE type_id = ? AND prompt_name = ?",
                (type_id, prompt_name)
            )
            existing_prompt = cursor.fetchone()
            
            if existing_prompt:
                messagebox.showerror("错误", f"该类型下已存在名为 '{prompt_name}' 的提示词")
                return
            
            cursor.execute(
                "INSERT INTO prompts (type_id, prompt_name, prompt_text, introduction) VALUES (?,?,?,?)",
                (type_id, prompt_name, prompt_text, introduction)
            )
            self.conn.commit()
            self.refresh_crud()
            messagebox.showinfo("成功", "提示词添加成功")
        else:
            messagebox.showerror("错误", "请填写完整信息")

    def update_prompt(self):
        selected_type = self.crud_type_combobox.get()
        old_prompt_name = self.crud_prompt_combobox.get()
        new_prompt_name = self.crud_prompt_name_entry.get().strip()
        prompt_text = self.crud_prompt_textbox.get("1.0", tk.END).strip()
        introduction = self.crud_introduction_textbox.get("1.0", tk.END).strip()

        if selected_type and (old_prompt_name or new_prompt_name) and prompt_text and introduction:
            type_id = self.prompt_type_dict[selected_type]['id']
            cursor = self.conn.cursor()
            
            if old_prompt_name and old_prompt_name != new_prompt_name:
                # 如果名称发生了变化，先删除旧记录
                cursor.execute("DELETE FROM prompts WHERE type_id = ? AND prompt_name = ?", (type_id, old_prompt_name))
            
            # 插入或更新记录
            cursor.execute(
                "INSERT INTO prompts (type_id, prompt_name, prompt_text, introduction) VALUES (?,?,?,?)",
                (type_id, new_prompt_name, prompt_text, introduction)
            )
            
            self.conn.commit()
            self.refresh_crud()
            messagebox.showinfo("成功", "提示词修改成功")
        else:
            messagebox.showerror("错误", "请选择提示词并填写完整信息")

    def delete_prompt(self):
        selected_type = self.crud_type_combobox.get()
        prompt_name = self.crud_prompt_combobox.get()

        if selected_type and prompt_name:
            if messagebox.askyesno("确认删除", f"确定要删除提示词 '{prompt_name}' 吗？"):
                type_id = self.prompt_type_dict[selected_type]['id']
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM prompts WHERE type_id = ? AND prompt_name = ?", (type_id, prompt_name))
                self.conn.commit()
                self.refresh_crud()
                messagebox.showinfo("成功", "提示词删除成功")
        else:
            messagebox.showerror("错误", "请选择要删除的提示词")

    def add_type(self):
        type_name = self.type_name_entry.get().strip()
        if type_name:
            cursor = self.conn.cursor()
            try:
                cursor.execute("INSERT INTO prompt_types (type_name) VALUES (?)", (type_name,))
                self.conn.commit()
                self.refresh_crud()
                messagebox.showinfo("成功", "类型添加成功")
            except sqlite3.IntegrityError:
                messagebox.showerror("错误", "类型名称已存在")
        else:
            messagebox.showerror("错误", "请输入类型名称")

    def update_type(self):
        old_type_name = self.crud_type_combobox.get()
        new_type_name = self.type_name_entry.get().strip()

        if old_type_name and new_type_name:
            if old_type_name == new_type_name:
                messagebox.showinfo("提示", "新旧类型名称相同，无需修改")
                return
                
            type_id = self.prompt_type_dict[old_type_name]['id']
            cursor = self.conn.cursor()
            try:
                # 更新类型名称
                cursor.execute("UPDATE prompt_types SET type_name = ? WHERE id = ?", (new_type_name, type_id))
                
                self.conn.commit()
                self.refresh_crud()
                messagebox.showinfo("成功", "类型修改成功")
            except sqlite3.IntegrityError:
                messagebox.showerror("错误", "类型名称已存在")
        else:
            messagebox.showerror("错误", "请选择类型并输入新名称")

    def delete_type(self):
        type_name = self.crud_type_combobox.get()
        if type_name:
            if messagebox.askyesno("确认删除", f"确定要删除类型 '{type_name}' 及其所有提示词吗？"):
                type_id = self.prompt_type_dict[type_name]['id']
                cursor = self.conn.cursor()
                
                # 删除该类型下的所有提示词
                cursor.execute("DELETE FROM prompts WHERE type_id = ?", (type_id,))
                
                # 删除类型
                cursor.execute("DELETE FROM prompt_types WHERE id = ?", (type_id,))
                
                self.conn.commit()
                self.refresh_crud()
                messagebox.showinfo("成功", "类型删除成功")
        else:
            messagebox.showerror("错误", "请选择要删除的类型")

    def refresh_crud(self):
        self.initialize_prompt_type_dict()
        self.initialize_prompt_type_combobox()
        self.crud_type_combobox.set('')
        self.crud_prompt_combobox.set('')
        self.crud_prompt_textbox.delete("1.0", tk.END)
        self.crud_introduction_textbox.delete("1.0", tk.END)
        self.crud_prompt_name_entry.delete(0, tk.END)
        self.type_name_entry.delete(0, tk.END)

    def export_to_json(self):
        cursor = self.conn.cursor()
        
        # 获取所有类型
        cursor.execute("SELECT id, type_name FROM prompt_types")
        types = cursor.fetchall()
        
        # 获取所有提示词
        cursor.execute("SELECT id, type_id, prompt_name, prompt_text, introduction FROM prompts")
        prompts = cursor.fetchall()
        
        # 构建JSON数据结构
        json_data = {}
        
        # 添加类型和提示词
        for type_id, type_name in types:
            type_prompts = {}
            for prompt in prompts:
                p_id, p_type_id, p_name, p_text, p_intro = prompt
                if p_type_id == type_id:
                    type_prompts[p_name] = {
                        "prompt_text": p_text,
                        "introduction": p_intro
                    }
            json_data[type_name] = type_prompts
        
        # 保存到文件
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                self.status_label.config(text=f"导出成功: {file_path}")
                messagebox.showinfo("成功", f"数据已导出到 {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def import_from_json(self):
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("PLIST files", "*.plist"), ("All files", "*.*")]
            )
            if file_path:
                file_ext = os.path.splitext(file_path)[1].lower()
                
                cursor = self.conn.cursor()
                
                # 清空现有数据
                cursor.execute("DELETE FROM prompts")
                cursor.execute("DELETE FROM prompt_types")
                
                if file_ext == '.json':
                    # 处理JSON文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # 导入JSON数据
                    type_map = {}  # 用于映射类型名称到ID
                    
                    for type_name, prompts in json_data.items():
                        # 创建类型
                        cursor.execute("INSERT INTO prompt_types (type_name) VALUES (?)", (type_name,))
                        type_id = cursor.lastrowid
                        type_map[type_name] = type_id
                        
                        # 创建提示词
                        for prompt_name, prompt_data in prompts.items():
                            prompt_text = prompt_data.get("prompt_text", "")
                            introduction = prompt_data.get("introduction", "")
                            cursor.execute("INSERT INTO prompts (type_id, prompt_name, prompt_text, introduction) VALUES (?,?,?,?)",
                                           (type_id, prompt_name, prompt_text, introduction))
                
                elif file_ext == '.plist':
                    # 处理PLIST文件
                    type_map = {}  # 用于映射类型名称到ID
                    
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            fields = line.strip().split('^')
                            if len(fields) == 4:
                                prompt_type, prompt_name, prompt_text, introduction = fields
                                
                                # 如果类型不存在，创建新类型
                                if prompt_type not in type_map:
                                    cursor.execute("INSERT INTO prompt_types (type_name) VALUES (?)", (prompt_type,))
                                    type_id = cursor.lastrowid
                                    type_map[prompt_type] = type_id
                                else:
                                    type_id = type_map[prompt_type]
                                
                                # 插入提示词
                                cursor.execute("INSERT INTO prompts (type_id, prompt_name, prompt_text, introduction) VALUES (?,?,?,?)",
                                               (type_id, prompt_name, prompt_text, introduction))
                
                self.conn.commit()
                self.refresh_crud()
                self.status_label.config(text=f"导入成功: {file_path}")
                messagebox.showinfo("成功", "数据导入成功")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PromptCombinerApp(root)
    root.mainloop()