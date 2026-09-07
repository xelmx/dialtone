model: `C:/Users/lyle/Projects/models/stt/whisper-large-v3-turbo`  dtype: `float16`  normaliser: `whisper_en`  n = 2620 utterances

| condition | WER | 95% CI | gap vs clean, paired 95% CI | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 1.91% | 1.74–2.09 | — | 755 / 157 / 100 | 53027 | 0.027 |
| g711u | 1.94% | 1.77–2.12 | +0.03 pp [-0.05, +0.11] | 758 / 158 / 111 | 53027 | 0.027 |
| pots | 2.11% | 1.88–2.39 | +0.20 pp [+0.04, +0.42] | 793 / 208 / 117 | 53027 | 0.027 |
