#!/usr/bin/env python3
"""
START WINDOW - Главное окно запуска программ
Размер окна 800x300 пикселей
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import sys
import os
import configparser

def load_config():
    """Загрузка конфигурации из config.ini"""
    config = configparser.ConfigParser()
    config_file = 'config.ini'
    
    if os.path.exists(config_file):
        config.read(config_file)
    
    # Получаем пути или используем значения по умолчанию
    raw_path = config.get('PATHS', 'raw_data', fallback=r'C:\Users\dotignore\Documents\Python\examplaone_krakenSDR_web\data_raw')
    convert_path = config.get('PATHS', 'convert_data', fallback=r'C:\Users\dotignore\Documents\Python\examplaone_krakenSDR_web\data')
    gap_time = config.get('SETTINGS', 'gap_time', fallback='0')
    
    return raw_path, convert_path, gap_time

def save_config(raw_path, convert_path, gap_time='0'):
    """Сохранение конфигурации в config.ini"""
    config = configparser.ConfigParser()
    config['PATHS'] = {
        'raw_data': raw_path,
        'convert_data': convert_path
    }
    config['SETTINGS'] = {
        'gap_time': gap_time
    }
    
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def browse_folder(path_var, label_widget=None):
    """Открывает диалог выбора папки и сохраняет путь"""
    folder_path = filedialog.askdirectory(initialdir=path_var.get(), title="Выберите папку")
    
    if folder_path:
        path_var.set(folder_path)
        # Сохраняем в config.ini сразу после изменения
        save_config(raw_path_var.get(), convert_path_var.get(), gap_time_var.get())

def main():
    """Основная функция запуска программы"""
    global raw_path_var, convert_path_var, gap_time_var
    root = tk.Tk()
    root.title("DMRScope")
    root.geometry("900x400")
    root.resizable(False, False)
    
    # Центрируем окно
    x = (root.winfo_screenwidth() // 2) - 400
    y = (root.winfo_screenheight() // 2) - 150
    root.geometry(f"+{x}+{y}")
    
    # Загружаем конфигурацию
    raw_data_path, convert_data_path, gap_time_value = load_config()
    
    # Переменные для хранения путей и настроек
    raw_path_var = tk.StringVar(value=raw_data_path)
    convert_path_var = tk.StringVar(value=convert_data_path)
    gap_time_var = tk.StringVar(value=gap_time_value)
    
    # Основной контейнер с продвинутым хакерским дизайном
    main_frame = tk.Frame(root, bg="#002244")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Верхняя панель с ASCII артом
    header_frame = tk.Frame(main_frame, bg="#002244")
    header_frame.pack(fill=tk.X, pady=(0, 10))
    
    # ASCII арт заголовок
    ascii_art = """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║  ██████╗ ███╗   ███╗██████╗ ███████╗ ██████╗ ██████╗ ██████╗ ███████╗ ║
    ║  ██╔══██╗████╗ ████║██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝ ║
    ║  ██║  ██║██╔████╔██║██████╔╝███████╗██║     ██║   ██║██████╔╝█████╗   ║
    ║  ██║  ██║██║╚██╔╝██║██╔══██╗╚════██║██║     ██║   ██║██╔═══╝ ██╔══╝   ║
    ║  ██████╔╝██║ ╚═╝ ██║██║  ██║███████║╚██████╗╚██████╔╝██║     ███████╗ ║
    ║  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚══════╝ ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """
    
    ascii_label = tk.Label(header_frame, text=ascii_art, 
                          font=("Courier New", 6), 
                          bg="#002244", fg="#66ffff", justify="left")
    ascii_label.pack()
    
    # Системная информация
    system_info = tk.Label(header_frame, text="[SYSTEM] v2.1.3 | [STATUS] ONLINE | [MODE] INTERACTIVE | [USER] ROOT", 
                          font=("Courier New", 8), 
                          bg="#002244", fg="#66ffff")
    system_info.pack(pady=(5, 0))
    
    # Контейнер для кнопок
    buttons_frame = tk.Frame(main_frame, bg="#002244")
    buttons_frame.pack(expand=True, fill=tk.BOTH)
    
    # Продвинутый хакерский стиль кнопок
    hacker_button_style = {
        "font": ("Courier New", 9, "bold"),
        "width": 18,
        "height": 4,
        "relief": "flat",
        "bd": 0,
        "bg": "#003366",
        "fg": "#66ffff",
        "activebackground": "#004488",
        "activeforeground": "#66ffff",
        "cursor": "hand2"
    }
    
    # Темный стиль для CONVERT и HELP кнопок
    dark_button_style = {
        "font": ("Courier New", 9, "bold"),
        "width": 18,
        "height": 4,
        "relief": "flat",
        "bd": 0,
        "bg": "#001122",  # Более темный фон
        "fg": "#44ccff",  # Немного менее яркий цвет
        "activebackground": "#002244",  # Темнее при клике
        "activeforeground": "#66ffff",
        "cursor": "hand2"
    }
    
    # Все кнопки в одну горизонтальную линию
    buttons_row = tk.Frame(buttons_frame, bg="#002244")
    buttons_row.pack(expand=True)
    
    # Convert кнопка
    convert_btn = tk.Button(buttons_row, text="[01] CONVERT\nDATA\n─────────", 
                           command=run_convert_script,
                           **dark_button_style)
    convert_btn.pack(side=tk.LEFT, padx=3)
    
    # Visualization кнопка
    viz_btn = tk.Button(buttons_row, text="[02] VISUALIZATION\nCONNECTION\n─────────", 
                       command=lambda: run_script("_01_visualization.py"),
                       **hacker_button_style)
    viz_btn.pack(side=tk.LEFT, padx=3)
    
    # Daily кнопка
    daily_btn = tk.Button(buttons_row, text="[03] DAILY\nACTIVITIES\n─────────", 
                         command=lambda: run_script("_02_graphics.py"),
                         **hacker_button_style)
    daily_btn.pack(side=tk.LEFT, padx=3)
    
    # Group кнопка
    group_btn = tk.Button(buttons_row, text="[04] GROUP\nCONNECTIONS\n─────────", 
                         command=lambda: run_script("_03_group_connections.py"),
                         **hacker_button_style)
    group_btn.pack(side=tk.LEFT, padx=3)
    
    # Help кнопка
    help_btn = tk.Button(buttons_row, text="[05] HELP\nSYSTEM\n─────────", 
                        command=lambda: run_script("_04_help.py"),
                        **dark_button_style)
    help_btn.pack(side=tk.LEFT, padx=3)
    
    # Информация о путях к данным под кнопками (выровнено по левому краю первой кнопки)
    paths_frame = tk.Frame(main_frame, bg="#002244")
    paths_frame.pack(anchor="w", pady=(10, 0), padx=(110, 0))  # Выравнивание по левому краю первой кнопки
    






    # RAW data путь
    raw_data_label = tk.Label(paths_frame, text="RAW data SDRTrank", 
                             font=("Courier New", 8, "bold"), 
                             bg="#002244", fg="#66ffff")
    raw_data_label.pack(anchor="w", padx=(0, 0))
    
    # Фрейм для пути RAW data с кнопкой Browse
    raw_path_frame = tk.Frame(paths_frame, bg="#002244")
    raw_path_frame.pack(anchor="w", pady=(1, 3))
    
    raw_browse_btn = tk.Button(raw_path_frame, text="📁", 
                               font=("Arial", 10),
                               bg="#003366", fg="#66ffff",
                               relief="flat", bd=0,
                               cursor="hand2",
                               command=lambda: browse_folder(raw_path_var, raw_path_label_text))
    raw_browse_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    raw_path_label_text = tk.Label(raw_path_frame, textvariable=raw_path_var, 
                                   font=("Courier New", 7), 
                                   bg="#002244", fg="#88ccff")
    raw_path_label_text.pack(side=tk.LEFT)
    
    
    # Convert data путь
    convert_data_label = tk.Label(paths_frame, text="Convert data", 
                                 font=("Courier New", 8, "bold"), 
                                 bg="#002244", fg="#66ffff")
    convert_data_label.pack(anchor="w", padx=(0, 0))
    
    # Фрейм для пути Convert data с кнопкой Browse
    convert_path_frame = tk.Frame(paths_frame, bg="#002244")
    convert_path_frame.pack(anchor="w", pady=(1, 0))
    
    convert_browse_btn = tk.Button(convert_path_frame, text="📁", 
                                   font=("Arial", 10),
                                   bg="#003366", fg="#66ffff",
                                   relief="flat", bd=0,
                                   cursor="hand2",
                                   command=lambda: browse_folder(convert_path_var, convert_path_label_text))
    convert_browse_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    convert_path_label_text = tk.Label(convert_path_frame, textvariable=convert_path_var, 
                                       font=("Courier New", 7), 
                                       bg="#002244", fg="#88ccff")
    convert_path_label_text.pack(side=tk.LEFT)
    

    # Gap time поле ввода под информацией о путях (выровнено по левому краю первой кнопки)
    gap_time_frame = tk.Frame(main_frame, bg="#002244")
    gap_time_frame.pack(anchor="w", pady=(10, 0), padx=(110, 0))  # Выравнивание по левому краю первой кнопки
    
    gap_time_label = tk.Label(gap_time_frame, text="Gap time [0-60] sec", 
                             font=("Courier New", 8, "bold"), 
                             bg="#002244", fg="#66ffff")
    gap_time_label.pack(anchor="w", padx=(0, 0))  # Убираем отступы
    
    gap_time_entry = tk.Entry(gap_time_frame, textvariable=gap_time_var, 
                             font=("Courier New", 8), width=3, justify="center",
                             bg="#003366", fg="#66ffff", insertbackground="#66ffff",
                             relief="flat", bd=1)
    gap_time_entry.pack(anchor="w", pady=(2, 0), padx=(0, 0))  # Убираем отступы
    





    # Валидация ввода (только цифры от 0 до 60)
    def validate_gap_time(value):
        if value == "" or value.isdigit():
            num = int(value) if value else 0
            return 0 <= num <= 60
        return False
    
    gap_time_entry.config(validate="key", validatecommand=(gap_time_entry.register(validate_gap_time), "%P"))
    
    # Обработчик изменения gap_time
    def on_gap_time_change(*args):
        """Сохраняет gap_time в config.ini при изменении"""
        save_config(raw_path_var.get(), convert_path_var.get(), gap_time_var.get())
    
    gap_time_var.trace('w', on_gap_time_change)
    
    # Нижняя панель с терминальным промптом
    terminal_frame = tk.Frame(main_frame, bg="#002244")
    terminal_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    
    # Терминальный промпт
    terminal_prompt = tk.Label(terminal_frame, text="root@dmrscope:~$ ./start_analyze.sh --execute", 
                              font=("Courier New", 9), 
                              bg="#002244", fg="#66ffff")
    terminal_prompt.pack(side=tk.LEFT)
    
    # Мигающий курсор
    cursor_label = tk.Label(terminal_frame, text="█", 
                           font=("Courier New", 9), 
                           bg="#002244", fg="#66ffff")
    cursor_label.pack(side=tk.LEFT)
    
    # Анимация мигающего курсора
    def blink_cursor():
        if cursor_label.cget("fg") == "#66ffff":
            cursor_label.config(fg="#002244")
        else:
            cursor_label.config(fg="#66ffff")
        root.after(500, blink_cursor)
    
    blink_cursor()
    
    # Запускаем главный цикл
    root.mainloop()

def run_script(script_name):
    """Запуск указанного скрипта"""
    try:
        if os.path.exists(script_name):
            subprocess.Popen([sys.executable, script_name])
        else:
            messagebox.showerror("Ошибка", f"Файл {script_name} не найден!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить {script_name}:\n{str(e)}")

def run_convert_script():
    """Запуск конвертации в зависимости от значения gap_time"""
    try:
        gap_time_value = int(gap_time_var.get())
        
        if gap_time_value == 0:
            # Если gap_time = 0, запускаем _00_0_convert.py
            script_name = "_00_0_convert.py"
        else:
            # Если gap_time от 1 до 60, запускаем _00_3_convert.py
            script_name = "_00_3_convert.py"
        
        if os.path.exists(script_name):
            subprocess.Popen([sys.executable, script_name])
        else:
            messagebox.showerror("Ошибка", f"Файл {script_name} не найден!")
    except ValueError:
        messagebox.showerror("Ошибка", "Неверное значение gap_time! Должно быть число от 0 до 60.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить конвертацию:\n{str(e)}")

def show_help():
    """Показать справку"""
    help_text = """
START WINDOW - Главное окно запуска программ

Доступные программы:

1. Convert Data - Конвертация данных
2. Gap time [] - Обработка временных интервалов
3. Visualization Connection - Визуализация соединений
4. Daily Activities - Ежедневная активность
5. Group Connections - Группировка соединений
6. Help - Справка

Для запуска программы нажмите на соответствующую кнопку.
    """
    messagebox.showinfo("Справка", help_text)

if __name__ == "__main__":
    main()