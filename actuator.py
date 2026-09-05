"""actuator.py — escreve render scale no reshade.ini / preset (dry-run por padrão)"""
from __future__ import annotations
import json
from pathlib import Path

CONFIG = Path(__file__).with_name("config.json")

def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))

def decide_scale(fps_est: float, cfg: dict) -> int:
    """Curva simples: quanto menor FPS, menor scale (mais performance)"""
    target = cfg["target_fps"]
    min_fps = cfg["min_fps"]
    scales = cfg["render_scales"]
    if fps_est >= target:
        return scales[0]  # 77 Ultra Quality
    if fps_est >= target - 10:
        return scales[1]  # 66 Quality
    if fps_est >= min_fps:
        return scales[2]  # 58 Balanced
    return scales[3]  # 50 Performance

def apply_scale(scale: int, dry_run: bool = True) -> str:
    cfg = load_config()
    msg = f"[Actuator] -> {scale}% ({cfg['labels'][cfg['render_scales'].index(scale)]}) dry_run={dry_run}"
    if dry_run:
        return msg + " (não escreveu)"
    # TODO: escrever em reshade.ini [renodx] ou ReShadePreset.ini quando jogo alvo definido
    # Path(cfg["reshade_ini"]).write_text(...)
    return msg + " (escrito)"

if __name__ == "__main__":
    for fps in [62, 55, 48, 38, 28]:
        cfg = load_config()
        s = decide_scale(fps, cfg)
        print(f"FPS {fps} -> {apply_scale(s, dry_run=True)}")
