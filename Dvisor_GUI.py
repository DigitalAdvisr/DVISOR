import customtkinter as ctk
from tkinter import ttk
import os

# ------------------- CORE UI SETUP -------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DvisorPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dvisor Pro v1.0 - Universal Downloader")
        self.geometry("950x600")
        self.minsize(800, 500)
        
        # Grid Layout (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ------------------- SIDEBAR -------------------
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="DVISOR PRO", font=ctk.CTkFont(size=24, weight="bold"), text_color="#00ffcc")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))
        
        self.btn_all = ctk.CTkButton(self.sidebar, text="🌐 All Downloads", anchor="w", fg_color="transparent", hover_color="#333333")
        self.btn_all.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_video = ctk.CTkButton(self.sidebar, text="🎬 Videos", anchor="w", fg_color="transparent", hover_color="#333333")
        self.btn_video.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_music = ctk.CTkButton(self.sidebar, text="🎵 Music", anchor="w", fg_color="transparent", hover_color="#333333")
        self.btn_music.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_docs = ctk.CTkButton(self.sidebar, text="📄 Documents", anchor="w", fg_color="transparent", hover_color="#333333")
        self.btn_docs.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_programs = ctk.CTkButton(self.sidebar, text="💻 Programs", anchor="w", fg_color="transparent", hover_color="#333333")
        self.btn_programs.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        # ------------------- MAIN AREA -------------------
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        # TOP ACTION BAR
        self.top_bar = ctk.CTkFrame(self.main_area, height=50, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        
        self.btn_add = ctk.CTkButton(self.top_bar, text="➕ Add Link", width=100)
        self.btn_add.pack(side="left", padx=10, pady=10)
        
        self.btn_pause = ctk.CTkButton(self.top_bar, text="⏸ Pause", width=90, fg_color="#444444", hover_color="#555555")
        self.btn_pause.pack(side="left", padx=5, pady=10)
        
        self.btn_resume = ctk.CTkButton(self.top_bar, text="▶ Resume", width=90, fg_color="#444444", hover_color="#555555")
        self.btn_resume.pack(side="left", padx=5, pady=10)
        
        self.btn_delete = ctk.CTkButton(self.top_bar, text="❌ Remove", width=90, fg_color="#7a2a2a", hover_color="#993333")
        self.btn_delete.pack(side="left", padx=5, pady=10)

        self.btn_settings = ctk.CTkButton(self.top_bar, text="⚙ Settings", width=90, fg_color="transparent", border_width=1)
        self.btn_settings.pack(side="right", padx=10, pady=10)

        # DATA GRID (TREEVIEW)
        self.grid_frame = ctk.CTkFrame(self.main_area, corner_radius=0)
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        
        # Dark Theme Styling for Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#242424", foreground="white", fieldbackground="#242424", borderwidth=0, rowheight=30)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", relief="flat", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#00ffcc")], foreground=[("selected", "black")])
        
        columns = ("File Name", "Size", "Status", "Time Left", "Transfer Rate", "Added On")
        self.tree = ttk.Treeview(self.grid_frame, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "File Name": self.tree.column(col, width=300)
            else: self.tree.column(col, width=100, anchor="center")
            
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for Grid
        scrollbar = ctk.CTkScrollbar(self.grid_frame, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Insert Dummy Data for Preview
        self.tree.insert("", "end", values=("Example_Movie_1080p.mp4", "1.2 GB", "Downloading (32%)", "00:04:15", "5.2 MiB/s", "Today"))
        self.tree.insert("", "end", values=("Windows_Tool_Setup.exe", "450 MB", "Completed", "-", "-", "Yesterday"))

if __name__ == "__main__":
    app = DvisorPro()
    app.mainloop()
