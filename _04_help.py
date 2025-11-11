#!/usr/bin/env python3
"""
DMRScope Help System
Справка по использованию приложения DMRScope
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import webbrowser


def main():
    root = tk.Tk()
    root.title("DMRScope - Help System")
    root.geometry("800x600")
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - 400
    y = (root.winfo_screenheight() // 2) - 300
    root.geometry(f"800x600+{x}+{y}")
    
    # Main frame with dark theme
    main_frame = tk.Frame(root, bg="#002244")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Header
    header_frame = tk.Frame(main_frame, bg="#003366")
    header_frame.pack(fill=tk.X, padx=0, pady=0)
    
    title_label = tk.Label(header_frame, text="DMRScope - Help System", 
                          font=("Arial", 16, "bold"), 
                          bg="#003366", fg="#66ffff", pady=10)
    title_label.pack()
    
    # Create notebook for tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Tab 1: About
    about_frame = tk.Frame(notebook, bg="#f0f0f0")
    notebook.add(about_frame, text="About")
    
    about_text = scrolledtext.ScrolledText(about_frame, wrap=tk.WORD, 
                                          font=("Arial", 10), bg="#f0f0f0")
    about_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    about_content = """DMRScope v1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DMR Signal Analysis and Visualization System

DMRScope is a comprehensive tool for analyzing, visualizing, and managing 
DMR (Digital Mobile Radio) network connections and activity data.

Features:
• Data conversion and processing
• Network connection visualization
• Hourly activity analysis
• Group connection analysis
• PDF, Excel, and TXT export
• Real-time data filtering

Version: 1
Last Updated: 2025
Special version for DragonOS
Web site: https://cemaxecuter.com/

Support via Signal Message:
https://signal.me/#eu/D7xY48CJYLU2Lg3gxDHVnXGYg_QbJOoUJH5GzjO_UbNRelYoyL5NBpaFucNUO7tJ

Click the links above to visit our website or message us via Signal
Signal is a secure messaging application by Signal Foundation"""
    
    about_text.insert(1.0, about_content)
    about_text.config(state=tk.NORMAL)  # Enable editing to add tags
    
    # Make links clickable in about_text
    about_text.tag_config("link", foreground="blue", underline=True)
    
    def tag_links_in_text(text_widget):
        """Tag all URLs in text widget to make them clickable"""
        import re
        content = text_widget.get("1.0", "end")
        url_pattern = r'https?://[^\s]+'
        
        # Find all URLs and their positions
        link_count = 0
        for match in re.finditer(url_pattern, content):
            url = match.group()
            start_idx = match.start()
            end_idx = match.end()
            
            # Convert character index to text widget index
            line = 1
            col = 0
            
            for i, char in enumerate(content):
                if i == start_idx:
                    break
                if char == '\n':
                    line += 1
                    col = 0
                else:
                    col += 1
            
            start_pos = f"{line}.{col}"
            end_pos = f"{line}.{col + len(url)}"
            
            # Create unique tag for each link
            link_tag = f"link_{link_count}"
            text_widget.tag_config(link_tag, foreground="blue", underline=True)
            text_widget.tag_add(link_tag, start_pos, end_pos)
            
            # Bind click event to this specific link with a closure to capture the URL
            def make_click_handler(target_url):
                def on_click(event):
                    webbrowser.open(target_url)
                return on_click
            
            text_widget.tag_bind(link_tag, "<Button-1>", make_click_handler(url))
            text_widget.tag_bind(link_tag, "<Enter>", 
                               lambda e: about_text.config(cursor="hand2"))
            text_widget.tag_bind(link_tag, "<Leave>", 
                               lambda e: about_text.config(cursor="arrow"))
            
            link_count += 1
    
    tag_links_in_text(about_text)
    about_text.config(state=tk.DISABLED)  # Disable editing
    
    # Tab 2: Quick Start
    quickstart_frame = tk.Frame(notebook, bg="#f0f0f0")
    notebook.add(quickstart_frame, text="Quick Start")
    
    quickstart_text = scrolledtext.ScrolledText(quickstart_frame, wrap=tk.WORD, 
                                               font=("Arial", 10), bg="#f0f0f0")
    quickstart_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    quickstart_content = """Quick Start Guide
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. CONVERT DATA [01]
   • Select gap time: 0 seconds (no gap) or 1-60 seconds (with gap)
   • Converts raw DMR logs to processed format
   • Output: Data files in convert_data directory

