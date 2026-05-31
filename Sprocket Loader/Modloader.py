import os
import sys
import json
import zipfile
import shutil
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path

CONFIG_FILE = "modloader_config.json"

# Fix for Windows Taskbar: Force Windows to recognize this as a distinct application
# rather than grouping it under the generic Python/PyInstaller process icon.
if platform.system() == "Windows":
    try:
        import ctypes
        myappid = "sprocket.modmanager.loader.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

def get_asset_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SprocketModloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sprocket Mod Manager")
        self.geometry("700x600")
        self.resizable(False, False)
        
        # --- App Icon Logic (Title Bar & Taskbar) ---
        icon_path = get_asset_path("sprocket.png")
        if os.path.exists(icon_path):
            try:
                # Use PhotoImage for cross-platform compatibility in Tkinter
                self.app_icon = tk.PhotoImage(file=icon_path)
                self.iconphoto(False, self.app_icon)
            except Exception as e:
                print(f"Failed to load window icon: {e}")
        
        # Colors / Style
        self.configure(bg="#2b2b2b")
        self.fg_color = "#ffffff"
        self.bg_color = "#2b2b2b"
        self.btn_color = "#404040"
        self.hl_color = "#007acc"
        self.list_bg = "#1e1e1e"
        
        # Load Config
        self.config = self.load_config()
        self.mods_path = self.config.get("mods_path", self.default_mods_path())
        self.game_path = self.config.get("game_path", self.auto_detect_game_path())
        
        self.mod_vars = {} # Maps mod name to Tkinter IntVar
        self.last_mods_state = None
        
        self.create_widgets()
        self.refresh_mods_list()
        self.auto_poll_mods()

    def auto_poll_mods(self):
        # Periodically check if the folder contents have changed
        if os.path.exists(self.mods_path):
            try:
                items = os.listdir(self.mods_path)
                mods = []
                for d in items:
                    full_path = os.path.join(self.mods_path, d)
                    if os.path.isdir(full_path):
                        mods.append(d)
                    elif os.path.isfile(full_path) and (d.endswith(".zip") or d.endswith(".disabled")):
                        mods.append(d)
                mods.sort(key=lambda x: x.lower())
                
                # Create a state signature based on folder names
                current_state = hash(tuple(mods))
                if self.last_mods_state is not None and current_state != self.last_mods_state:
                    self.refresh_mods_list()
                self.last_mods_state = current_state
            except Exception:
                pass
                
        # Run again every 2 seconds
        self.after(2000, self.auto_poll_mods)

    def default_mods_path(self):
        home = str(Path.home())
        return os.path.join(home, "Documents", "My Games", "Sprocket", "Mods")
        
    def auto_detect_game_path(self):
        system = platform.system()
        paths_to_check = []
        
        if system == "Windows":
            paths_to_check = [
                r"C:\Program Files (x86)\Steam\steamapps\common\Sprocket",
                r"C:\Program Files\Steam\steamapps\common\Sprocket",
                r"D:\SteamLibrary\steamapps\common\Sprocket",
            ]
        elif system == "Linux":
            home = str(Path.home())
            paths_to_check = [
                f"{home}/.steam/steam/steamapps/common/Sprocket",
                f"{home}/.local/share/Steam/steamapps/common/Sprocket",
                f"{home}/.var/app/com.valvesoftware.Steam/.steam/steam/steamapps/common/Sprocket"
            ]
            
        for path in paths_to_check:
            if os.path.isdir(path) and os.path.isdir(os.path.join(path, "Sprocket_Data")):
                return path
        return ""

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self):
        self.config["mods_path"] = self.mods_path
        self.config["game_path"] = self.game_path
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def create_widgets(self):
        # Toolbar
        toolbar = tk.Frame(self, bg=self.btn_color)
        toolbar.pack(fill="x", side="top")
        
        tk.Button(toolbar, text="Deploy Mods to Game", bg=self.hl_color, fg="#ffffff", 
                  command=self.deploy_mods, font=("Helvetica", 10, "bold"), bd=0, padx=10, pady=5).pack(side="left", padx=5, pady=5)
                  
        tk.Button(toolbar, text="Settings", bg=self.btn_color, fg="#ffffff", 
                  command=self.open_settings, font=("Helvetica", 10), bd=0, padx=10, pady=5).pack(side="right", padx=5, pady=5)
        
        # Header
        tk.Label(self, text="Installed Mods", font=("Helvetica", 14, "bold"), 
                 bg=self.bg_color, fg=self.hl_color).pack(pady=(10, 5))
                 
        # Mod List Frame (Scrollable)
        container = tk.Frame(self, bg=self.list_bg)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        self.canvas = tk.Canvas(container, bg=self.list_bg, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.list_bg)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Log Output for Deployment
        tk.Label(self, text="Deployment Log:", bg=self.bg_color, fg=self.fg_color).pack(anchor="w", padx=20)
        self.log_text = scrolledtext.ScrolledText(self, height=6, bg="#1e1e1e", fg=self.fg_color)
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.log_text.config(state="disabled")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.update()

    def refresh_mods_list(self):
        # Clear existing list
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.mod_vars.clear()
        
        if not os.path.exists(self.mods_path):
            tk.Label(self.scrollable_frame, text="Mods folder not found. Check Settings.", 
                     bg=self.list_bg, fg="gray").pack(pady=10, padx=10)
            return
            
        try:
            items = os.listdir(self.mods_path)
            # Find directories or zip files
            mods = []
            for d in items:
                full_path = os.path.join(self.mods_path, d)
                if os.path.isdir(full_path):
                    mods.append(d)
                elif os.path.isfile(full_path) and (d.endswith(".zip") or d.endswith(".disabled")):
                    mods.append(d)
            
            if not mods:
                tk.Label(self.scrollable_frame, text="No mods installed.", 
                         bg=self.list_bg, fg="gray").pack(pady=10, padx=10)
                return
                
            mods.sort(key=lambda x: x.lower())
            
            for mod_folder in mods:
                is_disabled = mod_folder.endswith(".disabled")
                mod_name = mod_folder[:-9] if is_disabled else mod_folder
                
                var = tk.IntVar(value=0 if is_disabled else 1)
                self.mod_vars[mod_folder] = var
                
                chk = tk.Checkbutton(self.scrollable_frame, text=mod_name, variable=var,
                                     bg=self.list_bg, fg=self.fg_color, selectcolor=self.bg_color,
                                     activebackground=self.list_bg, activeforeground=self.fg_color,
                                     command=lambda mf=mod_folder: self.toggle_mod(mf))
                chk.pack(anchor="w", padx=10, pady=2)
                
        except Exception as e:
            tk.Label(self.scrollable_frame, text=f"Error reading mods: {e}", 
                     bg=self.list_bg, fg="red").pack(pady=10, padx=10)

    def toggle_mod(self, mod_folder):
        var = self.mod_vars.get(mod_folder)
        if var is None:
            return
            
        enabled = var.get() == 1
        is_disabled = mod_folder.endswith(".disabled")
        
        old_path = os.path.join(self.mods_path, mod_folder)
        
        if enabled and is_disabled:
            # Enable it: remove .disabled
            new_name = mod_folder[:-9]
            new_path = os.path.join(self.mods_path, new_name)
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not enable mod: {e}")
                var.set(0) # revert
                
        elif not enabled and not is_disabled:
            # Disable it: add .disabled
            new_name = mod_folder + ".disabled"
            new_path = os.path.join(self.mods_path, new_name)
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not disable mod: {e}")
                var.set(1) # revert
                
        # Full refresh to update internal paths
        self.refresh_mods_list()

    def open_settings(self):
        settings_win = tk.Toplevel(self)
        settings_win.title("Settings")
        settings_win.geometry("550x220")
        settings_win.configure(bg=self.bg_color)
        settings_win.resizable(False, False)
        
        # Make modal
        settings_win.transient(self)
        settings_win.grab_set()
        
        # Game Directory
        tk.Label(settings_win, text="Game Directory:", bg=self.bg_color, fg=self.fg_color).pack(anchor="w", padx=20, pady=(15, 0))
        game_path_var = tk.StringVar(value=self.game_path)
        game_entry_frame = tk.Frame(settings_win, bg=self.bg_color)
        game_entry_frame.pack(fill="x", padx=20, pady=(0, 10))
        tk.Entry(game_entry_frame, textvariable=game_path_var, bg=self.list_bg, fg=self.fg_color, 
                 insertbackground=self.fg_color).pack(side="left", fill="x", expand=True, padx=(0, 5))
                 
        def browse_game():
            folder = filedialog.askdirectory(initialdir=game_path_var.get(), title="Select Game Directory")
            if folder:
                game_path_var.set(folder)
        tk.Button(game_entry_frame, text="Browse", bg=self.btn_color, fg=self.fg_color, command=browse_game).pack(side="right")
        
        # Mods Directory
        tk.Label(settings_win, text="Mods Directory:", bg=self.bg_color, fg=self.fg_color).pack(anchor="w", padx=20)
        mods_path_var = tk.StringVar(value=self.mods_path)
        mods_entry_frame = tk.Frame(settings_win, bg=self.bg_color)
        mods_entry_frame.pack(fill="x", padx=20)
        tk.Entry(mods_entry_frame, textvariable=mods_path_var, bg=self.list_bg, fg=self.fg_color, 
                 insertbackground=self.fg_color).pack(side="left", fill="x", expand=True, padx=(0, 5))
                 
        def browse_mods():
            folder = filedialog.askdirectory(initialdir=mods_path_var.get(), title="Select Mods Directory")
            if folder:
                mods_path_var.set(folder)
        tk.Button(mods_entry_frame, text="Browse", bg=self.btn_color, fg=self.fg_color, command=browse_mods).pack(side="right")
        
        def save():
            new_mods = mods_path_var.get().strip()
            new_game = game_path_var.get().strip()
            if new_mods and new_game:
                self.mods_path = new_mods
                self.game_path = new_game
                self.save_config()
                self.refresh_mods_list()
                settings_win.destroy()
                
        tk.Button(settings_win, text="Save Settings", bg=self.hl_color, fg="#ffffff", command=save, font=("Helvetica", 10, "bold")).pack(pady=15)

    def deploy_mods(self):
        if not self.game_path or not os.path.isdir(self.game_path):
            messagebox.showerror("Error", "Invalid Game Directory set in Settings.")
            return
            
        target_base = os.path.join(self.game_path, "Sprocket_Data", "StreamingAssets")
        if not os.path.exists(target_base):
            confirm = messagebox.askyesno("Warning", f"'Sprocket_Data/StreamingAssets' not found in:\n{self.game_path}\n\nAre you sure this is the right folder? Deploying will create it.")
            if not confirm:
                return
                
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
        self.log("--- Starting Mod Deployment ---")
        self.log(f"Target Game Directory: {target_base}")
        
        # Process ALL mods (disabled first, then enabled)
        items = os.listdir(self.mods_path)
        disabled_mods = [d for d in items if d.endswith(".disabled")]
        enabled_mods = [d for d in items if not d.endswith(".disabled")]
        
        # Undeploy disabled mods
        for mod in disabled_mods:
            full_path = os.path.join(self.mods_path, mod)
            self.log(f"\nUndeploying (removing files): {mod}")
            try:
                if os.path.isfile(full_path) and full_path.endswith(".zip.disabled"):
                    self._undeploy_zip_mod(full_path, target_base)
                elif os.path.isdir(full_path):
                    self._undeploy_dir_mod(full_path, target_base)
            except Exception as e:
                self.log(f"Error undeploying {mod}: {e}")
        
        # Deploy enabled mods
        for mod in enabled_mods:
            full_path = os.path.join(self.mods_path, mod)
            self.log(f"\nDeploying (extracting files): {mod}")
            
            try:
                if os.path.isfile(full_path) and full_path.endswith(".zip"):
                    self._extract_zip_mod(full_path, target_base)
                elif os.path.isdir(full_path):
                    self._copy_dir_mod(full_path, target_base)
            except Exception as e:
                self.log(f"Error deploying {mod}: {e}")
                
        self.log("\n--- Deployment Complete! ---")
        messagebox.showinfo("Deploy", "Mods have been successfully synced with the game!")

    def _get_zip_data_prefix(self, namelist):
        """Find the prefix path up to and including 'Data/' in the zip."""
        for name in namelist:
            if name.endswith("Data/") or "/Data/" in name or name.startswith("Data/"):
                idx = name.find("Data/")
                if idx != -1:
                    return name[:idx + 5]  # includes 'Data/'
        return None

    def _extract_zip_mod(self, zip_path, target_base):
        # Copy only files inside Data/<subfolder>/ (e.g. Eras/, Technology/)
        # into StreamingAssets/<subfolder>/. Ignore Meta and Data itself.
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            data_prefix = self._get_zip_data_prefix(namelist)
            if not data_prefix:
                self.log("  Warning: No Data/ folder found in zip, skipping.")
                return

            extract_count = 0
            for item in namelist:
                if not item.startswith(data_prefix) or item.endswith("/"):
                    continue
                # Path relative to Data/  e.g. "Eras/Coldwar.json"
                rel = item[len(data_prefix):]
                if not rel or "/" not in rel:
                    # Skip loose files sitting directly in Data/ (if any)
                    continue
                target_file_path = os.path.normpath(os.path.join(target_base, rel))
                os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                with zf.open(item) as source, open(target_file_path, "wb") as target:
                    target.write(source.read())
                extract_count += 1
            self.log(f"  Extracted {extract_count} files from zip.")

    def _copy_dir_mod(self, dir_path, target_base):
        # Only copy from Data/<subfolder>/ (e.g. Eras/, Technology/) into StreamingAssets/<subfolder>/
        # Ignore Meta/ and anything not inside a subfolder of Data/
        data_dir = os.path.join(dir_path, "Data")
        if not os.path.isdir(data_dir):
            self.log("  Warning: No Data/ folder found in mod directory, skipping.")
            return

        copy_count = 0
        # Each direct child of Data/ is a game subfolder (Eras, Technology, etc.)
        for subfolder in os.listdir(data_dir):
            sub_src = os.path.join(data_dir, subfolder)
            if not os.path.isdir(sub_src):
                continue  # Skip loose files directly in Data/
            for root, dirs, files in os.walk(sub_src):
                for file in files:
                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, data_dir)  # e.g. Eras/Coldwar.json
                    dest_file = os.path.normpath(os.path.join(target_base, rel_path))
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                    shutil.copy2(src_file, dest_file)
                    copy_count += 1
        self.log(f"  Copied {copy_count} files from directory.")


    def _undeploy_zip_mod(self, zip_path, target_base):
        # Mirror of _extract_zip_mod — remove files from the same Data/ subfolders
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            data_prefix = self._get_zip_data_prefix(namelist)
            if not data_prefix:
                self.log("  Warning: No Data/ folder found in zip, nothing to remove.")
                return

            remove_count = 0
            for item in namelist:
                if not item.startswith(data_prefix) or item.endswith("/"):
                    continue
                rel = item[len(data_prefix):]
                if not rel or "/" not in rel:
                    continue
                target_file_path = os.path.normpath(os.path.join(target_base, rel))
                if os.path.isfile(target_file_path):
                    try:
                        os.remove(target_file_path)
                        remove_count += 1
                    except:
                        pass
            self.log(f"  Removed {remove_count} files originally from zip.")

    def _undeploy_dir_mod(self, dir_path, target_base):
        # Mirror of _copy_dir_mod — remove only files from Data/ subfolders
        data_dir = os.path.join(dir_path, "Data")
        if not os.path.isdir(data_dir):
            self.log("  Warning: No Data/ folder found in mod directory, nothing to remove.")
            return

        remove_count = 0
        for subfolder in os.listdir(data_dir):
            sub_src = os.path.join(data_dir, subfolder)
            if not os.path.isdir(sub_src):
                continue
            for root, dirs, files in os.walk(sub_src):
                for file in files:
                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, data_dir)  # e.g. Eras/Coldwar.json
                    dest_file = os.path.normpath(os.path.join(target_base, rel_path))
                    if os.path.isfile(dest_file):
                        try:
                            os.remove(dest_file)
                            remove_count += 1
                        except:
                            pass
        self.log(f"  Removed {remove_count} files originally from directory.")

if __name__ == "__main__":
    app = SprocketModloader()
    app.mainloop()