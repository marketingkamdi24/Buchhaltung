"""Utility functions."""
import socket
import subprocess
import sys


def find_available_port(start_port: int = 7860, end_port: int = 7880) -> int:
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available port in range {start_port}-{end_port}")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def kill_process_on_port(port: int):
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['netstat', '-ano', '-p', 'tcp'], capture_output=True, text=True)
            pid = None
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        break
            if pid:
                subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
                return True, f"Killed process {pid}"
            return False, "No process found"
        else:
            result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
            if result.stdout.strip():
                for pid in result.stdout.strip().split('\n'):
                    subprocess.run(['kill', '-9', pid], check=True)
                return True, "Killed process"
            return False, "No process found"
    except Exception as e:
        return False, f"Error: {e}"


def ensure_output_directory(base_path=None):
    from pathlib import Path
    if base_path is None:
        base_path = Path(__file__).parent.parent.parent
    output_dir = base_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def validate_date_format(date_str: str):
    import re
    from datetime import datetime
    if not date_str:
        return False, "Date empty"
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_str):
        return False, "Use DD.MM.YYYY format"
    try:
        day, month, year = date_str.split('.')
        parsed_date = datetime(int(year), int(month), int(day))
        return True, parsed_date.strftime('%d.%m.%Y')
    except ValueError as e:
        return False, f"Invalid date: {e}"