2. VISUALIZATION CONNECTION [02]
   • Visualize network connections between nodes
   • Filter by FROM/TO identifiers
   • Select specific files and date ranges
   • Export to SVG format

3. DAILY ACTIVITIES [03]
   • View hourly activity patterns
   • Analyze session groups
   • Export reports to PDF

4. GROUP CONNECTIONS [04]
   • Group sessions by time intervals
   • Filter and analyze connections
   • Export to PDF, Excel, or TXT
   • View detailed session information

5. HELP SYSTEM [05]
   • View this help documentation
   • Learn about application features"""
    
    quickstart_text.insert(1.0, quickstart_content)
    quickstart_text.config(state=tk.DISABLED)
    
    # Tab 3: Configuration
    config_frame = tk.Frame(notebook, bg="#f0f0f0")
    notebook.add(config_frame, text="Configuration")
    
    config_text = scrolledtext.ScrolledText(config_frame, wrap=tk.WORD, 
                                           font=("Arial", 10), bg="#f0f0f0")
    config_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    config_content = """Configuration Guide
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Configuration file: config.ini

[PATHS]
raw_data = Path to raw DMR data files
convert_data = Path to converted/processed data

[SETTINGS]
gap_time = Gap time for data conversion (0-60 seconds)

How to Change Settings:
1. Open the DMRScope start window
2. Use the "Browse" buttons to select directories
3. Enter gap_time value (0-60)
4. Settings are automatically saved to config.ini
5. All modules automatically use updated settings

Dynamic Configuration:
• All paths are loaded from config.ini at startup
• Changes to config.ini are picked up immediately
• No need to restart individual modules"""
    
    config_text.insert(1.0, config_content)
    config_text.config(state=tk.DISABLED)
    
    # Tab 4: Troubleshooting
    trouble_frame = tk.Frame(notebook, bg="#f0f0f0")
    notebook.add(trouble_frame, text="Troubleshooting")
    
    trouble_text = scrolledtext.ScrolledText(trouble_frame, wrap=tk.WORD, 
                                            font=("Arial", 10), bg="#f0f0f0")
    trouble_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    trouble_content = """Troubleshooting Guide
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: config.ini not found
Solution: Run run.py to create and configure config.ini with proper paths

Problem: No data files found
Solution: 
• Check that convert_data path in config.ini is correct
• Ensure .txt files exist in the data directory
• Check file permissions

Problem: Program freezes when loading data
Solution:
• Wait for loading to complete
• Check that data files are not corrupted
• Reduce number of files or try smaller date range

Problem: Export fails
Solution:
• Check that export directory exists
• Ensure sufficient disk space
• Try different export format
• Check file permissions

Problem: Cannot find raw data
Solution:
• Verify raw_data path in config.ini
• Run data conversion first (CONVERT DATA button)
• Check that source DMR log files exist

Need More Help?
• Check application logs for error messages
• Verify config.ini settings
• Ensure all dependencies are installed"""
    
    trouble_text.insert(1.0, trouble_content)
    trouble_text.config(state=tk.DISABLED)
    
    # Tab 5: Support
    support_frame = tk.Frame(notebook, bg="#f0f0f0")
    notebook.add(support_frame, text="Support")
    
    support_content_frame = tk.Frame(support_frame, bg="#f0f0f0")
    support_content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    support_title = tk.Label(support_content_frame, text="Support & Contact", 
                            font=("Arial", 14, "bold"), bg="#f0f0f0", fg="#001122")
    support_title.pack(pady=(0, 20))
    
    support_desc = tk.Label(support_content_frame, 
                           text="Need help or want to get in touch?\nClick the links in the About tab to contact us via Signal or visit our website:", 
                           font=("Arial", 11), bg="#f0f0f0", fg="#333333", justify=tk.CENTER)
    support_desc.pack(pady=(0, 20))
    
    support_info = tk.Label(support_content_frame, 
                           text="Signal is a secure messaging application.\nYour privacy is our priority.",
                           font=("Arial", 10), bg="#f0f0f0", fg="#666666", justify=tk.CENTER)
    support_info.pack(pady=(20, 0))
    
    # Footer
    footer_frame = tk.Frame(main_frame, bg="#003366")
    footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    footer_label = tk.Label(footer_frame, 
                           text=f"DMRScope v1 | © 2025",
                           font=("Arial", 9), bg="#003366", fg="#66ffff", pady=5)
    footer_label.pack()
    
    root.mainloop()


if __name__ == "__main__":
    main()
