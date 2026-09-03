import sys
import customtkinter as ctk
from tkinter import ttk, Menu
import threading

# SETTING THEME FAST
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DvisorPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. INSTANT GUI CREATION
        self.title("Internet Download Manager (Dvisor Pro v1.0)")
        self.geometry("1050x650")
        self.minsize(800, 500)
        self.configure(fg_color="#333333")
        
        # Grid Layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 2. BUILD UI ELEMENTS FAST
        self.build_menubar()
        self.build_toolbar()
        self.build_sidebar()
        self.build_grid()

        # 3. FORCE RENDER TO SCREEN (0.1 Second Load)
        self.update()

        # 4. LOAD HEAVY ENGINES IN BACKGROUND
        threading.Thread(target=self.lazy_load_engines, daemon=True).start()

    def build_menubar(self):
        self.menubar = Menu(self, bg="#2d2d2d", fg="white")
        
        menu_tasks = Menu(self.menubar, tearoff=0, bg="#2d2d2d", fg="white")
        menu_tasks.add_command(label="Add new download")
        self.menubar.add_cascade(label="Tasks", menu=menu_tasks)
        
        menu_file = Menu(self.menubar, tearoff=0, bg="#2d2d2d", fg="white")
        menu_file.add_command(label="Exit")
        self.menubar.add_cascade(label="File", menu=menu_file)
        
        menu_dl = Menu(self.menubar, tearoff=0, bg="#2d2d2d", fg="white")
        menu_dl.add_command(label="Pause All")
        self.menubar.add_cascade(label="Downloads", menu=menu_dl)
        
        self.menubar.add_cascade(label="View", menu=Menu(self.menubar, tearoff=0))
        self.menubar.add_cascade(label="Help", menu=Menu(self.menubar, tearoff=0))
        
        self.config(menu=self.menubar)

    def build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#333333")
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        buttons = ["Add URL", "Resume", "Stop", "Delete", "Options", "Scheduler", "Start Queue", "Stop Queue"]
        for btn_text in buttons:
            btn = ctk.CTkButton(self.toolbar, text=btn_text, width=70, height=50, fg_color="transparent", hover_color="#444444", border_width=1, border_color="#555555", text_color="white")
            btn.pack(side="left", padx=2, pady=5)

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#2b2b2b")
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(0, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Sidebar.Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=25, font=("Arial", 10))
        style.configure("Sidebar.Treeview.Heading", background="#2b2b2b", foreground="white", relief="flat", font=("Arial", 11, "bold"))
        style.map("Sidebar.Treeview", background=[("selected", "#555555")], foreground=[("selected", "white")])

        self.cat_tree = ttk.Treeview(self.sidebar_frame, style="Sidebar.Treeview", show="tree headings")
        self.cat_tree.heading("#0", text="Categories", anchor="w")
        self.cat_tree.column("#0", width=200)

        # IDM Tree Structure
        node_all = self.cat_tree.insert("", "end", text="All Downloads", open=True)
        self.cat_tree.insert(node_all, "end", text="Compressed")
        self.cat_tree.insert(node_all, "end", text="Documents")
        self.cat_tree.insert(node_all, "end", text="Music")
        self.cat_tree.insert(node_all, "end", text="Programs")
        self.cat_tree.insert(node_all, "end", text="Video")
        
        node_unf = self.cat_tree.insert("", "end", text="Unfinished", open=True)
        node_fin = self.cat_tree.insert("", "end", text="Finished", open=True)
        self.cat_tree.insert("", "end", text="Grabber projects", open=True)
        self.cat_tree.insert("", "end", text="Queues", open=True)

        self.cat_tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    def build_grid(self):
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e1e1e")
        self.main_area.grid(row=1, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.configure("Main.Treeview", background="#1e1e1e", foreground="white", fieldbackground="#1e1e1e", borderwidth=0, rowheight=25)
        style.configure("Main.Treeview.Heading", background="#333333", foreground="white", relief="flat", font=("Arial", 9, "bold"))
        style.map("Main.Treeview", background=[("selected", "#0078D7")], foreground=[("selected", "white")])
        
        columns = ("File Name", "Size", "Status", "Time Left", "Transfer Rate", "Last Try", "Description")
        self.tree = ttk.Treeview(self.main_area, columns=columns, show="headings", style="Main.Treeview")
        
        for col in columns:
            self.tree.heading(col, text=col, anchor="w")
            if col == "File Name": self.tree.column(col, width=280, anchor="w")
            elif col == "Status": self.tree.column(col, width=150, anchor="w")
            else: self.tree.column(col, width=90, anchor="w")
            
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.main_area, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # IDM Context Menu
        self.rc_menu = Menu(self, tearoff=0, bg="#333333", fg="white", activebackground="#0078D7")
        self.rc_menu.add_command(label="Resume Download")
        self.rc_menu.add_command(label="Stop Download")
        self.rc_menu.add_separator()
        self.rc_menu.add_command(label="Open Folder")
        self.rc_menu.add_command(label="Remove")
        self.tree.bind("<Button-3>", self.show_rc_menu)

        # Demo Data
        self.tree.insert("", "end", values=("Software_Setup_2026.exe", "45.2 MB", "Completed", "", "", "Today", ""))
        self.tree.insert("", "end", values=("Project_Video_Draft.mp4", "1.2 GB", "Downloading (32%)", "00:15:30", "2.1 MB/sec", "Today", ""))

    def show_rc_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.rc_menu.tk_popup(event.x_root, event.y_root)

    def lazy_load_engines(self):
        # 100% BACKGROUND LOADING. GUI WILL NOT FREEZE.
        import time
        import yt_dlp
        import urllib.request
        import ctypes
        import queue
        import win32clipboard

if __name__ == "__main__":
    app = DvisorPro()
    app.mainloop()
