import os
import re
import sys
import glob
import base64
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def get_redragon_pids():
    """Detecta exclusivamente PIDs bajo el fabricante VID_3554 (Redragon)."""
    pids = set()
    ps_cmd = (
        "Get-PnpDevice -Class 'HIDClass' | "
        "Where-Object { $_.InstanceId -match 'VID_3554&PID_([0-9A-Fa-f]{4})' } | "
        "ForEach-Object { [regex]::Matches($_.InstanceId, 'VID_3554&PID_([0-9A-Fa-f]{4})').Groups[1].Value }"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        for line in result.stdout.strip().splitlines():
            clean_pid = line.strip().upper()
            if len(clean_pid) == 4:
                pids.add(clean_pid)
    except Exception as e:
        print(f"Error consultando hardware: {e}")
    return sorted(list(pids))

def get_wired_pid_from_ini(cfg_path):
    """Lee Config.ini y extrae el PID del mouse con cable (M_PID) para descartarlo."""
    if not os.path.isfile(cfg_path):
        return None
    try:
        with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("M_PID="):
                    b64 = line.split("=", 1)[1].strip()
                    decoded = base64.b64decode(b64).decode("utf-8", errors="ignore")
                    # Formato habitual: RedragonXXXX -> extrae los últimos 4 dígitos hex
                    clean = decoded.replace("Redragon", "").strip().upper()
                    if len(clean) == 4:
                        return clean
    except Exception:
        pass
    return None

def find_default_config_path():
    """Busca Config.ini en rutas comunes de instalacion de Redragon."""
    patterns = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Redragon*\Config.ini"),
        os.path.expandvars(r"%ProgramFiles%\Redragon*\Config.ini"),
    ]
    for p in patterns:
        matches = glob.glob(p)
        if matches:
            return matches[0]
    return ""

class RedragonFixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Redragon Dongle PID Fixer")
        self.root.geometry("540x380")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use("clam")

        frame = ttk.Frame(root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # 1. Ruta Config.ini
        ttk.Label(frame, text="Ruta de Config.ini:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 2))
        path_box = ttk.Frame(frame)
        path_box.pack(fill=tk.X, pady=(0, 12))

        self.path_entry = ttk.Entry(path_box)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.path_entry.insert(0, find_default_config_path())

        browse_btn = ttk.Button(path_box, text="Buscar...", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)

        # 2. Dongle detectado
        ttk.Label(frame, text="Receptor USB detectado (PID):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 2))
        dongle_box = ttk.Frame(frame)
        dongle_box.pack(fill=tk.X, pady=(0, 12))

        self.pid_combo = ttk.Combobox(dongle_box, state="normal")
        self.pid_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        detect_btn = ttk.Button(dongle_box, text="Refrescar", command=self.scan_dongles)
        detect_btn.pack(side=tk.RIGHT)

        # 3. Log de estado
        ttk.Label(frame, text="Registro:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 2))
        self.log_txt = tk.Text(frame, height=7, state=tk.DISABLED, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.log_txt.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        # 4. Botón de aplicar
        self.apply_btn = ttk.Button(frame, text="Parchear Config.ini", command=self.apply_fix)
        self.apply_btn.pack(fill=tk.X)

        self.scan_dongles()

    def log(self, text):
        self.log_txt.config(state=tk.NORMAL)
        self.log_txt.insert(tk.END, text + "\n")
        self.log_txt.see(tk.END)
        self.log_txt.config(state=tk.DISABLED)

    def browse_file(self):
        f = filedialog.askopenfilename(
            title="Seleccionar Config.ini",
            filetypes=[("Archivos INI", "Config.ini"), ("Todos los archivos", "*.*")]
        )
        if f:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, f)
            self.scan_dongles()

    def scan_dongles(self):
        self.log("Buscando periféricos Redragon (VID 3554)...")
        all_pids = get_redragon_pids()
        cfg_path = self.path_entry.get().strip()
        wired_pid = get_wired_pid_from_ini(cfg_path)

        # Filtrar el PID del cable si se detectó
        dongle_candidates = [p for p in all_pids if p != wired_pid]

        if dongle_candidates:
            self.pid_combo['values'] = dongle_candidates
            self.pid_combo.current(0)
            target = dongle_candidates[0]
            self.log(f"[OK] Receptor inalámbrico detectado automáticamente: {target}")
            if wired_pid and wired_pid in all_pids:
                self.log(f"[INFO] Dispositivo cableado ignorado: {wired_pid}")
        elif all_pids:
            self.pid_combo['values'] = all_pids
            self.pid_combo.current(0)
            self.log(f"[!] Dispositivo detectado: {all_pids[0]}")
        else:
            self.log("[!] No se detectó dongle Redragon. Verificá que esté conectado.")

    def apply_fix(self):
        cfg_path = self.path_entry.get().strip()
        pid = self.pid_combo.get().strip().upper()

        if not os.path.isfile(cfg_path):
            messagebox.showerror("Error", "No se encontró el archivo Config.ini en la ruta indicada.")
            return

        if len(pid) != 4:
            messagebox.showerror("Error", "El PID debe tener exactamente 4 caracteres hexadecimales (ej. F5D5).")
            return

        # Generar Base64: Redragon + PID
        raw_str = f"Redragon{pid}"
        b64_pid = base64.b64encode(raw_str.encode("utf-8")).decode("utf-8")

        try:
            with open(cfg_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            new_lines = []
            modified_dpid = False
            modified_offline = False

            for line in lines:
                if line.startswith("D_PID="):
                    new_lines.append(f"D_PID={b64_pid}\n")
                    modified_dpid = True
                elif line.startswith("OfflineCantIn="):
                    new_lines.append("OfflineCantIn=0\n")
                    modified_offline = True
                else:
                    new_lines.append(line)

            with open(cfg_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            self.log(f"[EXITO] D_PID actualizado a: {b64_pid} ({raw_str})")
            if modified_offline:
                self.log("[EXITO] OfflineCantIn cambiado a 0.")
            messagebox.showinfo(
                "Listo",
                f"Config.ini parcheado con éxito para el PID {pid}.\nYa podés reiniciar el software de Redragon."
            )
        except PermissionError:
            messagebox.showerror("Error de Permisos", "No se pudo guardar el archivo. Ejecutá la aplicación como Administrador.")
        except Exception as ex:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {ex}")

if __name__ == "__main__":
    if os.name == 'nt' and not is_admin():
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(f'"{arg}"' for arg in sys.argv), None, 1)
        sys.exit()

    root = tk.Tk()
    app = RedragonFixerApp(root)
    root.mainloop()