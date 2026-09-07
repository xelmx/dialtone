model: `C:/Users/lyle/Projects/models/stt/whisper-large-v3-turbo`  dtype: `float16`  normaliser: `whisper_en`  n = 200 utterances

| condition | WER | 95% CI | vs clean | S / D / I | ref words | RTF |
|---|---:|:---:|---:|:---:|---:|---:|
| clean | 1.73% | 1.19–2.41 | — | 60 / 9 / 4 | 4227 | 0.033 |
| g711u | 1.80% | 1.22–2.44 | +0.07 pp (+4%) | 59 / 10 / 7 | 4227 | 0.032 |
| pots | 1.87% | 1.33–2.49 | +0.14 pp (+8%) | 63 / 7 / 9 | 4227 | 0.042 |
