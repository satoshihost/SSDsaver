import subprocess

class ServiceManager:
    SERVICE_NAME = "log2ram"

    def get_status(self):
        """Returns the status of the log2ram service."""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", self.SERVICE_NAME],
                capture_output=True, text=True
            )
            return result.stdout.strip()
        except Exception as e:
            return "unknown"

    def _run_command(self, action):
        """Runs a systemctl command with pkexec."""
        try:
            cmd = ["pkexec", "systemctl", action, self.SERVICE_NAME]
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to {action} service: {e}")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def restart_service(self):
        """Restarts the log2ram service. Requires root."""
        return self._run_command("restart")

    def stop_service(self):
        """Stops the log2ram service. Requires root."""
        return self._run_command("stop")

    def start_service(self):
        """Starts the log2ram service. Requires root."""
        return self._run_command("start")
