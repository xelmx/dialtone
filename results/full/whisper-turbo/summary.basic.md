model: `C:/Users/lyle/Projects/models/stt/whisper-large-v3-turbo`  dtype: `float16`  normaliser: `basic`  n = 2620 utterances

| condition | WER | 95% CI | gap vs clean, paired 95% CI | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 3.49% | 3.23–3.76 | — | 1302 / 175 / 356 | 52576 | 0.027 |
| g711u | 3.05% | 2.83–3.29 | -0.44 pp [-0.60, -0.28] | 1180 / 157 / 264 | 52576 | 0.027 |
| pots | 3.24% | 2.96–3.58 | -0.25 pp [-0.46, +0.01] | 1210 / 211 / 282 | 52576 | 0.027 |
