model: `Qwen/Qwen3-ASR-0.6B-hf`  dtype: `bfloat16`  normaliser: `basic`  n = 2620 utterances

| condition | WER | 95% CI | gap vs clean, paired 95% CI | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 2.29% | 2.11–2.49 | — | 983 / 128 / 93 | 52576 | 0.015 |
| g711u | 2.38% | 2.20–2.59 | +0.09 pp [+0.04, +0.16] | 1019 / 142 / 92 | 52576 | 0.014 |
| pots | 2.57% | 2.39–2.78 | +0.28 pp [+0.21, +0.37] | 1093 / 157 / 103 | 52576 | 0.013 |
