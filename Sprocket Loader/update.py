import os
import re

with open("Modloader.py", "r") as f:
    content = f.read()

# Replace the auto_detect_sprocket method
old_auto_detect = """    def auto_detect_sprocket(self):
        system = platform.system()
        paths_to_check = []
        
        if system == "Windows":
            paths_to_check = [
                r"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Sprocket",
                r"C:\\Program Files\\Steam\\steamapps\\common\\Sprocket",
                r"D:\\SteamLibrary\\steamapps\\common\\Sprocket",
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
        return \"\""""

new_auto_detect = """    def auto_detect_sprocket(self):
        home = str(Path.home())
        # Handles both Windows (C:\\Users\\<user>) and Linux (/home/<user>)
        mods_path = os.path.join(home, "Documents", "My Games", "Sprocket", "Mods")
        return mods_path"""

content = content.replace(old_auto_detect, new_auto_detect)

# Replace target dir labels
content = content.replace('"Select Sprocket Installation Directory"', '"Select Mods Directory"')
content = content.replace('text="Sprocket Directory:"', 'text="Mods Directory:"')
content = content.replace('self.sprocket_dir', 'self.mods_dir')
content = content.replace('def browse_sprocket(self):', 'def browse_mods(self):')
content = content.replace('command=self.browse_sprocket', 'command=self.browse_mods')
content = content.replace('sprocket_path = self.sprocket_dir.get().strip()', 'mods_path = self.mods_dir.get().strip()')

# Replace install logic
old_install = """        if not sprocket_path or not os.path.isdir(sprocket_path):
            messagebox.showerror("Error", "Invalid Sprocket directory.")
            return
            
        target_base = os.path.join(sprocket_path, "Sprocket_Data", "StreamingAssets")
        if not os.path.isdir(target_base):
            confirm = messagebox.askyesno("Warning", f"'Sprocket_Data/StreamingAssets' not found in:\\n{sprocket_path}\\n\\nAre you sure this is the correct directory? The folder will be created.")
            if not confirm:
                return
                
        if not zip_path or not os.path.isfile(zip_path):
            messagebox.showerror("Error", "Invalid Mod Zip file.")
            return
            
        self.log(f"Starting installation of: {os.path.basename(zip_path)}")
        self.log(f"Target: {target_base}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                namelist = zf.namelist()
                
                # Find the 'Data/' prefix. It could be 'Data/' or 'Mod/Data/' etc.
                data_prefix = None
                for name in namelist:
                    if name.endswith("Data/") or "/Data/" in name or name.startswith("Data/"):
                        # Extract the exact prefix up to 'Data/'
                        idx = name.find("Data/")
                        if idx != -1:
                            data_prefix = name[:idx + 5] # includes 'Data/'
                            break
                            
                if not data_prefix:
                    self.log("Error: Could not find a 'Data/' directory in the zip file.")
                    messagebox.showerror("Error", "Invalid Mod Zip. No 'Data/' directory found inside.")
                    return
                    
                self.log(f"Found Data directory at prefix: '{data_prefix}'")
                
                extract_count = 0
                for item in namelist:
                    if item.startswith(data_prefix) and not item.endswith("/"):
                        # Calculate relative path inside Data/
                        relative_path = item[len(data_prefix):]
                        if not relative_path:
                            continue
                            
                        # Use os.path.normpath to resolve correct path separators on Windows/Linux
                        target_file_path = os.path.normpath(os.path.join(target_base, relative_path))
                        
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                        
                        # Read from zip and write to disk
                        with zf.open(item) as source, open(target_file_path, "wb") as target:
                            target.write(source.read())
                            
                        self.log(f"Extracted: {relative_path}")
                        extract_count += 1
                        
                self.log(f"Successfully extracted {extract_count} files!")
                messagebox.showinfo("Success", f"Mod installed successfully!\\n{extract_count} files extracted.")"""

new_install = """        if not mods_path:
            messagebox.showerror("Error", "Mods directory is not set.")
            return
            
        target_base = mods_path
        if not os.path.isdir(target_base):
            try:
                os.makedirs(target_base, exist_ok=True)
                self.log(f"Created Mods directory at: {target_base}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create Mods directory:\\n{e}")
                return
                
        if not zip_path or not os.path.isfile(zip_path):
            messagebox.showerror("Error", "Invalid Mod Zip file.")
            return
            
        # Determine mod name from zip filename
        zip_filename = os.path.basename(zip_path)
        mod_name = os.path.splitext(zip_filename)[0]
        mod_target_dir = os.path.join(target_base, mod_name)
            
        self.log(f"Starting installation of: {zip_filename}")
        self.log(f"Target: {mod_target_dir}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                namelist = zf.namelist()
                
                # Determine the common root folder in the zip (e.g. 'Mod/' or none)
                # We want to extract 'Data' and 'Meta' into the mod_target_dir
                # Find the prefix that contains 'Data/'
                root_prefix = ""
                for name in namelist:
                    if name.endswith("Data/") or "/Data/" in name or name.startswith("Data/"):
                        idx = name.find("Data/")
                        if idx != -1:
                            root_prefix = name[:idx]
                            break
                            
                self.log(f"Detected root prefix in zip: '{root_prefix}'")
                
                extract_count = 0
                for item in namelist:
                    if item.startswith(root_prefix) and not item.endswith("/"):
                        # Calculate relative path
                        relative_path = item[len(root_prefix):]
                        if not relative_path:
                            continue
                            
                        # Use os.path.normpath to resolve correct path separators on Windows/Linux
                        target_file_path = os.path.normpath(os.path.join(mod_target_dir, relative_path))
                        
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                        
                        # Read from zip and write to disk
                        with zf.open(item) as source, open(target_file_path, "wb") as target:
                            target.write(source.read())
                            
                        self.log(f"Extracted: {relative_path}")
                        extract_count += 1
                        
                self.log(f"Successfully extracted {extract_count} files to {mod_target_dir}!")
                messagebox.showinfo("Success", f"Mod installed successfully!\\n{extract_count} files extracted to {mod_name}.")"""

content = content.replace(old_install, new_install)

with open("Modloader.py", "w") as f:
    f.write(content)
