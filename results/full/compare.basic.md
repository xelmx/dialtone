normaliser: `basic`  n = 2620 utterances

**WER by condition**

| model | clean | g711u | pots | pink10 | babble10 | pots_babble10 | opus12 | opus8 | RTF (clean) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 (`float32`) | 2.16% | 2.21% | 2.24% | 2.70% | 4.32% | 5.17% | 2.22% | 2.42% | 0.007 |
| qwen3-asr-0.6b (`bfloat16`) | 2.29% | 2.38% | 2.57% | 2.73% | 3.73% | 5.49% | 2.34% | 2.69% | 0.015 |
| whisper-turbo (`float16`) | 3.49% | 3.05% | 3.24% | 3.47% | 4.09% | 6.28% | 3.14% | 3.18% | 0.027 |

**Gap vs clean, percentage points, paired bootstrap 95% CI** (an interval that excludes 0 means the condition really moved the model)

| model | g711u | pots | pink10 | babble10 | pots_babble10 | opus12 | opus8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | +0.05 pp [-0.03, +0.13] | +0.09 pp [+0.01, +0.17] | +0.55 pp [+0.43, +0.67] | +2.17 pp [+1.92, +2.43] | +3.01 pp [+2.78, +3.26] | +0.07 pp [+0.01, +0.13] | +0.26 pp [+0.17, +0.36] |
| qwen3-asr-0.6b | +0.09 pp [+0.04, +0.16] | +0.28 pp [+0.21, +0.37] | +0.44 pp [+0.36, +0.53] | +1.44 pp [+1.29, +1.60] | +3.20 pp [+2.97, +3.43] | +0.05 pp [-0.01, +0.11] | +0.40 pp [+0.31, +0.49] |
| whisper-turbo | -0.44 pp [-0.60, -0.28] | -0.25 pp [-0.46, +0.01] | -0.02 pp [-0.21, +0.17] | +0.60 pp [+0.32, +0.92] | +2.79 pp [+2.10, +4.05] | -0.34 pp [-0.51, -0.18] | -0.31 pp [-0.49, -0.12] |
