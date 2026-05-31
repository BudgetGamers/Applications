import os

with open("Modloader.py", "r") as f:
    content = f.read()

# Remove Install button from Toolbar
content = content.replace('tk.Button(toolbar, text="Install from Zip", bg=self.hl_color, fg="#ffffff", \n                  command=self.install_mod_from_zip, font=("Helvetica", 10, "bold"), bd=0, padx=10, pady=5).pack(side="left", padx=5, pady=5)', '')

# Remove install_mod_from_zip method
import re
content = re.sub(r'    def install_mod_from_zip\(self\):.*', '', content, flags=re.DOTALL)

with open("Modloader.py", "w") as f:
    f.write(content)
