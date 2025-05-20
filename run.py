import subprocess
import os
import platform

def open_terminal_and_run(command, cwd=None):
    system = platform.system()

    if system == "Darwin":  # macOS
        subprocess.Popen(['osascript', '-e',
                          f'tell application "Terminal" to do script "cd {cwd} && {command}"'])
    elif system == "Linux":
        subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'cd {cwd} && {command}; exec bash'])
    elif system == "Windows":
        subprocess.Popen(f'start cmd /K "cd /d {cwd} && {command}"', shell=True)
    else:
        raise OSError("Sistema operacional não suportado.")

# Caminhos relativos
backend_path = os.path.join(os.getcwd(), "backend")
frontend_path = os.path.join(os.getcwd(), "frontend")

# Comandos
backend_cmd = "python main.py"
frontend_cmd = "npm start"

# Abrindo dois terminais
open_terminal_and_run(backend_cmd, cwd=backend_path)
open_terminal_and_run(frontend_cmd, cwd=frontend_path)