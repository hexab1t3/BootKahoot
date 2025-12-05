import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import google.generativeai as genai
import pyautogui
import keyboard
import threading
import time
import json
import os
from PIL import ImageGrab

print("--- INICIANDO EL PROGRAMA (DARK MODE) ---")

CONFIG_FILE = "kahoot_config.json"

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
        self.model = None
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

        tk.Label(frame, text="Presiona 'K' para activar", bg=COL_BG, fg=COL_ACCENT).pack(pady=5)

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
            except: pass

    def save_config(self):
        data = {
            "api_key": self.api_key.get(),
            "capture_area": self.capture_area,
            "button_coords": self.button_coords,
            "model_name": self.selected_model_name.get()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)

    def update_ui_status(self):
        if self.capture_area: self.lbl_area.config(text=f"✔ Área OK", fg=COL_SUCCESS)
        if all(self.button_coords.values()): self.lbl_buttons.config(text="✔ Botones OK", fg=COL_SUCCESS)
        
        if self.model and self.capture_area and all(self.button_coords.values()):
            self.lbl_status.config(text="LISTO (K)", fg=COL_SUCCESS)
        else:
            self.lbl_status.config(text="CONFIGURAR", fg="orange")

    def fetch_models(self):
        key = self.api_key.get().strip()
        if not key: return messagebox.showerror("Error", "Pon la API Key primero")
        
        self.log("Buscando modelos...")
        try:
            genai.configure(api_key=key)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
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
            genai.configure(api_key=self.api_key.get())
            self.model = genai.GenerativeModel(model_name=model_name, generation_config={"temperature": 0.0})
            self.log(f"Conectado a: {model_name}")
            self.save_config()
            self.update_ui_status()
        except Exception as e:
            self.log(f"Fallo conexión: {e}")
            messagebox.showerror("Error", str(e))

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
        if self.is_running or not self.model: return
        threading.Thread(target=self.process).start()

    def process(self):
        self.is_running = True
        self.root.after(0, lambda: self.lbl_status.config(text="⌛ ...", fg=COL_SUCCESS))
        try:
            img = ImageGrab.grab(bbox=self.capture_area)
            t0 = time.time()
            res = self.model.generate_content(["Responde SOLO: ROJO, AZUL, AMARILLO, VERDE.", img])
            txt = res.text.strip().upper()
            dt = time.time() - t0
            
            self.root.after(0, lambda: self.log(f"🤖 ({dt:.2f}s): {txt}"))
            
            detected = None
            if "ROJO" in txt: detected = "rojo"
            elif "AZUL" in txt: detected = "azul"
            elif "AMARILLO" in txt: detected = "amarillo"
            elif "VERDE" in txt: detected = "verde"
            
            if detected and self.button_coords[detected]:
                self.root.after(0, lambda: self.lbl_status.config(text=f"CLICK {detected.upper()}", fg=COL_ACCENT))
                pyautogui.click(self.button_coords[detected])
            else:
                self.root.after(0, lambda: self.lbl_status.config(text="?", fg=COL_WARN))
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Err: {e}"))
        finally:
            self.is_running = False
            time.sleep(0.5)
            if self.model: self.root.after(0, lambda: self.lbl_status.config(text="LISTO (K)", fg=COL_SUCCESS))

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = KahootBotApp(root)
        root.mainloop()
    except Exception as e:
        print(f"ERROR FATAL: {e}")