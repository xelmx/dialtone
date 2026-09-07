model: `Qwen/Qwen3-ASR-0.6B-hf`  dtype: `bfloat16`  normaliser: `basic`  n = 200 utterances

| condition | WER | 95% CI | vs clean | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 2.38% | 1.73–3.18 | — | 83 / 10 / 7 | 4196 | 0.023 |
| g711u | 2.50% | 1.86–3.34 | +0.12 pp (+5%) | 89 / 10 / 6 | 4196 | 0.023 |
| pots | 2.67% | 2.01–3.47 | +0.29 pp (+12%) | 94 / 13 / 5 | 4196 | 0.023 |
