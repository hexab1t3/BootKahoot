import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from google import genai
from google.genai import types
import pyautogui
import keyboard
import threading
import time
import json
import io
import os
import re
import sys
from PIL import ImageGrab, ImageChops, ImageStat

pyautogui.PAUSE = 0          # sin pausa artificial tras cada click
pyautogui.FAILSAFE = False

MAX_IMG_WIDTH = 900          # imagen más chica = respuesta más rápida
AUTO_THRESHOLD = 10          # cuánto debe cambiar la pantalla para contar como pregunta nueva
PROMPT = (
    "Es una captura de una pregunta de Kahoot con sus opciones de colores "
    "(ROJO, AZUL, AMARILLO, VERDE). Elige la opción correcta. "
    "Responde SOLO con una palabra: ROJO, AZUL, AMARILLO o VERDE. "
    "Si en la imagen NO hay una pregunta con opciones para responder, responde SOLO: NINGUNA."
)

# Coordenadas correctas en pantallas con escala (125%, 150%...) en Windows
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

print("--- INICIANDO EL PROGRAMA (DARK MODE) ---")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kahoot_config.json")

# --- PALETA DE COLORES ---
COL_BG = "#121212"        # Fondo principal (Casi negro)
COL_FRAME = "#1E1E1E"     # Fondo de paneles
COL_TEXT = "#E0E0E0"      # Texto principal
COL_ACCENT = "#BB86FC"    # Morado (Botones acción)
COL_SUCCESS = "#03DAC6"   # Cyan/Verde (Éxito)
COL_WARN = "#CF6679"      # Rojo suave (Alertas)
COL_INPUT = "#2C2C2C"     # Fondo de inputs
COL_BTN_TEXT = "#000000"  # Texto de botones

class KahootBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kahoot Bot - Dark Edition")
        self.root.geometry("420x720")
        self.root.attributes('-topmost', True)
        self.root.configure(bg=COL_BG)

        # Variables
        self.api_key = tk.StringVar()
        self.selected_model_name = tk.StringVar()
        self.capture_area = None
        self.button_coords = {"rojo": None, "azul": None, "amarillo": None, "verde": None}
        self.client = None
        self.model_name = None
        self.auto_mode = tk.BooleanVar(value=False)
        self.last_sig = None
        self.is_running = False

        # --- ESTILOS TTK (Para el Combobox) ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=COL_INPUT, background=COL_FRAME, foreground=COL_TEXT, arrowcolor="white")

        # --- INTERFAZ ---
        
        # 1. API HEADER
        self.create_header()

        # 2. CALIBRACIÓN
        self.create_calibration_section()

        # 3. CONTROL Y LOGS
        self.create_control_section()

        # Lógica inicial
        self.load_config()
        keyboard.add_hotkey('k', self.on_hotkey_pressed)
        keyboard.add_hotkey('f8', lambda: self.root.after(0, self.toggle_auto_hotkey))
        threading.Thread(target=self.auto_loop, daemon=True).start()
        self.update_ui_status()
        print("--- VENTANA LISTA ---")

    def create_header(self):
        frame = tk.LabelFrame(self.root, text=" 1. CONEXIÓN ", bg=COL_BG, fg=COL_SUCCESS, font=("Consolas", 10, "bold"), bd=2, relief="groove")
        frame.pack(fill="x", padx=15, pady=10)
        
        # API Input
        tk.Label(frame, text="API Key:", bg=COL_BG, fg=COL_TEXT).pack(anchor="w", padx=5)
        entry = tk.Entry(frame, textvariable=self.api_key, show="*", bg=COL_INPUT, fg="white", insertbackground="white", relief="flat")
        entry.pack(fill="x", padx=5, pady=5, ipady=3)
        
        # Botones Modelos
        tk.Button(frame, text="↻ Buscar Modelos", command=self.fetch_models, 
                 bg="#3700B3", fg="white", activebackground="#6200EE", activeforeground="white", relief="flat", cursor="hand2").pack(fill="x", padx=5, pady=2)
        
        # Combo y Conectar
        tk.Label(frame, text="Modelo:", bg=COL_BG, fg=COL_TEXT).pack(anchor="w", padx=5)
        self.combo_models = ttk.Combobox(frame, textvariable=self.selected_model_name, state="normal")
        self.combo_models.pack(fill="x", padx=5, pady=2)
        
        tk.Button(frame, text="⚡ CONECTAR", command=self.manual_connect, 
                 bg=COL_SUCCESS, fg="black", font=("Arial", 9, "bold"), activebackground="#018786", cursor="hand2").pack(fill="x", padx=5, pady=8)

    def create_calibration_section(self):
        frame = tk.LabelFrame(self.root, text=" 2. CALIBRACIÓN ", bg=COL_BG, fg=COL_ACCENT, font=("Consolas", 10, "bold"), bd=2, relief="groove")
        frame.pack(fill="x", padx=15, pady=5)

        # Área
        btn_area = tk.Button(frame, text="[ A ] DEFINIR ÁREA", command=self.start_area_selection,
                            bg=COL_FRAME, fg="white", activebackground=COL_ACCENT, relief="raised")
        btn_area.pack(fill="x", padx=5, pady=2)
        self.lbl_area = tk.Label(frame, text="⚠ Falta Área", bg=COL_BG, fg=COL_WARN, font=("Arial", 8))
        self.lbl_area.pack()

        # Botones
        btn_btns = tk.Button(frame, text="[ B ] MAPEAR BOTONES", command=self.start_button_calibration,
                            bg=COL_FRAME, fg="white", activebackground=COL_ACCENT, relief="raised")
        btn_btns.pack(fill="x", padx=5, pady=2)
        self.lbl_buttons = tk.Label(frame, text="⚠ Faltan Botones", bg=COL_BG, fg=COL_WARN, font=("Arial", 8))
        self.lbl_buttons.pack(pady=(0,5))

    def create_control_section(self):
        frame = tk.LabelFrame(self.root, text=" 3. JUEGO ", bg=COL_BG, fg="#FF0266", font=("Consolas", 10, "bold"), bd=2, relief="groove")
        frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Status Principal
        self.lbl_status = tk.Label(frame, text="OFFLINE", bg=COL_BG, fg="#555555", font=("Impact", 24))
        self.lbl_status.pack(pady=10)
        
        # Toolbar del Log
        toolbar = tk.Frame(frame, bg=COL_BG)
        toolbar.pack(fill="x", padx=5)
        tk.Label(toolbar, text="Log de Gemini:", bg=COL_BG, fg="gray", font=("Arial", 8)).pack(side="left")
        
        # BOTÓN LIMPIAR
        tk.Button(toolbar, text="🗑 Limpiar", command=self.clear_log, 
                 bg=COL_BG, fg=COL_WARN, font=("Arial", 8, "bold"), bd=0, cursor="hand2").pack(side="right")

        # Log Box
        self.log_box = scrolledtext.ScrolledText(frame, height=10, font=("Consolas", 9), 
                                                bg="#000000", fg="#00FF00", insertbackground="white", state='normal')
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Checkbutton(frame, text="Modo AUTO (responde solo cuando sale una pregunta nueva)  [F8]",
                       variable=self.auto_mode, command=self.on_auto_toggle, bg=COL_BG, fg=COL_SUCCESS,
                       selectcolor=COL_INPUT, activebackground=COL_BG, activeforeground=COL_SUCCESS,
                       font=("Arial", 8, "bold")).pack(pady=(5, 0))
        tk.Label(frame, text="Manual: presiona 'K'", bg=COL_BG, fg=COL_ACCENT).pack(pady=5)

    # --- FUNCIONES ---

    def clear_log(self):
        self.log_box.delete('1.0', tk.END)
        self.log("--- Log Limpiado ---")

    def log(self, text):
        self.log_box.insert(tk.END, f"> {text}\n")
        self.log_box.see(tk.END)
        print(f"LOG: {text}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.api_key.set(data.get("api_key", ""))
                    self.capture_area = data.get("capture_area")
                    self.button_coords = data.get("button_coords", self.button_coords)
                    saved_model = data.get("model_name", "")
                    if saved_model:
                        self.selected_model_name.set(saved_model)
            except Exception: pass

    def save_config(self):
        data = {
            "api_key": self.api_key.get(),
            "capture_area": self.capture_area,
            "button_coords": self.button_coords,
            "model_name": self.selected_model_name.get()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def update_ui_status(self):
        if self.capture_area: self.lbl_area.config(text=f"✔ Área OK", fg=COL_SUCCESS)
        if all(self.button_coords.values()): self.lbl_buttons.config(text="✔ Botones OK", fg=COL_SUCCESS)
        
        if self.client and self.capture_area and all(self.button_coords.values()):
            self.lbl_status.config(text="LISTO (K)", fg=COL_SUCCESS)
        else:
            self.lbl_status.config(text="CONFIGURAR", fg="orange")

    def fetch_models(self):
        key = self.api_key.get().strip()
        if not key: return messagebox.showerror("Error", "Pon la API Key primero")
        
        self.log("Buscando modelos...")
        try:
            client = genai.Client(api_key=key)
            models = [m.name for m in client.models.list() if 'generateContent' in (m.supported_actions or [])]
            self.combo_models['values'] = models
            if models: 
                self.combo_models.set(models[0])
                self.log(f"Encontrados: {len(models)}")
            else:
                self.log("No encontrados. Escribe manual.")
        except Exception as e:
            self.log(f"Error API: {e}")

    def manual_connect(self):
        name = self.selected_model_name.get().strip()
        if not name: return messagebox.showerror("Error", "Escribe o selecciona un modelo")
        self.connect_model(name)

    def connect_model(self, model_name):
        try:
            client = genai.Client(api_key=self.api_key.get().strip())
            name = model_name if model_name.startswith("models/") else f"models/{model_name}"
            client.models.generate_content(model=name, contents="ok",
                                           config=self.make_config())  # calienta la conexión
            self.client, self.model_name = client, name
            self.log(f"Conectado a: {model_name}")
            self.save_config()
            self.update_ui_status()
        except Exception as e:
            self.log(f"Fallo conexión: {e}")
            messagebox.showerror("Error", str(e))

    def make_config(self, thinking=True):
        kw = dict(temperature=0.0, max_output_tokens=64)
        # Sin "pensar" Gemini responde mucho más rápido (solo modelos que lo permiten)
        if thinking and "2.5" in (self.selected_model_name.get() or "") and "pro" not in self.selected_model_name.get():
            kw["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        return types.GenerateContentConfig(**kw)

    # --- CALIBRACIÓN VISUAL ---
    def start_area_selection(self):
        self.root.iconify()
        self.sel_win = tk.Toplevel(self.root)
        self.sel_win.attributes('-fullscreen', True, '-alpha', 0.3, '-topmost', True)
        self.sel_win.config(bg='black') # Oscuro para calibrar
        self.sel_win.bind('<Button-1>', self.on_click_start)
        self.sel_win.bind('<B1-Motion>', self.on_drag)
        self.sel_win.bind('<ButtonRelease-1>', self.on_click_end)
        self.canvas = tk.Canvas(self.sel_win, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def on_click_start(self, e):
        self.start_x, self.start_y = e.x, e.y
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline=COL_SUCCESS, width=3)

    def on_drag(self, e):
        self.canvas.coords(self.rect, self.start_x, self.start_y, e.x, e.y)

    def on_click_end(self, e):
        x1, y1 = min(self.start_x, e.x), min(self.start_y, e.y)
        x2, y2 = max(self.start_x, e.x), max(self.start_y, e.y)
        self.capture_area = (x1, y1, x2, y2)
        self.save_config()
        self.update_ui_status()
        self.sel_win.destroy()
        self.root.deiconify()

    def start_button_calibration(self):
        messagebox.showinfo("Orden", "Click en: ROJO -> AZUL -> AMARILLO -> VERDE")
        self.root.iconify()
        self.cal_win = tk.Toplevel(self.root)
        self.cal_win.attributes('-fullscreen', True, '-alpha', 0.01, '-topmost', True)
        self.cal_win.bind('<Button-1>', self.cal_click)
        self.cal_step = 0
        self.colors = ["rojo", "azul", "amarillo", "verde"]

    def cal_click(self, e):
        if self.cal_step < 4:
            c = self.colors[self.cal_step]
            self.button_coords[c] = (e.x, e.y)
            print(f"Calibrado {c}: {e.x},{e.y}")
            self.cal_step += 1
            if self.cal_step == 4:
                self.cal_win.destroy()
                self.root.deiconify()
                self.save_config()
                self.update_ui_status()

    # --- PROCESO ---
    def on_hotkey_pressed(self):
        if self.is_running or not self.client: return
        # No disparar si se está escribiendo la letra "k" en un campo de texto
        if isinstance(self.root.focus_get(), (tk.Entry, ttk.Combobox, tk.Text)): return
        threading.Thread(target=self.process, daemon=True).start()

    def on_auto_toggle(self):
        if self.auto_mode.get() and not (self.client and self.capture_area and all(self.button_coords.values())):
            self.auto_mode.set(False)
            return messagebox.showwarning("Falta configurar", "Conecta el modelo y calibra área y botones primero.")
        self.last_sig = None
        self.log("Modo AUTO " + ("ACTIVADO" if self.auto_mode.get() else "desactivado"))

    def toggle_auto_hotkey(self):
        self.auto_mode.set(not self.auto_mode.get())
        self.on_auto_toggle()

    @staticmethod
    def signature(img):
        return img.convert("L").resize((48, 48))

    def auto_loop(self):
        """Vigila el área: cuando aparece una pregunta nueva y se estabiliza, responde sola."""
        prev = None
        while True:
            time.sleep(0.2)
            try:
                if not (self.auto_mode.get() and self.client and self.capture_area) or self.is_running:
                    prev = None
                    continue
                sig = self.signature(ImageGrab.grab(bbox=self.capture_area))
                stable = prev is not None and ImageStat.Stat(ImageChops.difference(sig, prev)).mean[0] < 2
                prev = sig
                new_q = self.last_sig is None or ImageStat.Stat(ImageChops.difference(sig, self.last_sig)).mean[0] > AUTO_THRESHOLD
                # contenido "con algo": evita responder a una pantalla casi uniforme
                if stable and new_q and ImageStat.Stat(sig).stddev[0] > 15:
                    self.last_sig = sig
                    self.process()
            except Exception as e:
                self.root.after(0, lambda e=e: self.log(f"Auto err: {e}"))

    def process(self):
        self.is_running = True
        self.root.after(0, lambda: self.lbl_status.config(text="⌛ ...", fg=COL_SUCCESS))
        try:
            t0 = time.time()
            img = ImageGrab.grab(bbox=self.capture_area).convert("RGB")
            if img.width > MAX_IMG_WIDTH:
                img = img.resize((MAX_IMG_WIDTH, int(img.height * MAX_IMG_WIDTH / img.width)))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            parts = [types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"), PROMPT]

            try:
                res = self.client.models.generate_content(model=self.model_name, contents=parts, config=self.make_config())
            except Exception:
                # reintento sin opciones especiales (por si el modelo no admite thinking_config)
                res = self.client.models.generate_content(model=self.model_name, contents=parts, config=self.make_config(thinking=False))
            txt = (res.text or "").strip().upper()
            dt = time.time() - t0

            self.root.after(0, lambda: self.log(f"🤖 ({dt:.2f}s): {txt}"))

            m = re.search(r"ROJO|AZUL|AMARILLO|VERDE", txt)
            detected = m.group(0).lower() if m else None

            if detected and self.button_coords[detected]:
                x, y = self.button_coords[detected]
                pyautogui.click(x, y)
                self.root.after(0, lambda: self.lbl_status.config(text=f"CLICK {detected.upper()}", fg=COL_ACCENT))
            else:
                shown = "…" if "NINGUNA" in txt else "?"
                self.root.after(0, lambda: self.lbl_status.config(text=shown, fg=COL_WARN))

        except Exception as e:
            self.root.after(0, lambda e=e: self.log(f"Err: {e}"))
        finally:
            time.sleep(0.5)
            self.is_running = False
            if self.client: self.root.after(0, lambda: self.lbl_status.config(text="LISTO (K)", fg=COL_SUCCESS))

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = KahootBotApp(root)
        root.mainloop()
    except Exception as e:
        print(f"ERROR FATAL: {e}")