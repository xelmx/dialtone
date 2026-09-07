model: `Qwen/Qwen3-ASR-0.6B-hf`  dtype: `bfloat16`  normaliser: `whisper_en`  n = 2620 utterances

| condition | WER | 95% CI | gap vs clean, paired 95% CI | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 2.13% | 1.95–2.32 | — | 874 / 160 / 93 | 53027 | 0.015 |
| g711u | 2.21% | 2.04–2.41 | +0.09 pp [+0.03, +0.15] | 904 / 175 / 94 | 53027 | 0.014 |
| pots | 2.37% | 2.20–2.58 | +0.25 pp [+0.18, +0.33] | 974 / 179 / 106 | 53027 | 0.013 |
