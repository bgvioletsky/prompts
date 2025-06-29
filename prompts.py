'''
Author: bgcode
Date: 2025-06-29 09:51:17
LastEditTime: 2025-06-29 10:34:53
LastEditors: bgcode
Description: 描述
FilePath: /prompts/prompts.py
本项目采用GPL 许可证，欢迎任何人使用、修改和分发。
'''
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
import os
import urllib.request
import sys
import platform


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # 获取用户文档目录并构建目标路径
        documents_folder = os.path.expanduser("~/Documents")
        base_path = os.path.join(documents_folder, "prompts")

        # 确保路径合法，防止路径穿越攻击
        safe_relative_path = os.path.normpath(relative_path)
        if ".." in safe_relative_path.split(os.sep):
            raise ValueError("Relative path must not contain '..' to prevent path traversal.")

        # 创建目录（如果不存在）
        if not os.path.exists(base_path):
            os.makedirs(base_path)

    except (OSError, PermissionError) as e:
        # 明确捕获常见错误，并打印日志便于排查
        print(f"[Warning] Failed to create prompts directory: {e}")
    return os.path.join(base_path, safe_relative_path)
class PromptCombinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI绘图 Prompt生成器")
        try:
            if platform.system() == 'Windows':
                self.root.iconbitmap(resource_path('icon.ico'))
            elif platform.system() == 'Darwin':
                self.root.iconbitmap(resource_path('icon.icns'))
            else:
                self.root.iconbitmap(resource_path('icon.png'))
        except tk.TclError:
            print("[Warning] Failed to load icon.")
            
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        if platform.system() == "Windows":
            default_font = ("Microsoft YaHei UI", 10)
        elif platform.system() == "Darwin":  # macOS
            default_font = ("Arial Unicode MS", 10)
        else:  # Linux 等其他系统
            default_font = ("SimHei", 10)
        self.root.option_add("*Font", default_font)
        self.prompt_type_dict = {}  # 类型字典
        self.current_selected_type_dict = {}  # 当前选中类型的提示词
        self.preset_dict = {}  # 预设字典
        db_path = resource_path('test.db')
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        self.tab_control = ttk.Notebook(root)
        self.prompt_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.prompt_tab, text="提示词生成")
        self.create_prompt_tab()
        # self.crud_tab = ttk.Frame(self.tab_control)
        # self.tab_control.add(self.crud_tab, text="提示词管理")
        # self.create_crud_tab()
        # self.import_export_tab = ttk.Frame(self.tab_control)
        # self.tab_control.add(self.import_export_tab, text="数据管理")
        # self.create_import_export_tab()
        # self.tab_control.pack(expand=1, fill="both")
        # self.initialize_prompt_type_dict()
        # self.initialize_prompt_type_combobox()
        # self.initialize_presets()
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_id INTEGER,
                prompt_name TEXT,
                prompt_text TEXT,
                FOREIGN KEY (type_id) REFERENCES prompt_types (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preset_name TEXT,
                prompt TEXT,
                negative_prompt TEXT,
                introduction TEXT
            )
        ''')
        
        self.conn.commit()
        
    def create_prompt_tab(self):
        main_frame = ttk.Frame(self.prompt_tab)
        main_frame.pack(fill="both", expand=True,padx=10, pady=10)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x",pady=5)
        ttk.Label(control_frame, text="提示词类型:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prompt_type_combobox = ttk.Combobox(control_frame, width=15)
        self.prompt_type_combobox.bind("<<ComboboxSelected>>", self.prompt_type_combobox_selection_changed)
        self.prompt_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")       
        
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
        
    def  prompt_type_combobox_selection_changed(self, event):
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
    def add_to_prompt_button_click(self):
        selected_prompt = self.prompt_combobox.get()
        if selected_prompt and selected_prompt in self.current_selected_type_dict:
            prompt = self.current_selected_type_dict[selected_prompt][1]
            self.prompt_textbox.insert(tk.END, prompt + ', ')

    def add_to_negative_button_click(self):
        selected_prompt = self.prompt_combobox.get()
        if selected_prompt and selected_prompt in self.current_selected_type_dict:
            prompt = self.current_selected_type_dict[selected_prompt][1]
            self.negative_prompt_textbox.insert(tk.END, prompt + ', ')
    def load_config_button_click(self):
        selected_preset = self.presets_combobox.get()
        if selected_preset and selected_preset in self.preset_dict:
            prompt, negative_prompt = self.preset_dict[selected_preset]
            self.prompt_textbox.delete("1.0", tk.END)
            self.prompt_textbox.insert(tk.END, prompt)
            self.negative_prompt_textbox.delete("1.0", tk.END)
            self.negative_prompt_textbox.insert(tk.END, negative_prompt)

    def save_config_button_click(self):
        prompt = self.prompt_textbox.get("1.0", tk.END).strip()
        negative_prompt = self.negative_prompt_textbox.get("1.0", tk.END).strip()
        introduction = self.introduction_textbox.get("1.0", tk.END).strip()
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
                        "UPDATE presets SET prompt = ?, negative_prompt = ?,introduction = ? WHERE preset_name = ?",
                        (prompt, negative_prompt, introduction ,save_name)
                    )
                else:
                    # 插入新预设
                    cursor.execute(
                        "INSERT INTO presets (preset_name, prompt, negative_prompt,introduction) VALUES (?,?,?,?)",
                        (save_name, prompt, negative_prompt,introduction)
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

        
        
if __name__ == "__main__":
    root = tk.Tk()
    app = PromptCombinerApp(root)
    root.mainloop()