"""sensor.py — NVML + estimativa de FPS para RTX 3060"""
from __future__ import annotations
import time
import pynvml

class Sensor:
    def __init__(self):
        pynvml.nvmlInit()
        self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        self.name = pynvml.nvmlDeviceGetName(self.handle)
        if isinstance(self.name, bytes):
            self.name = self.name.decode()

    def sample(self) -> dict:
        mem = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
        power = pynvml.nvmlDeviceGetPowerUsage(self.handle) / 1000.0
        temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
        # Estimativa simples: GPU Util alto + power alto = cena pesada / FPS baixo
        # FPS real virá do ReShade addon log quando disponível
        return {
            "ts": time.time(),
            "gpu_util": util.gpu,
            "mem_util": util.memory,
            "vram_used_mb": mem.used // (1024*1024),
            "vram_total_mb": mem.total // (1024*1024),
            "power_w": power,
            "temp_c": temp,
        }

if __name__ == "__main__":
    s = Sensor()
    print(f"Sensor OK — {s.name}")
    for i in range(5):
        print(s.sample())
        time.sleep(0.5)
