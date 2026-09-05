# DLSS_3060 — AutoBalancer para RTX 3060 12GB

> **"O amor entre performance e beleza do DLSS 5"** — balanceamento automático para série 30 (Ampere)

Baseado no vazamento `nvngx_dlssnr.dll 310.8.0` (NBA 2K27) + patch ShortFuse `310.8.SF-v2` do [RankFTW/RHI](https://github.com/RankFTW/RHI) + injeção [RenoDX](https://github.com/clshortfuse/renodx).

Validado em: **RTX 3060 12GB sm_86 | Driver 616.56 | CUDA 12.4 | RE4 (Steam)**

## Por que existe?

A DLL vazada veio só com `sm_120` (Blackwell/50xx). Na 3060 ela roda em emulação lenta: **-50% FPS** (71→35 FPS na 5070 Ti, pior na 3060). O patcher [dev-camo/dlssnr-patcher](https://github.com/dev-camo/dlssnr-patcher) libera Ampere, mas não otimiza. O RHI instala, mas não balanceia.

Este repo faz o que falta: **ajuste dinâmico de render scale em tempo real para manter 60 FPS com máxima qualidade.**

## Como funciona (v0.1)

```
sensor.py    → NVML: gpu_util, vram, power, temp (pynvml)
actuator.py  → decide scale: 77% Ultra Quality → 66% Quality → 58% Balanced → 50% Performance
balancer.py  → loop 500ms com histerese (6 frames) pra não piscar qualidade
config.json  → curva alvo (target_fps: 60, min_fps: 45)
```

Compatível com RHI — não substitui, roda junto. RHI faz deploy, balancer faz tuning.

> ⚠️ Single-player only. ReShade com addon pode disparar anti-cheat. DLL patchada perde assinatura NVIDIA.

## Instalação

```bash
pip install nvidia-ml-py
python sensor.py        # testa leitura
python actuator.py      # testa curva
python balancer.py      # dry-run (não escreve)
python balancer.py --live --iters 100  # ao vivo (escreve reshade.ini)
```

Para RE4 (sem DLSS nativo), instale antes via RHI: `DLSS5 Feeder + nvngx_dlssnr.dll 310.8.SF-v2`

## Roadmap

- [x] v0.1 sensor + balancer dry-run validado na 3060
- [ ] Ler FPS real do `renodx-dlss5.addon64` (substituir heurística gpu_util)
- [ ] Escrever em `reshade.ini` / `ReShadePreset.ini` ao vivo
- [ ] Calibrar curva com RE4 benchmark
- [ ] Dashboard overlay

## Créditos

- ShortFuse / RenoDX — NR addon e patch SF-v2
- RankFTW/RHI — manifest e deploy (dlssnr 310.8.SF-v2)
- dev-camo/dlssnr-patcher — patch Ampere sm_86

## Licença

MIT — não distribui DLLs da NVIDIA. Use sua cópia de `nvngx_dlssnr.dll`.
