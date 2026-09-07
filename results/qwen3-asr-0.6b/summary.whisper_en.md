model: `Qwen/Qwen3-ASR-0.6B-hf`  dtype: `bfloat16`  normaliser: `whisper_en`  n = 200 utterances

| condition | WER | 95% CI | vs clean | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 2.11% | 1.47–2.82 | — | 70 / 12 / 7 | 4227 | 0.023 |
| g711u | 2.25% | 1.61–3.00 | +0.14 pp (+7%) | 76 / 12 / 7 | 4227 | 0.023 |
| pots | 2.46% | 1.78–3.21 | +0.35 pp (+17%) | 82 / 15 / 7 | 4227 | 0.023 |
