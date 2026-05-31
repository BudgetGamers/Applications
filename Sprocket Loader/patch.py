import os

with open("Modloader.py", "r") as f:
    content = f.read()

undeploy_logic = """
    def _undeploy_zip_mod(self, zip_path, target_base):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            root_prefix = ""
            for name in namelist:
                if name.endswith("Data/") or "/Data/" in name or name.startswith("Data/"):
                    idx = name.find("Data/")
                    if idx != -1:
                        root_prefix = name[:idx]
                        break
                        
            remove_count = 0
            for item in namelist:
                if item.startswith(root_prefix) and not item.endswith("/"):
                    relative_path = item[len(root_prefix):]
                    if not relative_path:
                        continue
                    
                    target_file_path = os.path.normpath(os.path.join(target_base, relative_path))
                    if os.path.isfile(target_file_path):
                        try:
                            os.remove(target_file_path)
                            remove_count += 1
                        except:
                            pass
            self.log(f"  Removed {remove_count} files originally from zip.")

    def _undeploy_dir_mod(self, dir_path, target_base):
        data_dir = os.path.join(dir_path, "Data")
        if not os.path.exists(data_dir):
            data_dir = dir_path
            
        remove_count = 0
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, data_dir)
                dest_file = os.path.normpath(os.path.join(target_base, rel_path))
                
                if os.path.isfile(dest_file):
                    try:
                        os.remove(dest_file)
                        remove_count += 1
                    except:
                        pass
                        
        self.log(f"  Removed {remove_count} files originally from directory.")

if __name__ == "__main__":
"""

content = content.replace('if __name__ == "__main__":', undeploy_logic)

with open("Modloader.py", "w") as f:
    f.write(content)
