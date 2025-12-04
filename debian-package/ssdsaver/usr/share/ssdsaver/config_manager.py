import os
import tempfile
import subprocess

class ConfigManager:
    CONFIG_PATH = "/etc/log2ram.conf"

    def __init__(self):
        self.config = {}
        self.raw_lines = []

    def read_config(self):
        """Reads the log2ram configuration file."""
        self.config = {
            "SIZE": "40M",
            "USE_RSYNC": "false",
            "MAIL": "true",
            "ZL2R": "false"
        }
        self.raw_lines = []

        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, 'r') as f:
                    self.raw_lines = f.readlines()
                
                for line in self.raw_lines:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        self.config[key.strip()] = value.strip().strip('"')
            except Exception as e:
                print(f"Error reading config: {e}")
        
        return self.config

    def save_config(self, new_config):
        """Writes the configuration to the file. Requires root privileges."""
        # Update internal config
        self.config.update(new_config)
        
        # Generate new file content preserving comments
        new_lines = []
        # If we have no raw lines (e.g. file didn't exist), we should probably create a basic template
        # But for now, let's assume if it doesn't exist, we just write simple key=values
        if not self.raw_lines:
             for key, value in self.config.items():
                 new_lines.append(f'{key}="{value}"\n')
        else:
            # Map of keys we want to update
            keys_to_update = list(new_config.keys())
            
            for line in self.raw_lines:
                stripped = line.strip()
                updated = False
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = stripped.split("=", 1)[0].strip()
                    if key in keys_to_update:
                        # Preserve the original formatting (quotes etc) if possible, 
                        # but standard log2ram.conf uses quotes.
                        new_lines.append(f'{key}="{self.config[key]}"\n')
                        keys_to_update.remove(key)
                        updated = True
                
                if not updated:
                    new_lines.append(line)
            
            # Append any new keys that weren't in the original file
            for key in keys_to_update:
                new_lines.append(f'{key}="{self.config[key]}"\n')

        # Write to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.writelines(new_lines)
            temp_path = temp.name

        # Move temp file to /etc/log2ram.conf using pkexec
        try:
            # We use 'cp' instead of 'mv' to ensure ownership/permissions of destination might be preserved 
            # (though cp will overwrite). 
            # Better to use 'install' or just 'cp' and then 'rm'.
            # Let's use a shell command string for pkexec to handle the copy
            cmd = ["pkexec", "sh", "-c", f"cp '{temp_path}' '{self.CONFIG_PATH}' && rm '{temp_path}'"]
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to save config: {e}")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
