import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from collections import defaultdict
import math
import os
from datetime import datetime, timedelta
import glob
import configparser

try:
    from tkcalendar import Calendar
except ImportError:
    Calendar = None

# PDF export libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ReportLab not installed. PDF export will be disabled.")
    print("Install with: pip install reportlab")


def load_data_directory():
    """Загрузить путь к директории convert_data из config.ini"""
    config = configparser.ConfigParser()
    config_file = 'config.ini'
    
    if os.path.exists(config_file):
        config.read(config_file)
        # Читаем convert_data из config.ini
        convert_path = config.get('PATHS', 'convert_data', fallback=r'C:\Users\dotignore\Documents\Python\examplaone_krakenSDR_web\data')
        # Преобразуем '/' на '\' для Windows
        convert_path = convert_path.replace('/', '\\')
        return convert_path
    else:
        # Если config.ini не найден, используем путь по умолчанию
        return r'C:\Users\dotignore\Documents\Python\examplaone_krakenSDR_web\data'


class DateMaskEntry(tk.Frame):
    """Widget for date input with mask DD/MM/YY HH:MM:SS and calendar"""
    def __init__(self, parent, textvariable=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.textvariable = textvariable
        
        # Frame for entry and button
        input_frame = tk.Frame(self)
        input_frame.pack(side=tk.LEFT)
        
        # Create Entry
        self.entry = tk.Entry(input_frame, width=17, font=("Courier", 9))
        self.entry.pack(side=tk.LEFT)
        
        # Calendar icon button
        self.cal_button = tk.Button(input_frame, text="📅", width=2, 
                                   command=self.show_calendar,
                                   font=("Arial", 10), cursor="hand2",
                                   relief=tk.FLAT, bg="#f5f5f5")
        self.cal_button.pack(side=tk.LEFT, padx=(2, 0))
        
        # Initial value
        self.entry.insert(0, "01/01/25 00:00:00")
        
        # Bind events
        self.entry.bind('<KeyPress>', self.on_key_press)
        self.entry.bind('<Left>', self.on_arrow_left)
        self.entry.bind('<Right>', self.on_arrow_right)
        
        # Separator positions
        self.separators = {2: '/', 5: '/', 8: ' ', 11: ':', 14: ':'}
        self.field_positions = [
            (0, 2),   # DD
            (3, 5),   # MM
            (6, 8),   # YY
            (9, 11),  # HH
            (12, 14), # MM
            (15, 17)  # SS
        ]
        
        # Synchronization with textvariable
        if self.textvariable:
            self.textvariable.trace('w', self.update_from_var)
            self.update_from_var()
    
    def on_arrow_left(self, event):
        """Handle left arrow key"""
        pos = self.entry.index(tk.INSERT)
        
        # Skip separators when moving left
        if pos > 0:
            pos -= 1
            if pos in self.separators:
                pos -= 1
            self.entry.icursor(pos)
        return 'break'
    
    def on_arrow_right(self, event):
        """Handle right arrow key"""
        pos = self.entry.index(tk.INSERT)
        
        # Skip separators when moving right
        if pos < 16:
            pos += 1
            if pos in self.separators:
                pos += 1
            self.entry.icursor(pos)
        return 'break'
    
    def on_key_press(self, event):
        """Handle key press events"""
        if event.char.isdigit():
            pos = self.entry.index(tk.INSERT)
            
            # Don't allow input at separator positions
            if pos in self.separators:
                return 'break'
            
            # Replace character at cursor position
            text = list(self.entry.get())
            if pos < len(text):
                text[pos] = event.char
                self.entry.delete(0, tk.END)
                self.entry.insert(0, ''.join(text))
                
                # Move cursor
                new_pos = pos + 1
                
                # Skip separator if needed
                if new_pos in self.separators:
                    new_pos += 1
                    
                # Check bounds
                if new_pos <= 16:
                    self.entry.icursor(new_pos)
                else:
                    self.entry.icursor(pos)
            
            # Update variable
            if self.textvariable:
                self.textvariable.set(self.entry.get())
                
            return 'break'
        
        elif event.keysym == 'BackSpace':
            pos = self.entry.index(tk.INSERT)
            if pos > 0 and pos - 1 not in self.separators:
                text = list(self.entry.get())
                text[pos - 1] = '0'
                self.entry.delete(0, tk.END)
                self.entry.insert(0, ''.join(text))
                self.entry.icursor(pos - 1)
            return 'break'
        
        elif event.keysym in ['Tab', 'Return']:
            return  # Allow standard behavior
        
        return 'break'
    
    def show_calendar(self):
        """Show calendar for date and time selection"""
        if not Calendar:
            print("tkcalendar not installed! Install: pip install tkcalendar")
            return
            
        cal_window = tk.Toplevel(self)
        cal_window.title("Select date and time")
        cal_window.geometry("320x520")
        cal_window.resizable(False, False)
        
        try:
            current_date_str = self.entry.get()
            current_date = datetime.strptime(current_date_str, "%d/%m/%y %H:%M:%S")
        except:
            current_date = datetime.now()
        
        # Main container
        main_container = tk.Frame(cal_window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Frame for calendar
        date_frame = tk.LabelFrame(main_container, text="Date", padx=10, pady=5)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        cal = Calendar(date_frame, selectmode='day',
                    year=current_date.year, 
                    month=current_date.month,
                    day=current_date.day,
                    date_pattern='dd/mm/yyyy')
        cal.pack()
        
        # Frame for time
        time_frame = tk.LabelFrame(main_container, text="Time (click to select)", padx=10, pady=5)
        time_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Variables for selected time
        selected_hour = tk.IntVar(value=current_date.hour)
        selected_min = tk.IntVar(value=current_date.minute)
        selected_sec = tk.IntVar(value=current_date.second)
        
        # Frame for displaying selected time
        selected_time_frame = tk.Frame(time_frame)
        selected_time_frame.pack(pady=5)
        
        hour_label = tk.Label(selected_time_frame, text=f"{selected_hour.get():02d}", 
                            font=("Courier", 16, "bold"), width=2, relief=tk.SUNKEN, bg="white")
        hour_label.grid(row=0, column=0, padx=2)
        
        tk.Label(selected_time_frame, text=":", font=("Courier", 16, "bold")).grid(row=0, column=1)
        
        min_label = tk.Label(selected_time_frame, text=f"{selected_min.get():02d}", 
                            font=("Courier", 16, "bold"), width=2, relief=tk.SUNKEN, bg="white")
        min_label.grid(row=0, column=2, padx=2)
        
        tk.Label(selected_time_frame, text=":", font=("Courier", 16, "bold")).grid(row=0, column=3)
        
        sec_label = tk.Label(selected_time_frame, text=f"{selected_sec.get():02d}", 
                            font=("Courier", 16, "bold"), width=2, relief=tk.SUNKEN, bg="white")
        sec_label.grid(row=0, column=4, padx=2)
        
        # Frame with three columns for time selection
        picker_frame = tk.Frame(time_frame)
        picker_frame.pack(fill=tk.X)
        
        # Hours column
        hour_frame = tk.Frame(picker_frame)
        hour_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(hour_frame, text="Hours", font=("Arial", 9)).pack()
        
        hour_listbox = tk.Listbox(hour_frame, height=4, width=4, font=("Courier", 10))
        hour_scroll = tk.Scrollbar(hour_frame, orient="vertical", command=hour_listbox.yview)
        hour_listbox.configure(yscrollcommand=hour_scroll.set)
        
        for i in range(24):
            hour_listbox.insert(tk.END, f"{i:02d}")
        
        hour_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        hour_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        hour_listbox.selection_set(current_date.hour)
        hour_listbox.see(current_date.hour)
        
        # Minutes column
        min_frame = tk.Frame(picker_frame)
        min_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(min_frame, text="Minutes", font=("Arial", 9)).pack()
        
        min_listbox = tk.Listbox(min_frame, height=4, width=4, font=("Courier", 10))
        min_scroll = tk.Scrollbar(min_frame, orient="vertical", command=min_listbox.yview)
        min_listbox.configure(yscrollcommand=min_scroll.set)
        
        for i in range(60):
            min_listbox.insert(tk.END, f"{i:02d}")
        
        min_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        min_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        min_listbox.selection_set(current_date.minute)
        min_listbox.see(current_date.minute)
        
        # Seconds column
        sec_frame = tk.Frame(picker_frame)
        sec_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(sec_frame, text="Seconds", font=("Arial", 9)).pack()
        
        sec_listbox = tk.Listbox(sec_frame, height=4, width=4, font=("Courier", 10))
        sec_scroll = tk.Scrollbar(sec_frame, orient="vertical", command=sec_listbox.yview)
        sec_listbox.configure(yscrollcommand=sec_scroll.set)
        
        for i in range(60):
            sec_listbox.insert(tk.END, f"{i:02d}")
        
        sec_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sec_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        sec_listbox.selection_set(current_date.second)
        sec_listbox.see(current_date.second)
        
        # Update functions on selection
        def on_hour_select(event):
            selection = hour_listbox.curselection()
            if selection:
                selected_hour.set(selection[0])
                hour_label.config(text=f"{selection[0]:02d}")
        
        def on_min_select(event):
            selection = min_listbox.curselection()
            if selection:
                selected_min.set(selection[0])
                min_label.config(text=f"{selection[0]:02d}")
        
        def on_sec_select(event):
            selection = sec_listbox.curselection()
            if selection:
                selected_sec.set(selection[0])
                sec_label.config(text=f"{selection[0]:02d}")
        
        hour_listbox.bind('<<ListboxSelect>>', on_hour_select)
        min_listbox.bind('<<ListboxSelect>>', on_min_select)
        sec_listbox.bind('<<ListboxSelect>>', on_sec_select)
        
        # Apply button
        def apply_datetime():
            date_str = cal.get_date()
            selected_date = datetime.strptime(date_str, '%d/%m/%Y')
            
            final_date = selected_date.replace(hour=selected_hour.get(), 
                                            minute=selected_min.get(), 
                                            second=selected_sec.get())
            date_formatted = final_date.strftime("%d/%m/%y %H:%M:%S")
            
            self.entry.delete(0, tk.END)
            self.entry.insert(0, date_formatted)
            
            if self.textvariable:
                self.textvariable.set(date_formatted)
            
            cal_window.destroy()
        
        # Control buttons
        button_frame = tk.Frame(cal_window, bg="#e0e0e0", height=60)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        button_frame.pack_propagate(False)
        
        ok_button = tk.Button(button_frame, 
                            text="✓ APPLY", 
                            command=apply_datetime,
                            bg="#4CAF50", 
                            fg="white", 
                            font=("Arial", 11, "bold"),
                            width=12,
                            height=2,
                            cursor="hand2")
        ok_button.pack(side=tk.LEFT, padx=20, pady=10)
        
        cancel_button = tk.Button(button_frame, 
                                text="✗ CANCEL", 
                                command=cal_window.destroy,
                                bg="#f44336", 
                                fg="white", 
                                font=("Arial", 11, "bold"),
                                width=12,
                                height=2,
                                cursor="hand2")
        cancel_button.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Make window modal
        cal_window.transient(self.winfo_toplevel())
        cal_window.grab_set()
        
        # Center window
        cal_window.update_idletasks()
        x = (cal_window.winfo_screenwidth() // 2) - (160)
        y = (cal_window.winfo_screenheight() // 2) - (260)
        cal_window.geometry(f"+{x}+{y}")

    def update_from_var(self, *args):
        """Update widget from variable"""
        value = self.textvariable.get()
        if value and len(value) == 17:
            current = self.entry.get()
            if current != value:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, value)
    
    def get(self):
        """Get value"""
        return self.entry.get()


class HourlyActivityVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("DMR Hourly Activity Visualization")
        self.root.geometry("1400x900")
        
        # Data directory
        self.data_directory = load_data_directory()
        
        # Load all .txt files from directory
        self.file_paths = self.get_all_txt_files()
        
        # Selected files (all by default)
        self.selected_files = set(range(len(self.file_paths)))
        
        # Sort variables for file selector
        self.sort_by_name = tk.StringVar(value="asc")  # asc, desc
        self.sort_by_sessions = tk.StringVar(value="none")  # asc, desc, none
        
        # Time interval for grouping sessions (in minutes)
        self.time_interval_minutes = tk.StringVar(value="60")  # Default: 60 minutes (1 hour)
        
        # Print info about loaded files
        print(f"Found {len(self.file_paths)} files in directory: {self.data_directory}")
        if self.file_paths:
            print("Files loaded:")
            for i, path in enumerate(self.file_paths[:10], 1):  # Show first 10
                print(f"  {i}. {os.path.basename(path)}")
            if len(self.file_paths) > 10:
                print(f"  ... and {len(self.file_paths) - 10} more files")
        else:
            print("No .txt files found in directory!")
        
        # Data storage
        self.file_data = []
        self.filtered_file_data = []
        self.hourly_data_by_file = {}
        
        # Filter variables
        self.date_from_var = tk.StringVar(value="01/01/25 00:00:00")
        self.date_to_var = tk.StringVar(value="31/12/25 23:59:59")
        self.duration_from_var = tk.StringVar(value="")
        self.duration_to_var = tk.StringVar(value="")
        self.selected_event = tk.StringVar(value="All")
        self.selected_timeslot = tk.StringVar(value="All")
        self.selected_color_code = tk.StringVar(value="All")
        self.selected_algorithm = tk.StringVar(value="All")
        self.selected_key = tk.StringVar(value="All")
        
        # Unique values for filters
        self.unique_events = set()
        self.unique_timeslots = set()
        self.unique_color_codes = set()
        self.unique_algorithms = set()
        self.unique_keys = set()

        self.unique_details = set()
        self.from_identifiers = {}
        self.to_identifiers = {}
        self.selected_details = set()
        self.selected_from_ids = set()
        self.selected_to_ids = set()
        
        # Color scheme
        self.bg_color = "#ffffff"
        self.text_color = "#000000"
        
        # Create interface
        self.setup_ui()
        
        # Load and display data
        self.load_all_data()
        self.draw_hourly_visualization()
    
    def get_all_txt_files(self):
        """Get all .txt files from the data directory"""
        try:
            # Use glob to find all .txt files
            pattern = os.path.join(self.data_directory, "*.txt")
            files = glob.glob(pattern)
            
            # Sort files alphabetically for consistent ordering
            files.sort()
            
            return files
        except Exception as e:
            print(f"Error loading files from directory: {e}")
            messagebox.showerror("Error", f"Failed to load files from directory:\n{self.data_directory}\n\nError: {e}")
            return []
    








    def setup_ui(self):
        """Create user interface"""
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top panel with buttons
        top_frame = tk.Frame(main_frame, bg=self.bg_color, height=40)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)
        
        # Button panel
        button_panel = tk.Frame(top_frame, bg=self.bg_color)
        button_panel.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Info label showing number of files
        info_label = tk.Label(button_panel, 
                            text=f"Files loaded: {len(self.file_paths)}", 
                            bg=self.bg_color,
                            font=("Arial", 9))
        info_label.pack(side=tk.LEFT, padx=10)
        
        refresh_btn = tk.Button(button_panel, text="Refresh", command=self.refresh_all,
                            bg="#e0e0e0", relief=tk.RAISED, bd=1)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(button_panel, text="Export Report", command=self.export_report,
                            bg="#2196F3", fg="white", relief=tk.RAISED, bd=1)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # PDF Export button
        if REPORTLAB_AVAILABLE:
            export_pdf_btn = tk.Button(button_panel, text="Export PDF", command=self.export_to_pdf,
                                    bg="#FF5722", fg="white", relief=tk.RAISED, bd=1)
            export_pdf_btn.pack(side=tk.LEFT, padx=5)
        
        # Horizontal container
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left filter panel
        filter_frame = tk.Frame(content_frame, bg="#f5f5f5", width=200)
        filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        filter_frame.pack_propagate(False)
        
        # Container for filters
        filter_content = tk.Frame(filter_frame, bg="#f5f5f5")
        filter_content.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # FILE SELECTION BUTTON
        file_select_frame = tk.Frame(filter_content, bg="#f5f5f5")
        file_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.select_files_button = tk.Button(file_select_frame, text="SELECT FILES", 
                                        command=self.open_file_selector,
                                        bg="#2196F3", fg="white",
                                        font=("Arial", 10, "bold"),
                                        relief=tk.RAISED, bd=2,
                                        cursor="hand2", width=15)
        self.select_files_button.pack(fill=tk.X)
        
        # DURATION FILTER
        duration_frame = tk.Frame(filter_content, bg="#f5f5f5")
        duration_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(duration_frame, text="DURATION", bg="#f5f5f5", 
                fg=self.text_color, font=("Arial", 9, "bold")).pack()
        
        dur_from_frame = tk.Frame(duration_frame, bg="#f5f5f5")
        dur_from_frame.pack(fill=tk.X, pady=2)
        tk.Label(dur_from_frame, text="From:", bg="#f5f5f5", width=7).pack(side=tk.LEFT)
        tk.Entry(dur_from_frame, textvariable=self.duration_from_var, width=10).pack(side=tk.LEFT)
        tk.Label(dur_from_frame, text="sec", bg="#f5f5f5", font=("Arial", 9)).pack(side=tk.LEFT, padx=(2, 0))
        
        dur_to_frame = tk.Frame(duration_frame, bg="#f5f5f5")
        dur_to_frame.pack(fill=tk.X, pady=2)
        tk.Label(dur_to_frame, text="To:", bg="#f5f5f5", width=7).pack(side=tk.LEFT)
        tk.Entry(dur_to_frame, textvariable=self.duration_to_var, width=10).pack(side=tk.LEFT)
        tk.Label(dur_to_frame, text="sec", bg="#f5f5f5", font=("Arial", 9)).pack(side=tk.LEFT, padx=(2, 0))
        
        # EVENT FILTER
        event_frame = tk.Frame(filter_content, bg="#f5f5f5")
        event_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(event_frame, text="EVENT", bg="#f5f5f5", 
                fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.event_combo = ttk.Combobox(event_frame, textvariable=self.selected_event, 
                                    state="readonly", width=20)
        self.event_combo.pack()
        
        # TIMESLOT FILTER
        timeslot_frame = tk.Frame(filter_content, bg="#f5f5f5")
        timeslot_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(timeslot_frame, text="TIMESLOT", bg="#f5f5f5", 
                fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.timeslot_combo = ttk.Combobox(timeslot_frame, textvariable=self.selected_timeslot, 
                                        state="readonly", width=20)
        self.timeslot_combo.pack()
        
        # COLOR CODE FILTER
        color_frame = tk.Frame(filter_content, bg="#f5f5f5")
        color_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(color_frame, text="COLOR CODE", bg="#f5f5f5", 
                fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.color_combo = ttk.Combobox(color_frame, textvariable=self.selected_color_code, 
                                    state="readonly", width=20)
        self.color_combo.pack()
        
        # ALGORITHM FILTER
        algorithm_frame = tk.Frame(filter_content, bg="#f5f5f5")
        algorithm_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(algorithm_frame, text="ALGORITHM", bg="#f5f5f5", 
                        fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.algorithm_combo = ttk.Combobox(algorithm_frame, textvariable=self.selected_algorithm, 
                                        state="readonly", width=20)
        self.algorithm_combo.pack()
        
        # KEY FILTER
        key_frame = tk.Frame(filter_content, bg="#f5f5f5")
        key_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(key_frame, text="KEY", bg="#f5f5f5", 
                fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.key_combo = ttk.Combobox(key_frame, textvariable=self.selected_key, 
                                state="readonly", width=20)
        self.key_combo.pack()
        
        # DATE FILTER
        date_filter_frame = tk.Frame(filter_content, bg="#f5f5f5")
        date_filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # "From" field with mask
        from_frame = tk.Frame(date_filter_frame, bg="#f5f5f5")
        from_frame.pack(fill=tk.X, pady=2)
        
        from_label = tk.Label(from_frame, text="From:", bg="#f5f5f5", 
                            fg=self.text_color, font=("Arial", 9), width=5)
        from_label.pack(side=tk.LEFT)
        
        self.date_from_entry = DateMaskEntry(from_frame, textvariable=self.date_from_var,
                                            bg="#f5f5f5")
        self.date_from_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # "To" field with mask
        to_frame = tk.Frame(date_filter_frame, bg="#f5f5f5")
        to_frame.pack(fill=tk.X, pady=2)
        
        to_label = tk.Label(to_frame, text="To:", bg="#f5f5f5",
                        fg=self.text_color, font=("Arial", 9), width=5)
        to_label.pack(side=tk.LEFT)
        
        self.date_to_entry = DateMaskEntry(to_frame, textvariable=self.date_to_var,
                                        bg="#f5f5f5")
        self.date_to_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # APPLY and CLEAR FILTER buttons after date fields
        apply_frame = tk.Frame(date_filter_frame, bg="#f5f5f5")
        apply_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.apply_button = tk.Button(apply_frame, text="APPLY", 
                                    command=self.apply_filters,
                                    bg="#4CAF50", fg="white",
                                    font=("Arial", 10, "bold"),
                                    relief=tk.RAISED, bd=2,
                                    cursor="hand2", width=15)
        self.apply_button.pack(fill=tk.X)
        
        # Clear Filter button
        self.clear_button = tk.Button(apply_frame, text="CLEAR FILTER", 
                                    command=self.clear_filters,
                                    bg="#f44336", fg="white",
                                    font=("Arial", 10, "bold"),
                                    relief=tk.RAISED, bd=2,
                                    cursor="hand2", width=15)
        self.clear_button.pack(fill=tk.X, pady=(5, 0))
        
        # Filter status
        self.filter_status = tk.Label(apply_frame, text="No filter applied",
                                    bg="#f5f5f5", fg="#606060",
                                    font=("Arial", 8))
        self.filter_status.pack(pady=(5, 0))
        
        # TIME INTERVAL SETTING (moved to bottom)
        interval_frame = tk.Frame(filter_content, bg="#f5f5f5")
        interval_frame.pack(fill=tk.X, pady=(150, 0))
        
        tk.Label(interval_frame, text="TIME INTERVAL", bg="#f5f5f5", 
                fg=self.text_color, font=("Arial", 9, "bold")).pack()
        
        interval_input_frame = tk.Frame(interval_frame, bg="#f5f5f5")
        interval_input_frame.pack(fill=tk.X, pady=5)
        
        # Minutes input with better visibility
        minutes_label = tk.Label(interval_input_frame, text="Minutes:", bg="#f5f5f5", 
                               fg="#333333", font=("Arial", 9), width=8)
        minutes_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.interval_entry = tk.Entry(interval_input_frame, textvariable=self.time_interval_minutes, 
                                     width=8, font=("Arial", 9), relief=tk.SUNKEN, bd=1)
        self.interval_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        min_label = tk.Label(interval_input_frame, text="min", bg="#f5f5f5", 
                           fg="#666666", font=("Arial", 9))
        min_label.pack(side=tk.LEFT)
        
        # Default value label
        default_interval_label = tk.Label(interval_frame, text="Default: 60 min (range: 1-1440)", 
                                        bg="#f5f5f5", fg="#666666",
                                        font=("Arial", 8, "italic"))
        default_interval_label.pack(pady=(2, 0))
        
        # Debug: Print interval value
        print(f"TIME INTERVAL field created with value: {self.time_interval_minutes.get()}")
        
        # APPLY INTERVAL button
        apply_interval_frame = tk.Frame(filter_content, bg="#f5f5f5")
        apply_interval_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.apply_interval_button = tk.Button(apply_interval_frame, text="APPLY INTERVAL", 
                                              command=self.apply_interval,
                                              bg="#FF9800", fg="white",
                                              font=("Arial", 10, "bold"),
                                              relief=tk.RAISED, bd=2,
                                              cursor="hand2", width=15)
        self.apply_interval_button.pack(fill=tk.X)
        
        v_separator = tk.Frame(content_frame, width=1, bg="#d0d0d0")
        v_separator.pack(side=tk.LEFT, fill=tk.Y)
        
        # Canvas with scrolling for visualization
        canvas_frame = tk.Frame(content_frame, bg=self.bg_color)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.bg_color,
                            yscrollcommand=v_scroll.set,
                            xscrollcommand=h_scroll.set,
                            highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            # Вертикальная прокрутка
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def on_shift_mousewheel(event):
            # Горизонтальная прокрутка при зажатом Shift
            self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        
        # Windows и MacOS
        self.canvas.bind("<MouseWheel>", on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", on_shift_mousewheel)
        
        # Linux
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind("<Shift-Button-4>", lambda e: self.canvas.xview_scroll(-1, "units"))
        self.canvas.bind("<Shift-Button-5>", lambda e: self.canvas.xview_scroll(1, "units"))
        
        v_scroll.config(command=self.canvas.yview)
        h_scroll.config(command=self.canvas.xview)











    
    def parse_date(self, date_str):
        """Parse date from format DD/MM/YY HH:MM:SS"""
        try:
            return datetime.strptime(date_str, "%d/%m/%y %H:%M:%S")
        except:
            return None
    
    def parse_timestamp(self, timestamp_str):
        """Parse timestamp from format YYYY:MM:DD:HH:MM:SS"""
        try:
            return datetime.strptime(timestamp_str, "%Y:%m:%d:%H:%M:%S")
        except:
            return None
    
    def get_visualization_symbol(self, count):
        """Get visualization symbol based on session count"""
        if count == 0:
            return ' '
        elif count <= 3:
            return '░'
        elif count <= 6:
            return '▒'
        elif count <= 9:
            return '▓'
        else:
            # For 10+ use blocks of 10
            full_blocks = count // 10
            remainder = count % 10
            
            result = '█' * full_blocks
            
            if remainder > 0:
                if remainder <= 3:
                    result += '░'
                elif remainder <= 6:
                    result += '▒'
                else:
                    result += '▓'
            
            return result













    def load_all_data(self):
        """Load data from all files"""
        self.file_data.clear()
        self.filtered_file_data.clear()
        self.hourly_data_by_file.clear()
        
        # Clear unique values
        self.unique_events.clear()
        self.unique_timeslots.clear()
        self.unique_color_codes.clear()
        self.unique_algorithms.clear()
        self.unique_keys.clear()
        self.unique_details.clear()
        self.from_identifiers.clear()
        self.to_identifiers.clear()
        
        # Progress indicator for large datasets
        total_files = len(self.file_paths)
        print(f"Loading {total_files} files...")
        
        for idx, file_path in enumerate(self.file_paths):
            if idx % 10 == 0 and idx > 0:
                print(f"  Loaded {idx}/{total_files} files...")
            
            data = self.load_file_data(file_path)
            if data:
                self.file_data.append(data)
                
                # Collect unique values
                self.unique_events.update(data.get('events', set()))
                self.unique_timeslots.update(data.get('timeslots', set()))
                self.unique_color_codes.update(data.get('color_codes', set()))
                self.unique_algorithms.update(data.get('algorithms', set()))
                self.unique_keys.update(data.get('keys', set()))
                self.unique_details.update(data.get('details', set()))
                
                # Count FROM and TO identifiers
                for from_id in data.get('from_ids', set()):
                    if from_id not in self.from_identifiers:
                        self.from_identifiers[from_id] = 0
                    self.from_identifiers[from_id] += 1
                
                for to_id in data.get('to_ids', set()):
                    if to_id not in self.to_identifiers:
                        self.to_identifiers[to_id] = 0
                    self.to_identifiers[to_id] += 1
        
        print(f"Successfully loaded {len(self.file_data)} files")
        
        # Initialize selected IDs with all identifiers by default
        if not self.selected_from_ids:
            self.selected_from_ids = set(self.from_identifiers.keys())
        if not self.selected_to_ids:
            self.selected_to_ids = set(self.to_identifiers.keys())
        
        # Update comboboxes
        self.update_comboboxes()
        
        # Set date range from data
        self.set_date_range_from_data()











    
    def load_file_data(self, file_path):
        """Load data from one file and count hourly sessions"""
        hourly_sessions = defaultdict(int)
        all_records = []
        
        # Unique values for filters
        events = set()
        timeslots = set()
        color_codes = set()
        algorithms = set()
        keys = set()
        details = set()  # Добавляем details
        from_ids = set()  # Добавляем FROM идентификаторы
        to_ids = set()    # Добавляем TO идентификаторы
        
        # Extract frequency
        frequency = "Unknown"
        try:
            filename = os.path.basename(file_path)
            if '-' in filename:
                parts = filename.replace('.txt', '').split('-')
                if len(parts) == 3:
                    freq_mhz = parts[0]
                    freq_khz = parts[1] + parts[2]
                    frequency = f"{freq_mhz}.{freq_khz} MHz"
        except:
            pass
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line for line in file if not line.startswith('#')]
            
            csv_reader = csv.DictReader(lines)
            
            for row in csv_reader:
                # Read all fields
                timestamp_str = row.get('TIMESTAMP', '').strip()
                duration_ms = row.get('DURATION_MS', '').strip()
                event = row.get('EVENT', '').strip()
                timeslot = row.get('TIMESLOT', '').strip()
                color_code = row.get('COLOR_CODE', '').strip()
                algorithm = row.get('ALGORITHM', '').strip()
                key = row.get('KEY', '').strip()
                from_id = row.get('FROM', '').strip()
                to_id = row.get('TO', '').strip()
                detail = row.get('DETAILS', '').strip()  # Добавляем DETAILS
                
                # Collect unique values
                if event:
                    events.add(event)
                if timeslot:
                    timeslots.add(timeslot)
                if color_code:
                    color_codes.add(color_code)
                if algorithm:
                    algorithms.add(algorithm)
                if key:
                    keys.add(key)
                if detail:
                    details.add(detail)
                if from_id:
                    from_ids.add(from_id)
                if to_id:
                    to_ids.add(to_id)
                
                # Parse timestamp
                timestamp = None
                if timestamp_str:
                    timestamp_str = timestamp_str.strip('"')
                    timestamp = self.parse_timestamp(timestamp_str)
                
                if timestamp:
                    # Count session in the appropriate time interval
                    try:
                        interval_minutes = int(self.time_interval_minutes.get())
                        if interval_minutes < 1 or interval_minutes > 1440:
                            interval_minutes = 60  # Default to 60 minutes if invalid
                    except:
                        interval_minutes = 60  # Default to 60 minutes if error
                    
                    # Calculate which time interval this session belongs to
                    total_minutes = timestamp.hour * 60 + timestamp.minute
                    interval_index = total_minutes // interval_minutes
                    hourly_sessions[interval_index] += 1
                
                # Store complete record including FROM and TO
                all_records.append({
                    'timestamp': timestamp,
                    'duration_ms': duration_ms,
                    'event': event,
                    'timeslot': timeslot,
                    'color_code': color_code,
                    'algorithm': algorithm,
                    'key': key,
                    'from_id': from_id,
                    'to_id': to_id,
                    'details': detail
                })
            
            # Store hourly data for this file
            self.hourly_data_by_file[file_path] = dict(hourly_sessions)
            
            return {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'frequency': frequency,
                'hourly_sessions': dict(hourly_sessions),
                'all_records': all_records,
                'events': events,
                'timeslots': timeslots,
                'color_codes': color_codes,
                'algorithms': algorithms,
                'keys': keys,
                'details': details,
                'from_ids': from_ids,
                'to_ids': to_ids
            }
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

























    def update_comboboxes(self):
        """Update comboboxes with unique values"""
        # EVENT
        event_values = ['All'] + sorted(self.unique_events)
        self.event_combo['values'] = event_values
        if self.selected_event.get() not in event_values:
            self.selected_event.set('All')
        
        # TIMESLOT
        timeslot_values = ['All'] + sorted(self.unique_timeslots)
        self.timeslot_combo['values'] = timeslot_values
        if self.selected_timeslot.get() not in timeslot_values:
            self.selected_timeslot.set('All')
        
        # COLOR CODE
        color_values = ['All'] + sorted(self.unique_color_codes)
        self.color_combo['values'] = color_values
        if self.selected_color_code.get() not in color_values:
            self.selected_color_code.set('All')
        
        # ALGORITHM
        algorithm_values = ['All'] + sorted(self.unique_algorithms)
        self.algorithm_combo['values'] = algorithm_values
        if self.selected_algorithm.get() not in algorithm_values:
            self.selected_algorithm.set('All')
        
        # KEY
        key_values = ['All'] + sorted(self.unique_keys)
        self.key_combo['values'] = key_values
        if self.selected_key.get() not in key_values:
            self.selected_key.set('All')
    
    def set_date_range_from_data(self):
        """Set date range based on loaded data"""
        min_date = None
        max_date = None
        
        for data in self.file_data:
            for record in data.get('all_records', []):
                if record['timestamp']:
                    if min_date is None or record['timestamp'] < min_date:
                        min_date = record['timestamp']
                    if max_date is None or record['timestamp'] > max_date:
                        max_date = record['timestamp']
        
        if min_date and max_date:
            from_str = min_date.strftime("%d/%m/%y %H:%M:%S")
            to_str = max_date.strftime("%d/%m/%y %H:%M:%S")
            
            self.date_from_var.set(from_str)
            self.date_to_var.set(to_str)
    













    def apply_filters(self):
        """Apply filters to data"""
        date_from_str = self.date_from_var.get()
        date_to_str = self.date_to_var.get()
        
        date_from = self.parse_date(date_from_str)
        date_to = self.parse_date(date_to_str)
        
        if not date_from or not date_to:
            self.filter_status.config(text="Invalid date format", fg="red")
            return
        
        # Get filter values
        duration_from = self.duration_from_var.get()
        duration_to = self.duration_to_var.get()
        event_filter = self.selected_event.get()
        timeslot_filter = self.selected_timeslot.get()
        color_code_filter = self.selected_color_code.get()
        algorithm_filter = self.selected_algorithm.get()
        key_filter = self.selected_key.get()
        
        # Convert duration from seconds to milliseconds
        try:
            dur_from_ms = float(duration_from) * 1000 if duration_from else None
            dur_to_ms = float(duration_to) * 1000 if duration_to else None
        except:
            dur_from_ms = dur_to_ms = None
        
        # Filter data
        self.filtered_file_data = []
        total_filtered = 0
        total_sessions = 0
        
        for data in self.file_data:
            filtered_hourly = defaultdict(int)
            filtered_records = []
            
            for record in data['all_records']:
                total_sessions += 1
                passes_filter = True
                
                # Filter by date
                if record['timestamp']:
                    if not (date_from <= record['timestamp'] <= date_to):
                        passes_filter = False
                else:
                    passes_filter = False
                
                # Filter by duration
                if dur_from_ms is not None or dur_to_ms is not None:
                    try:
                        duration_ms = float(record['duration_ms']) if record['duration_ms'] else 0
                        if dur_from_ms is not None and duration_ms < dur_from_ms:
                            passes_filter = False
                        if dur_to_ms is not None and duration_ms > dur_to_ms:
                            passes_filter = False
                    except:
                        passes_filter = False
                
                # Filter by EVENT
                if event_filter != 'All' and record['event'] != event_filter:
                    passes_filter = False
                
                # Filter by TIMESLOT
                if timeslot_filter != 'All' and record['timeslot'] != timeslot_filter:
                    passes_filter = False
                
                # Filter by COLOR_CODE
                if color_code_filter != 'All' and record['color_code'] != color_code_filter:
                    passes_filter = False
                
                # Filter by ALGORITHM
                if algorithm_filter != 'All' and record['algorithm'] != algorithm_filter:
                    passes_filter = False
                
                # Filter by KEY
                if key_filter != 'All' and record['key'] != key_filter:
                    passes_filter = False
                
                # ВОТ СЮДА ДОБАВЬТЕ ЭТИ НОВЫЕ ФИЛЬТРЫ:
                # Filter by FROM identifier
                if self.selected_from_ids and record.get('from_id') not in self.selected_from_ids:
                    passes_filter = False
                
                # Filter by TO identifier  
                if self.selected_to_ids and record.get('to_id') not in self.selected_to_ids:
                    passes_filter = False
                
                # Filter by DETAILS
                if self.selected_details and record.get('details') not in self.selected_details:
                    passes_filter = False
                
                if passes_filter:
                    filtered_records.append(record)
                    if record['timestamp']:
                        # Use the same time interval logic as in load_file_data
                        try:
                            interval_minutes = int(self.time_interval_minutes.get())
                            if interval_minutes < 1 or interval_minutes > 1440:
                                interval_minutes = 60
                        except:
                            interval_minutes = 60
                        
                        total_minutes = record['timestamp'].hour * 60 + record['timestamp'].minute
                        interval_index = total_minutes // interval_minutes
                        filtered_hourly[interval_index] += 1
                    total_filtered += 1
        
           
            filtered_data = {
                'file_path': data['file_path'],
                'filename': data['filename'],
                'frequency': data['frequency'],
                'hourly_sessions': dict(filtered_hourly),
                'all_records': filtered_records
            }
            self.filtered_file_data.append(filtered_data)
        
        # Update status
        percent = int((total_filtered / total_sessions) * 100) if total_sessions > 0 else 0
        self.filter_status.config(
            text=f"Filtered: {total_filtered}/{total_sessions} ({percent}%)",
            fg="green" if total_filtered > 0 else "orange"
        )
        
        # Redraw with filtered data
        self.draw_hourly_visualization(use_filtered=True)
    





















    def clear_filters(self):
        """Clear all filters"""
        self.filtered_file_data = []
        
        # Reset filter values
        self.duration_from_var.set("")
        self.duration_to_var.set("")
        self.selected_event.set("All")
        self.selected_timeslot.set("All")
        self.selected_color_code.set("All")
        self.selected_algorithm.set("All")
        self.selected_key.set("All")
        
        # Update status
        self.filter_status.config(text="No filter applied", fg="#606060")
        
        # Redraw without filters
        self.draw_hourly_visualization(use_filtered=False)
    
    def apply_interval(self):
        """Apply new time interval and reload data"""
        try:
            interval_value = int(self.time_interval_minutes.get())
            if interval_value < 1 or interval_value > 1440:
                messagebox.showwarning("Invalid Interval", "Time interval must be between 1 and 1440 minutes")
                return
        except ValueError:
            messagebox.showwarning("Invalid Interval", "Please enter a valid number for time interval")
            return
        
        # Reload data with new interval
        self.load_all_data()
        
        # Update status - removed green status message
        
        # Redraw visualization
        self.draw_hourly_visualization(use_filtered=False)
    
 
 




    def draw_hourly_visualization(self, use_filtered=False):
        """Draw hourly activity visualization"""
        self.canvas.delete("all")
        
        # Choose data to display
        data_to_draw = self.filtered_file_data if use_filtered and self.filtered_file_data else self.file_data
        
        # Filter by selected files
        data_to_draw = [data for idx, data in enumerate(data_to_draw) if idx in self.selected_files]
        
        # НОВОЕ: Сортировка - файлы с данными первыми, без данных в конце
        files_with_data = []
        files_without_data = []
        
        for data in data_to_draw:
            # Проверяем есть ли записи с датами
            has_data = False
            for record in data.get('all_records', []):
                if record.get('timestamp'):
                    has_data = True
                    break
            
            if has_data:
                files_with_data.append(data)
            else:
                files_without_data.append(data)
        
        # Объединяем: сначала с данными, потом без
        data_to_draw = files_with_data + files_without_data
        
        if not data_to_draw:
            self.canvas.create_text(400, 200, text="No files selected", 
                                font=("Arial", 14), fill=self.text_color)
            return
        
        # Starting position
        y_offset = 20
        x_offset = 20
        chart_width = 800
        bar_height = 20
        
        # 10 muted colors palette
        color_palette = [
            "#E8D5C4",  # Light beige (oldest)
            "#D4C5B9",  # Warm gray
            "#C7B5A3",  # Light brown
            "#B8A598",  # Muted tan
            "#A8958F",  # Dusty rose
            "#968684",  # Mauve gray
            "#827678",  # Muted purple
            "#6F676B",  # Dark gray blue
            "#5C585E",  # Charcoal blue
            "#4A4952"   # Dark slate (newest)
        ]
        
        # Draw data for each file
        for file_data in data_to_draw:
            # Organize records by date
            records_by_date = defaultdict(list)
            for record in file_data.get('all_records', []):
                if record['timestamp']:
                    date_key = record['timestamp'].date()
                    records_by_date[date_key].append(record)
            
            # Calculate hourly sessions for each date
            daily_hourly_data = {}
            for date, records in records_by_date.items():
                hourly_counts = defaultdict(int)
                for record in records:
                    # Use the same time interval logic
                    try:
                        interval_minutes = int(self.time_interval_minutes.get())
                        if interval_minutes < 1 or interval_minutes > 1440:
                            interval_minutes = 60
                    except:
                        interval_minutes = 60
                    
                    total_minutes = record['timestamp'].hour * 60 + record['timestamp'].minute
                    interval_index = total_minutes // interval_minutes
                    hourly_counts[interval_index] += 1
                daily_hourly_data[date] = dict(hourly_counts)
            
            # Check if file has any records
            total = sum(len(records) for records in records_by_date.values())
            
            if total == 0:
                # Display "no records" message for empty files
                self.canvas.create_text(x_offset, y_offset, 
                                    text=f"File: {file_data['filename']} - no records",
                                    font=("Arial", 11, "bold"), anchor="w", fill="#999999")
                y_offset += 25
                
                # Separator
                self.canvas.create_line(x_offset, y_offset, x_offset + chart_width + 200, y_offset,
                                    fill="#cccccc")
                y_offset += 20
                continue
            
            # File header for files with data
            self.canvas.create_text(x_offset, y_offset, 
                                text=f"File: {file_data['filename']}",
                                font=("Arial", 11, "bold"), anchor="w")
            y_offset += 20
            
            self.canvas.create_text(x_offset, y_offset,
                                text=f"Frequency: {file_data['frequency']}",
                                font=("Arial", 10), anchor="w")
            y_offset += 25
            
            # Sort dates (oldest first so they draw at bottom)
            sorted_dates = sorted(daily_hourly_data.keys())
            num_days = len(sorted_dates)
            
            # Calculate max count for scaling across all days
            max_count = 1
            for hourly_data in daily_hourly_data.values():
                if hourly_data:
                    max_count = max(max_count, max(hourly_data.values()))
            
            # Bar parameters
            base_bar_height = 10  # Height of each day's bar
            bar_vertical_offset = 10  # How much each day is offset vertically
            interval_spacing = 15 + (num_days - 1) * bar_vertical_offset  # Total space per interval
            
            # Draw horizontal overlapping bar chart
            chart_start_y = y_offset
            
            # Calculate time intervals based on user setting
            try:
                interval_minutes = int(self.time_interval_minutes.get())
                if interval_minutes < 1 or interval_minutes > 1440:
                    interval_minutes = 60
            except:
                interval_minutes = 60
            
            # Calculate number of intervals per day
            intervals_per_day = 1440 // interval_minutes  # 1440 minutes in a day
            
            # Draw grid lines
            bar_x = x_offset + 60
            for i in range(5):  # Draw vertical grid lines
                grid_x = bar_x + (chart_width * i / 4)
                self.canvas.create_line(grid_x, chart_start_y - 5, 
                                    grid_x, chart_start_y + intervals_per_day * (base_bar_height + interval_spacing) + num_days * bar_vertical_offset,
                                    fill="#e0e0e0", dash=(2, 2))
            
            for interval in range(intervals_per_day):
                hour_base_y = chart_start_y + interval * (base_bar_height + interval_spacing)
                
                # Calculate time for this interval
                start_minutes = interval * interval_minutes
                start_hour = start_minutes // 60
                start_minute = start_minutes % 60
                
                # Interval label (positioned at center of all bars for this interval)
                label_y = hour_base_y + (num_days * bar_vertical_offset) // 2 + base_bar_height // 2
                self.canvas.create_text(x_offset, label_y,
                                    text=f"{start_hour:02d}:{start_minute:02d}",
                                    font=("Courier", 9), anchor="w")
                
                # Draw bars for each day (oldest at bottom, newest on top)
                for day_index, date in enumerate(sorted_dates):
                    hourly_data = daily_hourly_data[date]
                    count = hourly_data.get(interval, 0)
                    
                    # Calculate vertical position - older days lower, newer days higher
                    bar_y = hour_base_y + (num_days - 1 - day_index) * bar_vertical_offset
                    
                    # Choose color based on age - 10 muted colors gradient
                    if num_days <= 10:
                        # Direct mapping for 10 or fewer days
                        color_index = day_index * (len(color_palette) - 1) // max(num_days - 1, 1)
                        color = color_palette[color_index]
                    else:
                        # For more than 10 days, interpolate
                        color_index = day_index * 9 // (num_days - 1)
                        color = color_palette[color_index]
                    
                    z_order = day_index + 1  # Higher index = draw on top
                    
                    # Draw background for this bar
                    self.canvas.create_rectangle(bar_x, bar_y, 
                                                bar_x + chart_width, bar_y + base_bar_height,
                                                fill="#f8f8f8", outline="#f0f0f0", width=0.5,
                                                tags=f"bg_day_{day_index}")
                    
                    # Draw data bar if count > 0
                    if count > 0:
                        bar_width = (count / max_count) * chart_width
                        self.canvas.create_rectangle(
                            bar_x, 
                            bar_y,
                            bar_x + bar_width, 
                            bar_y + base_bar_height,
                            fill=color, outline="",
                            tags=f"bar_day_{day_index}"
                        )
                
                # Draw counts vertically for each day on the right
                count_x = bar_x + chart_width + 10
                for day_index, date in enumerate(sorted_dates):
                    count = daily_hourly_data[date].get(interval, 0)
                    if count > 0:  # Only show non-zero counts
                        # Position each count vertically aligned with its bar
                        count_y = hour_base_y + (num_days - 1 - day_index) * bar_vertical_offset + base_bar_height // 2
                        self.canvas.create_text(count_x, count_y,
                                            text=str(count),
                                            font=("Courier", 9), anchor="w")
            
            # Calculate where the chart ended
            y_offset = chart_start_y + intervals_per_day * (base_bar_height + interval_spacing) + 20
            
            # Date legend - simplified to show only color and date
            if len(sorted_dates) > 1:
                y_offset += 10
                
                # Show dates horizontally
                legend_x = x_offset
                for day_index, date in enumerate(sorted_dates):
                    # Match the colors from the chart - same 10 color palette
                    if num_days <= 10:
                        # Direct mapping for 10 or fewer days
                        color_index = day_index * (len(color_palette) - 1) // max(num_days - 1, 1)
                        color = color_palette[color_index]
                    else:
                        # For more than 10 days, interpolate
                        color_index = day_index * 9 // (num_days - 1)
                        color = color_palette[color_index]
                    
                    date_str = date.strftime("%Y-%m-%d")
                    
                    # Color box
                    self.canvas.create_rectangle(legend_x, y_offset,
                                                legend_x + 15, y_offset + 15,
                                                fill=color, outline="black")
                    
                    # Date only
                    self.canvas.create_text(legend_x + 20, y_offset + 7,
                                        text=date_str,
                                        font=("Arial", 9), anchor="w")
                    legend_x += 120  # Move to next column (smaller spacing)
                    
                    # Break to new line if needed
                    if (day_index + 1) % 6 == 0:  # 6 items per row (more compact)
                        y_offset += 20
                        legend_x = x_offset
                
                if len(sorted_dates) % 6 != 0:
                    y_offset += 20
            else:
                # Single day - show date
                if sorted_dates:
                    date = sorted_dates[0]
                    self.canvas.create_text(x_offset, y_offset,
                                        text=f"Date: {date.strftime('%Y-%m-%d')}",
                                        font=("Arial", 9), anchor="w")
                    y_offset += 15
            
            # Statistics
            y_offset += 10
            if total > 0:
                self.canvas.create_text(x_offset, y_offset,
                                    text=f"Total sessions: {total}",
                                    font=("Arial", 10, "bold"), anchor="w")
                y_offset += 15
                
                # Find overall peak hour across all days
                combined_hourly = defaultdict(int)
                for hourly_data in daily_hourly_data.values():
                    for hour, count in hourly_data.items():
                        combined_hourly[hour] += count
                
                if combined_hourly:
                    max_hour = max(combined_hourly, key=combined_hourly.get)
                    avg_sessions = total / (24 * len(sorted_dates)) if sorted_dates else 0
                    
                    self.canvas.create_text(x_offset, y_offset,
                                        text=f"Peak hour (overall): {max_hour:02d}:00 ({combined_hourly[max_hour]} sessions)",
                                        font=("Arial", 9), anchor="w")
                    y_offset += 15
                    
                    self.canvas.create_text(x_offset, y_offset,
                                        text=f"Days with data: {len(sorted_dates)}",
                                        font=("Arial", 9), anchor="w")
                    y_offset += 15
                    
                    self.canvas.create_text(x_offset, y_offset,
                                        text=f"Average per hour: {avg_sessions:.1f}",
                                        font=("Arial", 9), anchor="w")
                    y_offset += 20
            
            # Separator
            self.canvas.create_line(x_offset, y_offset, x_offset + chart_width + 200, y_offset,
                                fill="#cccccc")
            y_offset += 20
        
        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, chart_width + 300, y_offset + 50))












 





    def open_file_selector(self):
        """Open file selection window"""
        # Store reference to selector window
        self.file_selector_window = tk.Toplevel(self.root)
        selector = self.file_selector_window
        selector.title("Select Files")
        selector.geometry("600x700")  # Doubled height from 350 to 700, increased width
        selector.resizable(True, True)  # Allow resizing
        
        # Main container
        main_container = tk.Frame(selector, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info label showing number of files
        info_label = tk.Label(main_container, 
                            text=f"Total files: {len(self.file_paths)}", 
                            bg="#f5f5f5", font=("Arial", 10, "bold"))
        info_label.pack(pady=(0, 5))
        
        # List frame
        files_frame = tk.Frame(main_container, bg="#f5f5f5")
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        # Container for scrolling with better configuration
        canvas = tk.Canvas(files_frame, bg="white")
        scrollbar = tk.Scrollbar(files_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        # Configure canvas scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Update scroll region when frame changes
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # Update canvas width when canvas size changes
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas_width)
        
        # Create header frame with sortable columns
        header_frame = tk.Frame(scrollable_frame, bg="#f0f0f0", relief=tk.RAISED, bd=1)
        header_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Header buttons with sort indicators
        name_text = "📁 File Name"
        if self.sort_by_name.get() == "asc":
            name_text += " ↑"
        elif self.sort_by_name.get() == "desc":
            name_text += " ↓"
        
        name_header = tk.Button(header_frame, text=name_text, 
                               command=lambda: self.toggle_sort("name"),
                               bg="#e0e0e0", fg="#000000",
                               font=("Arial", 9, "bold"),
                               relief=tk.RAISED, bd=1, width=25)
        name_header.pack(side=tk.LEFT, padx=2, pady=2)
        
        sessions_text = "📊 Sessions"
        if self.sort_by_sessions.get() == "asc":
            sessions_text += " ↑"
        elif self.sort_by_sessions.get() == "desc":
            sessions_text += " ↓"
        
        sessions_header = tk.Button(header_frame, text=sessions_text, 
                                   command=lambda: self.toggle_sort("sessions"),
                                   bg="#e0e0e0", fg="#000000",
                                   font=("Arial", 9, "bold"),
                                   relief=tk.RAISED, bd=1, width=15)
        sessions_header.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Create checkboxes for each file
        checkboxes = []
        checkbox_vars = []
        checkbox_to_file_index = []  # Map checkbox index to file index
        
        # Prepare data for sorting
        file_data_with_counts = []
        for idx, file_path in enumerate(self.file_paths):
            # Count sessions for this file
            session_count = 0
            if file_path in self.hourly_data_by_file:
                # hourly_data_by_file[file_path] is a dict with hours as keys
                # Each hour contains the count of sessions for that hour
                for hour, count in self.hourly_data_by_file[file_path].items():
                    session_count += count
            
            
            file_data_with_counts.append({
                'index': idx,
                'file_path': file_path,
                'session_count': session_count
            })
        
        # Sort data based on current sort settings
        sorted_data = self.sort_file_data(file_data_with_counts)
        
        for item in sorted_data:
            var = tk.BooleanVar(value=(item['index'] in self.selected_files))
            checkbox_vars.append(var)
            checkbox_to_file_index.append(item['index'])  # Store mapping
            
            cb_frame = tk.Frame(scrollable_frame, bg="white")
            cb_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Add file number and session count for easier navigation
            cb_text = f"{item['index'] + 1}. {os.path.basename(item['file_path'])} ({item['session_count']} sessions)"
            
            cb = tk.Checkbutton(cb_frame, text=cb_text,
                            variable=var, bg="white",
                            font=("Arial", 9), anchor="w", 
                            wraplength=550)  # Wrap long filenames
            cb.pack(fill=tk.X)
            checkboxes.append(cb)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mouse wheel to canvas
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Control buttons
        button_frame = tk.Frame(main_container, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Select all / Deselect all buttons
        control_frame = tk.Frame(button_frame, bg="#f5f5f5")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        def deselect_all():
            for var in checkbox_vars:
                var.set(False)
            update_selection_count()
        
        def select_all():
            for var in checkbox_vars:
                var.set(True)
            update_selection_count()
        
        def invert_selection():
            for var in checkbox_vars:
                var.set(not var.get())
            update_selection_count()
        
        # Selection counter
        selection_label = tk.Label(control_frame, text="", bg="#f5f5f5", 
                                font=("Arial", 9))
        selection_label.pack(pady=(0, 5))
        
        def update_selection_count():
            count = sum(1 for var in checkbox_vars if var.get())
            selection_label.config(text=f"Selected: {count} / {len(self.file_paths)}")
        
        # Initial count
        update_selection_count()
        
        # Add trace to update count when checkboxes change
        for var in checkbox_vars:
            var.trace('w', lambda *args: update_selection_count())
        
        # Button row 1
        button_row1 = tk.Frame(control_frame, bg="#f5f5f5")
        button_row1.pack(fill=tk.X, pady=2)
        
        deselect_btn = tk.Button(button_row1, text="Deselect All",
                            command=deselect_all,
                            bg="#e0e0e0", font=("Arial", 9),
                            width=12, height=2)
        deselect_btn.pack(side=tk.LEFT, padx=5)
        
        select_all_btn = tk.Button(button_row1, text="Select All",
                                command=select_all,
                                bg="#e0e0e0", font=("Arial", 9),
                                width=12, height=2)
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
        invert_btn = tk.Button(button_row1, text="Invert Selection",
                            command=invert_selection,
                            bg="#e0e0e0", font=("Arial", 9),
                            width=12, height=2)
        invert_btn.pack(side=tk.LEFT, padx=5)
        
        # Apply and Cancel buttons
        button_row2 = tk.Frame(button_frame, bg="#f5f5f5")
        button_row2.pack(fill=tk.X, pady=(10, 0))
        
        def apply_file_selection():
            self.selected_files.clear()
            for checkbox_idx, var in enumerate(checkbox_vars):
                if var.get():
                    file_idx = checkbox_to_file_index[checkbox_idx]
                    self.selected_files.add(file_idx)
            
            # Unbind mousewheel before closing
            canvas.unbind_all("<MouseWheel>")
            
            selector.destroy()
            self.draw_hourly_visualization()
        
        def cancel_selection():
            # Unbind mousewheel before closing
            canvas.unbind_all("<MouseWheel>")
            selector.destroy()
        
        apply_btn = tk.Button(button_row2, text="APPLY",
                        command=apply_file_selection,
                        bg="#4CAF50", fg="white",
                        font=("Arial", 10, "bold"),
                        width=15, height=2)
        apply_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(button_row2, text="CANCEL",
                            command=cancel_selection,
                            bg="#f44336", fg="white",
                            font=("Arial", 10, "bold"),
                            width=15, height=2)
        cancel_btn.pack(side=tk.RIGHT, padx=10)
        
        # Make window modal
        selector.transient(self.root)
        selector.grab_set()
        
        # Center window
        selector.update_idletasks()
        x = (selector.winfo_screenwidth() // 2) - 300
        y = (selector.winfo_screenheight() // 2) - 350
        selector.geometry(f"+{x}+{y}")
        
        # Focus on first checkbox for keyboard navigation
        if checkboxes:
            checkboxes[0].focus_set()
    
    def toggle_sort(self, sort_type):
        """Toggle sorting for file selector"""
        if sort_type == "name":
            if self.sort_by_name.get() == "asc":
                self.sort_by_name.set("desc")
            else:
                self.sort_by_name.set("asc")
            self.sort_by_sessions.set("none")
        elif sort_type == "sessions":
            if self.sort_by_sessions.get() == "none":
                self.sort_by_sessions.set("desc")
            elif self.sort_by_sessions.get() == "desc":
                self.sort_by_sessions.set("asc")
            else:
                self.sort_by_sessions.set("none")
            self.sort_by_name.set("asc")
        
        # Update the current file selector window
        self.update_file_selector_sorting()
    
    def update_file_selector_sorting(self):
        """Update the file selector window with new sorting"""
        if hasattr(self, 'file_selector_window') and self.file_selector_window.winfo_exists():
            # Close current window and reopen with new sorting
            self.file_selector_window.destroy()
            self.open_file_selector()
    
    def sort_file_data(self, file_data_with_counts):
        """Sort file data based on current sort settings"""
        if self.sort_by_sessions.get() != "none":
            # Sort by session count
            reverse = self.sort_by_sessions.get() == "desc"
            return sorted(file_data_with_counts, 
                         key=lambda x: x['session_count'], 
                         reverse=reverse)
        else:
            # Sort by filename
            reverse = self.sort_by_name.get() == "desc"
            return sorted(file_data_with_counts, 
                         key=lambda x: os.path.basename(x['file_path']).lower(), 
                         reverse=reverse)





    



















    
    def refresh_all(self):
        """Refresh all data"""
        # Reload file list from directory
        self.file_paths = self.get_all_txt_files()
        self.selected_files = set(range(len(self.file_paths)))
        
        print(f"Refreshed: Found {len(self.file_paths)} files in directory")
        
        self.load_all_data()
        self.filtered_file_data = []
        self.filter_status.config(text="No filter applied", fg="#606060")
        self.draw_hourly_visualization()
    
    def export_report(self):
        """Export report to text file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Report"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("DMR HOURLY ACTIVITY REPORT\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    # Choose data source
                    data_source = self.filtered_file_data if self.filtered_file_data else self.file_data
                    data_to_export = [data for idx, data in enumerate(data_source) if idx in self.selected_files]
                    
                    for file_data in data_to_export:
                        f.write(f"\nFile: {file_data['filename']}\n")
                        f.write(f"Frequency: {file_data['frequency']}\n")
                        f.write("-" * 40 + "\n")
                        
                        hourly_data = file_data['hourly_sessions']
                        for hour in range(24):
                            count = hourly_data.get(hour, 0)
                            symbol = self.get_visualization_symbol(count)
                            f.write(f"{hour:02d}: {symbol} ({count})\n")
                        
                        total = sum(hourly_data.values())
                        if hourly_data:
                            max_hour = max(hourly_data, key=hourly_data.get)
                            avg_sessions = total / 24
                            f.write(f"\nTotal sessions: {total}\n")
                            f.write(f"Peak hour: {max_hour:02d}:00 ({hourly_data[max_hour]} sessions)\n")
                            f.write(f"Average per hour: {avg_sessions:.1f}\n")
                        f.write("\n" + "=" * 60 + "\n")
                
                messagebox.showinfo("Export Complete", f"Report saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error saving report:\n{e}")
























    def open_identifier_selector(self):
        """Open window for selecting FROM/TO identifiers with optimization"""
        selector = tk.Toplevel(self.root)
        selector.title("Select FROM/TO Identifiers")
        selector.geometry("700x500")
        selector.resizable(True, True)
        
        # Main container
        main_container = tk.Frame(selector, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info label
        info_text = f"Total: {len(self.from_identifiers)} FROM IDs, {len(self.to_identifiers)} TO IDs"
        info_label = tk.Label(main_container, text=info_text, 
                            bg="#f5f5f5", font=("Arial", 9), fg="#666666")
        info_label.pack(pady=(0, 10))
        
        # Search frames
        search_frame = tk.Frame(main_container, bg="#f5f5f5")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # FROM search
        from_search_frame = tk.Frame(search_frame, bg="#f5f5f5")
        from_search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Label(from_search_frame, text="Search FROM:", bg="#f5f5f5", font=("Arial", 9)).pack(side=tk.LEFT)
        from_search_var = tk.StringVar()
        from_search_entry = tk.Entry(from_search_frame, textvariable=from_search_var, width=15)
        from_search_entry.pack(side=tk.LEFT, padx=5)
        
        # TO search
        to_search_frame = tk.Frame(search_frame, bg="#f5f5f5")
        to_search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        tk.Label(to_search_frame, text="Search TO:", bg="#f5f5f5", font=("Arial", 9)).pack(side=tk.LEFT)
        to_search_var = tk.StringVar()
        to_search_entry = tk.Entry(to_search_frame, textvariable=to_search_var, width=15)
        to_search_entry.pack(side=tk.LEFT, padx=5)
        
        # Container for two columns
        columns_frame = tk.Frame(main_container, bg="#f5f5f5")
        columns_frame.pack(fill=tk.BOTH, expand=True)
        
        # FROM column
        from_column = tk.Frame(columns_frame, bg="#f5f5f5")
        from_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(from_column, text="FROM", bg="#f5f5f5", 
                font=("Arial", 11, "bold")).pack()
        
        # FROM listbox with scrollbar
        from_list_frame = tk.Frame(from_column)
        from_list_frame.pack(fill=tk.BOTH, expand=True)
        
        from_scrollbar = tk.Scrollbar(from_list_frame)
        from_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        from_listbox = tk.Listbox(from_list_frame, 
                                selectmode=tk.MULTIPLE,
                                yscrollcommand=from_scrollbar.set,
                                font=("Courier", 9))
        from_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        from_scrollbar.config(command=from_listbox.yview)
        
        # TO column
        to_column = tk.Frame(columns_frame, bg="#f5f5f5")
        to_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(to_column, text="TO", bg="#f5f5f5", 
                font=("Arial", 11, "bold")).pack()
        
        # TO listbox with scrollbar
        to_list_frame = tk.Frame(to_column)
        to_list_frame.pack(fill=tk.BOTH, expand=True)
        
        to_scrollbar = tk.Scrollbar(to_list_frame)
        to_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        to_listbox = tk.Listbox(to_list_frame,
                            selectmode=tk.MULTIPLE,
                            yscrollcommand=to_scrollbar.set,
                            font=("Courier", 9))
        to_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        to_scrollbar.config(command=to_listbox.yview)
        
        # Sort identifiers by frequency (ALL of them, not limited)
        sorted_from_ids = sorted(self.from_identifiers.items(), key=lambda x: x[1], reverse=True)
        sorted_to_ids = sorted(self.to_identifiers.items(), key=lambda x: x[1], reverse=True)
        
        # Initialize if empty (select ALL by default)
        if not self.selected_from_ids or len(self.selected_from_ids) == 0:
            self.selected_from_ids = set(self.from_identifiers.keys())
        if not self.selected_to_ids or len(self.selected_to_ids) == 0:
            self.selected_to_ids = set(self.to_identifiers.keys())
        
        # Store full lists for searching
        all_from_items = []  # Store ALL items
        all_to_items = []
        
        # Populate FROM listbox with ALL identifiers
        for idx, (identifier, count) in enumerate(sorted_from_ids):
            item_text = f"{str(identifier).ljust(12)} ({count})"
            all_from_items.append((identifier, item_text, idx))
            from_listbox.insert(tk.END, item_text)
            # Select if in selected set
            if identifier in self.selected_from_ids:
                from_listbox.selection_set(idx)
        
        # Populate TO listbox with ALL identifiers
        for idx, (identifier, count) in enumerate(sorted_to_ids):
            item_text = f"{str(identifier).ljust(12)} ({count})"
            all_to_items.append((identifier, item_text, idx))
            to_listbox.insert(tk.END, item_text)
            # Select if in selected set
            if identifier in self.selected_to_ids:
                to_listbox.selection_set(idx)
        
        # Store currently displayed items
        current_from_items = all_from_items.copy()
        current_to_items = all_to_items.copy()
        
        # Search functions
        def filter_from_list(*args):
            search_term = from_search_var.get().lower()
            from_listbox.delete(0, tk.END)
            current_from_items.clear()
            
            for identifier, item_text, orig_idx in all_from_items:
                if not search_term or search_term in str(identifier).lower():
                    current_from_items.append((identifier, item_text, orig_idx))
                    from_listbox.insert(tk.END, item_text)
                    if identifier in self.selected_from_ids:
                        from_listbox.selection_set(tk.END)
            
            update_selection_count()
        
        def filter_to_list(*args):
            search_term = to_search_var.get().lower()
            to_listbox.delete(0, tk.END)
            current_to_items.clear()
            
            for identifier, item_text, orig_idx in all_to_items:
                if not search_term or search_term in str(identifier).lower():
                    current_to_items.append((identifier, item_text, orig_idx))
                    to_listbox.insert(tk.END, item_text)
                    if identifier in self.selected_to_ids:
                        to_listbox.selection_set(tk.END)
            
            update_selection_count()
        
        from_search_var.trace('w', filter_from_list)
        to_search_var.trace('w', filter_to_list)
        
        # Control buttons
        button_frame = tk.Frame(main_container, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        control_frame = tk.Frame(button_frame, bg="#f5f5f5")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Selection counter
        selection_label = tk.Label(control_frame, text="", bg="#f5f5f5", font=("Arial", 9))
        selection_label.pack(pady=(0, 5))
        
        def update_selection_count():
            from_selected = len(from_listbox.curselection())
            to_selected = len(to_listbox.curselection())
            from_total = len(current_from_items)
            to_total = len(current_to_items)
            selection_label.config(text=f"Selected: {from_selected}/{from_total} FROM, {to_selected}/{to_total} TO")
        
        def deselect_all():
            from_listbox.selection_clear(0, tk.END)
            to_listbox.selection_clear(0, tk.END)
            update_selection_count()
        
        def select_all_visible():
            from_listbox.selection_set(0, tk.END)
            to_listbox.selection_set(0, tk.END)
            update_selection_count()
        
        def select_top_10():
            from_listbox.selection_clear(0, tk.END)
            to_listbox.selection_clear(0, tk.END)
            for i in range(min(10, from_listbox.size())):
                from_listbox.selection_set(i)
            for i in range(min(10, to_listbox.size())):
                to_listbox.selection_set(i)
            update_selection_count()
        
        def select_top_50():
            from_listbox.selection_clear(0, tk.END)
            to_listbox.selection_clear(0, tk.END)
            for i in range(min(50, from_listbox.size())):
                from_listbox.selection_set(i)
            for i in range(min(50, to_listbox.size())):
                to_listbox.selection_set(i)
            update_selection_count()
        
        # Bind selection change events
        from_listbox.bind('<<ListboxSelect>>', lambda e: update_selection_count())
        to_listbox.bind('<<ListboxSelect>>', lambda e: update_selection_count())
        
        # Button row 1
        button_row1 = tk.Frame(control_frame, bg="#f5f5f5")
        button_row1.pack(fill=tk.X, pady=2)
        
        deselect_btn = tk.Button(button_row1, text="Deselect All",
                            command=deselect_all,
                            bg="#e0e0e0", font=("Arial", 9),
                            width=12)
        deselect_btn.pack(side=tk.LEFT, padx=2)
        
        top10_btn = tk.Button(button_row1, text="Top 10",
                        command=select_top_10,
                        bg="#e0e0e0", font=("Arial", 9),
                        width=12)
        top10_btn.pack(side=tk.LEFT, padx=2)
        
        top50_btn = tk.Button(button_row1, text="Top 50",
                        command=select_top_50,
                        bg="#e0e0e0", font=("Arial", 9),
                        width=12)
        top50_btn.pack(side=tk.LEFT, padx=2)
        
        select_all_btn = tk.Button(button_row1, text="Select Visible",
                                command=select_all_visible,
                                bg="#e0e0e0", font=("Arial", 9),
                                width=12)
        select_all_btn.pack(side=tk.LEFT, padx=2)
        
        # Initial count
        update_selection_count()
        
        # Apply button
        def apply_identifier_selection():
            # Update selected FROM IDs based on current visible selection
            temp_from_selected = set()
            for idx in from_listbox.curselection():
                if idx < len(current_from_items):
                    identifier = current_from_items[idx][0]
                    temp_from_selected.add(identifier)
            
            # Update selected TO IDs based on current visible selection
            temp_to_selected = set()
            for idx in to_listbox.curselection():
                if idx < len(current_to_items):
                    identifier = current_to_items[idx][0]
                    temp_to_selected.add(identifier)
            
            # Apply selections
            self.selected_from_ids = temp_from_selected
            self.selected_to_ids = temp_to_selected
            
            print(f"Selected {len(self.selected_from_ids)} FROM IDs and {len(self.selected_to_ids)} TO IDs")
            
            selector.destroy()
        
        apply_btn = tk.Button(button_frame, text="APPLY",
                        command=apply_identifier_selection,
                        bg="#4CAF50", fg="white",
                        font=("Arial", 10, "bold"),
                        width=20, height=2)
        apply_btn.pack()
        
        # Make window modal
        selector.transient(self.root)
        selector.grab_set()
        
        # Center window
        selector.update_idletasks()
        x = (selector.winfo_screenwidth() // 2) - 350
        y = (selector.winfo_screenheight() // 2) - 250
        selector.geometry(f"+{x}+{y}")























    def export_to_pdf(self):
        """Export hourly activity visualization to PDF with horizontal bar charts"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Export Error", 
                            "ReportLab library is not installed.\n"
                            "Install it with: pip install reportlab")
            return
        
        # Дополнительные импорты для графиков
        try:
            from reportlab.graphics import renderPDF
            from reportlab.graphics.shapes import Drawing, Rect, String, Line, Group
            from reportlab.lib.colors import HexColor
        except ImportError:
            messagebox.showerror("Export Error", 
                            "ReportLab graphics components are not available.\n"
                            "Please reinstall: pip install reportlab")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save PDF Report"
        )
        
        if filename:
            try:
                # Create PDF document
                doc = SimpleDocTemplate(filename, pagesize=A4,
                                    rightMargin=50, leftMargin=50,
                                    topMargin=50, bottomMargin=30)
                
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title = Paragraph("DMR Hourly Activity Report", styles['Title'])
                elements.append(title)
                
                # Date and time
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                subtitle = Paragraph(f"Generated: {date_str}", styles['Normal'])
                elements.append(subtitle)
                elements.append(Spacer(1, 0.2*inch))
                
                # Filter information
                elements.append(Paragraph("Applied Filters:", styles['Heading2']))
                
                filter_info = []
                filter_info.append(f"Date Range: {self.date_from_var.get()} to {self.date_to_var.get()}")
                
                if self.duration_from_var.get() or self.duration_to_var.get():
                    dur_from = self.duration_from_var.get() or "0"
                    dur_to = self.duration_to_var.get() or "∞"
                    filter_info.append(f"Duration: {dur_from} - {dur_to} seconds")
                
                if self.selected_event.get() != 'All':
                    filter_info.append(f"Event: {self.selected_event.get()}")
                
                if self.selected_timeslot.get() != 'All':
                    filter_info.append(f"Timeslot: {self.selected_timeslot.get()}")
                
                if self.selected_color_code.get() != 'All':
                    filter_info.append(f"Color Code: {self.selected_color_code.get()}")
                
                if self.selected_algorithm.get() != 'All':
                    filter_info.append(f"Algorithm: {self.selected_algorithm.get()}")
                
                if self.selected_key.get() != 'All':
                    filter_info.append(f"Key: {self.selected_key.get()}")
                
                for info in filter_info:
                    elements.append(Paragraph(info, styles['Normal']))
                
                elements.append(Spacer(1, 0.2*inch))
                
                # Choose data source
                data_source = self.filtered_file_data if self.filtered_file_data else self.file_data
                data_to_export = [data for idx, data in enumerate(data_source) if idx in self.selected_files]
                
                # Сортировка: файлы с данными первыми, без данных в конце
                files_with_data = []
                files_without_data = []
                
                for file_data in data_to_export:
                    # Organize records by date
                    records_by_date = defaultdict(list)
                    for record in file_data.get('all_records', []):
                        if record['timestamp']:
                            date_key = record['timestamp'].date()
                            records_by_date[date_key].append(record)
                    
                    if records_by_date:
                        files_with_data.append((file_data, records_by_date))
                    else:
                        files_without_data.append((file_data, {}))
                
                # Объединяем: сначала с данными, потом без
                all_files = files_with_data + files_without_data
                
                # 10 muted colors palette
                color_palette = [
                    "#E8D5C4",  # Light beige (oldest)
                    "#D4C5B9",  # Warm gray
                    "#C7B5A3",  # Light brown
                    "#B8A598",  # Muted tan
                    "#A8958F",  # Dusty rose
                    "#968684",  # Mauve gray
                    "#827678",  # Muted purple
                    "#6F676B",  # Dark gray blue
                    "#5C585E",  # Charcoal blue
                    "#4A4952"   # Dark slate (newest)
                ]
                
                # Add data for each file
                for file_data, records_by_date in all_files:
                    # File header
                    elements.append(PageBreak())
                    elements.append(Paragraph(f"File: {file_data['filename']}", styles['Heading2']))
                    elements.append(Paragraph(f"Frequency: {file_data['frequency']}", styles['Normal']))
                    elements.append(Spacer(1, 0.1*inch))
                    
                    if not records_by_date:
                        elements.append(Paragraph("No data in selected date range", styles['Normal']))
                        continue
                    
                    # Calculate hourly sessions for each date
                    daily_hourly_data = {}
                    for date, records in records_by_date.items():
                        hourly_counts = defaultdict(int)
                        for record in records:
                            hour = record['timestamp'].hour
                            hourly_counts[hour] += 1
                        daily_hourly_data[date] = dict(hourly_counts)
                    
                    # Sort dates
                    sorted_dates = sorted(daily_hourly_data.keys())
                    num_days = len(sorted_dates)
                    
                    # Calculate max count for scaling
                    max_count = 1
                    for hourly_data in daily_hourly_data.values():
                        if hourly_data:
                            max_count = max(max_count, max(hourly_data.values()))
                    
                    # Create horizontal bar chart (как в программе)
                    drawing = Drawing(500, 400)
                    
                    # Chart parameters
                    chart_x = 50
                    chart_y = 50
                    chart_width = 400
                    chart_height = 300
                    bar_height = 5
                    bar_vertical_offset = 3  # Уменьшено с 5 до 3, чтобы бары помещались
                    hour_spacing = 12

                    # Если дней много, нужно корректировать смещение
                    if num_days > 3:
                        bar_vertical_offset = 2  # Еще меньше смещение для большого количества дней
                    if num_days > 5:
                        bar_vertical_offset = 1  # Минимальное смещение

                    # Draw hourly bars
                    for hour in range(24):
                        hour_y = chart_y + (23 - hour) * hour_spacing  # Инвертируем для правильного порядка
                        
                        # Hour label
                        drawing.add(String(chart_x - 30, hour_y + 2, f"{hour:02d}:00", 
                                        fontSize=7, textAnchor='end'))
                        
                        # Draw bars for each day (oldest at bottom, newest on top)
                        for day_index, date in enumerate(sorted_dates):
                            count = daily_hourly_data[date].get(hour, 0)
                            
                            if count > 0:
                                # Calculate bar position - корректируем позицию чтобы не было наложения
                                bar_y = hour_y + (day_index * bar_vertical_offset)
                                bar_width = (count / max_count) * chart_width
                                
                                # Choose color
                                if num_days <= 10:
                                    color_index = day_index * (len(color_palette) - 1) // max(num_days - 1, 1)
                                else:
                                    color_index = day_index * 9 // (num_days - 1)
                                
                                # Draw bar
                                drawing.add(Rect(chart_x, bar_y, bar_width, bar_height,
                                            fillColor=HexColor(color_palette[color_index]),
                                            strokeColor=None))
                                
                                # Add count text at the end of the newest bar only
                                if day_index == num_days - 1:  # Only for the top bar
                                    drawing.add(String(chart_x + bar_width + 5, bar_y + 2, 
                                                    str(count), fontSize=6))
                                        
                                    # Add title
                                    drawing.add(String(250, chart_y + chart_height + 20, 
                                                    "Hourly Activity", fontSize=12, textAnchor='middle'))
                    
                    elements.append(drawing)
                    
                    # Date legend
                    elements.append(Spacer(1, 0.1*inch))
                    legend_data = []
                    for date_idx, date in enumerate(sorted_dates):
                        if num_days <= 10:
                            color_index = date_idx * (len(color_palette) - 1) // max(num_days - 1, 1)
                        else:
                            color_index = date_idx * 9 // (num_days - 1)
                        
                        day_total = sum(daily_hourly_data[date].values())
                        legend_data.append([
                            "",  # Color box
                            date.strftime("%Y-%m-%d"),
                            f"{day_total} sessions"
                        ])
                    
                    if legend_data:
                        legend_table = Table(legend_data, colWidths=[0.3*inch, 2*inch, 1.5*inch])
                        
                        # Create table style with colored cells
                        table_style = [
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ]
                        
                        # Add color to first column for each row
                        for i in range(len(sorted_dates)):
                            if num_days <= 10:
                                color_index = i * (len(color_palette) - 1) // max(num_days - 1, 1)
                            else:
                                color_index = i * 9 // (num_days - 1)
                            table_style.append(
                                ('BACKGROUND', (0, i), (0, i), HexColor(color_palette[color_index]))
                            )
                        
                        legend_table.setStyle(TableStyle(table_style))
                        elements.append(legend_table)
                    
                    # Statistics
                    elements.append(Spacer(1, 0.2*inch))
                    
                    total_sessions = sum(sum(daily_hourly_data[date].values()) for date in sorted_dates)
                    
                    # Find overall peak hour
                    combined_hourly = defaultdict(int)
                    for hourly_data in daily_hourly_data.values():
                        for hour, count in hourly_data.items():
                            combined_hourly[hour] += count
                    
                    if combined_hourly:
                        max_hour = max(combined_hourly, key=combined_hourly.get)
                        avg_sessions = total_sessions / (24 * len(sorted_dates)) if sorted_dates else 0
                        
                        elements.append(Paragraph(f"Total sessions: {total_sessions}", styles['Normal']))
                        elements.append(Paragraph(f"Peak hour (overall): {max_hour:02d}:00 ({combined_hourly[max_hour]} sessions)", styles['Normal']))
                        elements.append(Paragraph(f"Days with data: {len(sorted_dates)}", styles['Normal']))
                        elements.append(Paragraph(f"Average per hour: {avg_sessions:.1f}", styles['Normal']))
                
                # Build PDF
                doc.build(elements)
                messagebox.showinfo("Export Complete", f"PDF saved to:\n{filename}")
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror("Export Error", f"Error saving PDF:\n{e}")




    def open_details_selector(self):
        """Open window for selecting DETAILS"""
        messagebox.showinfo("DETAILS Filter", 
                        "DETAILS filtering is not implemented for hourly visualization.\n"
                        "This feature is available in the network connections view.")
    
def main():
    root = tk.Tk()
    root.withdraw()  # Hide main window initially
    
    # Create progress window
    progress_window = tk.Toplevel(root)
    progress_window.title("DMR Graphics - Loading")
    progress_window.geometry("400x150")
    progress_window.resizable(False, False)
    
    # Center progress window
    progress_window.update_idletasks()
    x = (progress_window.winfo_screenwidth() // 2) - 200
    y = (progress_window.winfo_screenheight() // 2) - 75
    progress_window.geometry(f"400x150+{x}+{y}")
    
    # Frame for content
    frame = tk.Frame(progress_window, bg="#f0f0f0")
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Label
    label = tk.Label(frame, text="Loading DMR Graphics...", 
                    font=("Arial", 12, "bold"), bg="#f0f0f0")
    label.pack(pady=(0, 15))
    
    # Progress bar
    progress_bar = ttk.Progressbar(frame, mode='indeterminate', length=300)
    progress_bar.pack(pady=(0, 10))
    progress_bar.start(10)
    
    # Status label
    status_label = tk.Label(frame, text="Initializing application...", 
                           font=("Arial", 9), bg="#f0f0f0", fg="#666666")
    status_label.pack()
    
    # Force update to show progress window
    progress_window.update()
    
    try:
        # Update status
        progress_window.after(100, lambda: status_label.config(text="Loading data directory..."))
        progress_window.update()
        
        # Update status
        progress_window.after(200, lambda: status_label.config(text="Creating visualizer..."))
        progress_window.update()
        
        # Create main app
        app = HourlyActivityVisualizer(root)
        
        # Update status
        progress_window.after(300, lambda: status_label.config(text="Finalizing..."))
        progress_window.update()
        
        # Close progress window and show main window
        progress_window.destroy()
        root.deiconify()  # Show main window
        
    except Exception as e:
        progress_window.destroy()
        messagebox.showerror("Error", f"Failed to load application:\n{e}")
        return
    
    root.mainloop()


if __name__ == "__main__":
    main()