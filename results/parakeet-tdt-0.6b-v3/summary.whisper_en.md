model: `C:/Users/lyle/Projects/models/stt/parakeet-tdt-0.6b-v3`  dtype: `float32`  normaliser: `whisper_en`  n = 200 utterances

| condition | WER | 95% CI | vs clean | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 1.77% | 1.24–2.36 | — | 54 / 11 / 10 | 4227 | 0.009 |
| g711u | 1.75% | 1.25–2.29 | -0.02 pp (-1%) | 54 / 13 / 7 | 4227 | 0.009 |
| pots | 1.77% | 1.28–2.35 | +0.00 pp (+0%) | 56 / 12 / 7 | 4227 | 0.009 |
