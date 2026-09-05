"""balancer.py — loop principal: sensor -> decide -> atua"""
from __future__ import annotations
import time
import json
from pathlib import Path
from sensor import Sensor
from actuator import decide_scale, apply_scale, load_config

def estimate_fps(sample: dict) -> float:
    # Heurística v1: util alto = fps baixo. Calibrar com jogo real depois.
    # 20% util ~ 90 FPS, 50% ~ 60 FPS, 80% ~ 35 FPS, 95% ~ 25 FPS
    u = sample["gpu_util"]
    # mapeamento linear invertido simples
    fps = max(20, 110 - u * 0.9)
    return fps

def main(dry_run: bool = True, iterations: int = 20):
    cfg = load_config()
    sensor = Sensor()
    print(f"Balancer v0.1 — alvo {cfg['target_fps']} FPS | dry_run={dry_run} | {sensor.name}")
    stable_scale = None
    hysteresis = 0
    for i in range(iterations):
        s = sensor.sample()
        fps_est = estimate_fps(s)
        desired = decide_scale(fps_est, cfg)
        # Histerese simples pra não ficar oscilando
        if desired != stable_scale:
            hysteresis += 1
            if hysteresis >= cfg["hysteresis_frames"]:
                stable_scale = desired
                hysteresis = 0
                print(f"[{i:02d}] util={s['gpu_util']}% vram={s['vram_used_mb']}MB fps~{fps_est:.0f} => {apply_scale(desired, dry_run)}")
            else:
                print(f"[{i:02d}] util={s['gpu_util']}% fps~{fps_est:.0f} (aguardando histerese {hysteresis}/{cfg['hysteresis_frames']})")
        else:
            hysteresis = 0
            print(f"[{i:02d}] util={s['gpu_util']}% fps~{fps_est:.0f} scale {stable_scale}% estável")
        time.sleep(cfg["sampling_ms"]/1000)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true", help="desativa dry-run e escreve de verdade")
    p.add_argument("--iters", type=int, default=20)
    args = p.parse_args()
    main(dry_run=not args.live, iterations=args.iters)
