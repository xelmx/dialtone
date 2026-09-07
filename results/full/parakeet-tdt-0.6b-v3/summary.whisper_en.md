model: `C:/Users/lyle/Projects/models/stt/parakeet-tdt-0.6b-v3`  dtype: `float32`  normaliser: `whisper_en`  n = 2620 utterances

| condition | WER | 95% CI | gap vs clean, paired 95% CI | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 1.93% | 1.77–2.09 | — | 765 / 127 / 129 | 53027 | 0.007 |
| g711u | 1.98% | 1.82–2.14 | +0.05 pp [-0.03, +0.13] | 794 / 140 / 114 | 53027 | 0.004 |
| pots | 2.00% | 1.84–2.18 | +0.08 pp [+0.01, +0.15] | 808 / 140 / 114 | 53027 | 0.004 |
