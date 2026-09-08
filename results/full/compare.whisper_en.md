normaliser: `whisper_en`  n = 2620 utterances

**WER by condition**

| model | clean | g711u | pots | pink10 | babble10 | pots_babble10 | opus12 | opus8 | RTF (clean) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 (`float32`) | 1.93% | 1.98% | 2.00% | 2.36% | 3.91% | 4.79% | 1.99% | 2.16% | 0.007 |
| qwen3-asr-0.6b (`bfloat16`) | 2.13% | 2.21% | 2.37% | 2.56% | 3.53% | 5.25% | 2.18% | 2.52% | 0.015 |
| whisper-turbo (`float16`) | 1.91% | 1.94% | 2.11% | 2.37% | 3.36% | 5.60% | 1.96% | 2.17% | 0.027 |

**Gap vs clean, percentage points, paired bootstrap 95% CI** (an interval that excludes 0 means the condition really moved the model)

| model | g711u | pots | pink10 | babble10 | pots_babble10 | opus12 | opus8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | +0.05 pp [-0.03, +0.13] | +0.08 pp [+0.01, +0.15] | +0.43 pp [+0.33, +0.54] | +1.99 pp [+1.75, +2.26] | +2.87 pp [+2.64, +3.10] | +0.06 pp [+0.01, +0.13] | +0.24 pp [+0.14, +0.34] |
| qwen3-asr-0.6b | +0.09 pp [+0.03, +0.15] | +0.25 pp [+0.18, +0.33] | +0.43 pp [+0.35, +0.52] | +1.41 pp [+1.26, +1.57] | +3.12 pp [+2.89, +3.35] | +0.06 pp [-0.01, +0.11] | +0.39 pp [+0.31, +0.48] |
| whisper-turbo | +0.03 pp [-0.05, +0.11] | +0.20 pp [+0.04, +0.42] | +0.46 pp [+0.33, +0.57] | +1.45 pp [+1.22, +1.71] | +3.69 pp [+3.04, +4.92] | +0.05 pp [-0.05, +0.15] | +0.26 pp [+0.15, +0.37] |
