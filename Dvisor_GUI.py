import customtkinter as ctk
from tkinter import ttk, Menu
import threading

# ------------------- 1. INSTANT GUI LOAD -------------------
# GUI will load in 0.5 seconds before any heavy backend engine blocks it.
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DvisorPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dvisor Pro v1.0 - Internet Download Manager")
        self.geometry("1050x650")
        self.minsize(800, 500)
        
        # Grid Layout (2 Rows: Toolbar, Main Area)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ------------------- TOP TOOLBAR (IDM STYLE) -------------------
        self.toolbar = ctk.CTkFrame(self, height=75, corner_radius=0, fg_color="#1a1a1a")
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.build_toolbar()
        
        # ------------------- LEFT SIDEBAR -------------------
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#242424")
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)
        self.build_sidebar()

        # ------------------- MAIN DATA GRID -------------------
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.build_grid()

        # ------------------- BACKGROUND INITIALIZER -------------------
        # Loading Heavy Engines quietly in background
        threading.Thread(target=self.lazy_load_engines, daemon=True).start()

    def build_toolbar(self):
        btn_configs = [
            ("➕\nAdd URL", "#2FA572", None),
            ("▶\nResume", "#333333", None),
            ("⏸\nStop", "#333333", None),
            ("⏹\nStop All", "#333333", None),
            ("❌\nDelete", "#8A2A2A", None),
            ("⚙\nOptions", "#333333", None),
            ("🕒\nScheduler", "#333333", None)
        ]
        for text, color, cmd in btn_configs:
            btn = ctk.CTkButton(self.toolbar, text=text, width=75, height=55, fg_color=color, hover_color="#555555", font=ctk.CTkFont(size=12, weight="bold"))
            btn.pack(side="left", padx=5, pady=10)

    def build_sidebar(self):
        lbl = ctk.CTkLabel(self.sidebar, text="Categories", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00ffcc")
        lbl.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        cats = ["🌐 All Downloads", "⏳ Unfinished", "✅ Finished", "🎬 Videos", "🎵 Music", "💻 Programs", "📄 Documents", "📦 Compressed"]
        for i, cat in enumerate(cats):
            btn = ctk.CTkButton(self.sidebar, text=cat, anchor="w", fg_color="transparent", hover_color="#3a3a3a", text_color="#e0e0e0")
            btn.grid(row=i+1, column=0, padx=10, pady=2, sticky="ew")

    def build_grid(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#1e1e1e", foreground="white", fieldbackground="#1e1e1e", borderwidth=0, rowheight=28)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", relief="flat", font=("Arial", 9, "bold"))
        style.map("Treeview", background=[("selected", "#00ffcc")], foreground=[("selected", "black")])
        
        columns = ("File Name", "Size", "Status", "Time Left", "Transfer Rate", "Last Try", "Description")
        self.tree = ttk.Treeview(self.main_area, columns=columns, show="headings", selectmode="extended")
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "File Name": self.tree.column(col, width=280)
            elif col == "Status": self.tree.column(col, width=150)
            else: self.tree.column(col, width=90, anchor="center")
            
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ctk.CTkScrollbar(self.main_area, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # IDM Style Context Menu (Right Click)
        self.rc_menu = Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#00ffcc", activeforeground="black", font=("Arial", 10))
        self.rc_menu.add_command(label="▶ Resume Download")
        self.rc_menu.add_command(label="⏸ Stop Download")
        self.rc_menu.add_separator()
        self.rc_menu.add_command(label="📁 Open Folder")
        self.rc_menu.add_command(label="❌ Remove from list")
        self.tree.bind("<Button-3>", self.show_rc_menu)

        # Sample Data
        self.tree.insert("", "end", values=("Example_IDM_Setup.exe", "12.5 MB", "Completed", "-", "-", "Today", "Installer"))
        self.tree.insert("", "end", values=("Action_Movie_2026_1080p.mp4", "2.1 GB", "Downloading (45%)", "00:12:30", "3.2 MiB/s", "Today", "Media"))

    def show_rc_menu(self, event):
        try:
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.rc_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.rc_menu.grab_release()

    def lazy_load_engines(self):
        # Heavy engines loaded silently in the background
        import yt_dlp
        import urllib.request
        import ctypes
        import win32clipboard
        import queue
        import re

if __name__ == "__main__":
    app = DvisorPro()
    app.mainloop()
