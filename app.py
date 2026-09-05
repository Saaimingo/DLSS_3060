"""DLSS_3060 Tuner — UI real para RTX 3060"""
import tkinter as tk
from tkinter import ttk
import json, threading, time
from pathlib import Path
import sys

# permite rodar mesmo sem pynvml (mostra mock)
try:
    from sensor import Sensor
    HAS_SENSOR = True
except:
    HAS_SENSOR = False

from actuator import decide_scale, load_config

CONFIG = Path(__file__).with_name("config.json")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DLSS_3060 Tuner — RTX 3060 12GB")
        self.geometry("560x420")
        self.configure(bg="#0f0f0f")
        # tenta carregar config
        self.cfg = load_config()
        self.running = False
        self.sensor = Sensor() if HAS_SENSOR else None

        # Estilo
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0f0f0f", foreground="#e5e5e5", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="#00e5a0")
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TFrame", background="#0f0f0f")

        ttk.Label(self, text="DLSS_3060 Tuner", style="Title.TLabel").pack(pady=12)
        ttk.Label(self, text=f"Alvo {self.cfg['target_fps']} FPS • Histerese {self.cfg['hysteresis_frames']} frames • {self.sensor.name if self.sensor else 'SEM SENSOR'}").pack()

        # Status card
        card = tk.Frame(self, bg="#1a1a1a", bd=0, highlightthickness=0)
        card.pack(pady=16, padx=20, fill="x")
        self.lbl_scale = tk.Label(card, text="77% Ultra Quality", font=("Segoe UI", 22, "bold"), bg="#1a1a1a", fg="#00e5a0")
        self.lbl_scale.pack(pady=10)
        self.lbl_fps = tk.Label(card, text="FPS ~ -- • GPU --% • VRAM -- MB", font=("Consolas", 11), bg="#1a1a1a", fg="#a3a3a3")
        self.lbl_fps.pack()
        self.lbl_temp = tk.Label(card, text="Temp --°C • Power --W", font=("Consolas", 10), bg="#1a1a1a", fg="#737373")
        self.lbl_temp.pack(pady=(0,10))

        # Barra de escalas
        scales = tk.Frame(self, bg="#0f0f0f")
        scales.pack()
        for s, label in zip(self.cfg["render_scales"], self.cfg["labels"]):
            tk.Label(scales, text=f"{s}%", bg="#262626", fg="#e5e5e5", padx=10, pady=4, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)

        # Controles
        ctrl = ttk.Frame(self)
        ctrl.pack(pady=18)
        self.btn_toggle = ttk.Button(ctrl, text="▶  Iniciar Balanceamento (dry-run)", command=self.toggle)
        self.btn_toggle.pack(side="left", padx=6)
        ttk.Button(ctrl, text="Abrir RE4", command=self.open_re4).pack(side="left", padx=6)
        ttk.Button(ctrl, text="GitHub", command=self.open_github).pack(side="left", padx=6)

        # Log
        self.log = tk.Text(self, height=6, bg="#141414", fg="#9ca3af", font=("Consolas", 8), bd=0, padx=8, pady=6)
        self.log.pack(fill="x", padx=20, pady=(0,12))
        self.log.insert("1.0", "[DLSS_3060] Pronto. Clique em Iniciar.\n[INFO] RHI + SF-v2 já em RE4. Falta só ReShade dxgi via RHI.\n")
        self.log.configure(state="disabled")

        self.current_scale = self.cfg["render_scales"][0]
        self.after(500, self.poll_once)

    def log_msg(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def poll_once(self):
        if self.sensor:
            s = self.sensor.sample()
            # heurística mesma do balancer.py
            fps_est = max(20, 110 - s["gpu_util"] * 0.9)
            desired = decide_scale(fps_est, self.cfg)
            # só atualiza display, sem histerese pro preview
            if not self.running:
                self.current_scale = desired
            self.lbl_fps.config(text=f"FPS ~{fps_est:.0f} • GPU {s['gpu_util']}% • VRAM {s['vram_used_mb']}/{s['vram_total_mb']} MB")
            self.lbl_temp.config(text=f"Temp {s['temp_c']}°C • Power {s['power_w']:.1f}W")
            idx = self.cfg["render_scales"].index(self.current_scale) if self.current_scale in self.cfg["render_scales"] else 0
            self.lbl_scale.config(text=f"{self.current_scale}% {self.cfg['labels'][idx]}")
        self.after(600, self.poll_once)

    def toggle(self):
        if not self.running:
            self.running = True
            self.btn_toggle.config(text="⏸  Pausar")
            self.log_msg("[BALANCER] Iniciado em dry-run (não escreve ainda). Use --live no balancer.py pra RE4 real.")
            threading.Thread(target=self.loop, daemon=True).start()
        else:
            self.running = False
            self.btn_toggle.config(text="▶  Iniciar Balanceamento (dry-run)")
            self.log_msg("[BALANCER] Pausado.")

    def loop(self):
        from balancer import estimate_fps
        # usa balancer com histerese real
        cfg = self.cfg
        hysteresis = 0
        stable = self.current_scale
        while self.running:
            s = self.sensor.sample() if self.sensor else {"gpu_util": 40, "vram_used_mb": 0, "vram_total_mb": 12288, "power_w": 0, "temp_c": 0}
            fps = estimate_fps(s)
            desired = decide_scale(fps, cfg)
            if desired != stable:
                hysteresis += 1
                if hysteresis >= cfg["hysteresis_frames"]:
                    stable = desired
                    hysteresis = 0
                    self.current_scale = stable
                    self.log_msg(f"→ {stable}% (FPS ~{fps:.0f} util {s['gpu_util']}%)")
            else:
                hysteresis = 0
            time.sleep(cfg["sampling_ms"]/1000)

    def open_re4(self):
        import subprocess
        exe = self.cfg.get("game_exe", "")
        if Path(exe).exists():
            self.log_msg(f"[LAUNCH] Abrindo RE4...")
            subprocess.Popen([exe], cwd=str(Path(exe).parent))
        else:
            self.log_msg("[ERRO] RE4 não encontrado. Verifique Steam.")

    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/Saaimingo/DLSS_3060")

if __name__ == "__main__":
    App().mainloop()
