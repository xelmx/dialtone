normaliser: `whisper_en`  n = 200 utterances

**WER by condition**

| model | clean | g711u | pots | pink10 | babble10 | pots_babble10 | opus12 | opus8 | RTF (clean) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 (`float32`) | 1.77% | 1.75% | 1.77% | 2.20% | 4.02% | 4.64% | 2.03% | 2.01% | 0.009 |
| qwen3-asr-0.6b (`bfloat16`) | 2.11% | 2.25% | 2.46% | 2.70% | 3.83% | 5.02% | 2.32% | 2.63% | 0.023 |
| whisper-turbo (`float16`) | 1.73% | 1.80% | 1.87% | 2.18% | 3.24% | 4.68% | 1.92% | 1.85% | 0.033 |

**Gap vs clean, percentage points, paired bootstrap 95% CI** (an interval that excludes 0 means the condition really moved the model)

| model | g711u | pots | pink10 | babble10 | pots_babble10 | opus12 | opus8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | -0.02 pp [-0.24, +0.21] | +0.00 pp [-0.23, +0.24] | +0.43 pp [+0.05, +0.80] | +2.25 pp [+1.31, +3.70] | +2.86 pp [+2.17, +3.60] | +0.26 pp [+0.00, +0.57] | +0.24 pp [-0.10, +0.65] |
| qwen3-asr-0.6b | +0.14 pp [-0.05, +0.38] | +0.35 pp [+0.09, +0.68] | +0.59 pp [+0.30, +0.91] | +1.73 pp [+1.20, +2.25] | +2.91 pp [+2.31, +3.52] | +0.21 pp [-0.11, +0.53] | +0.52 pp [+0.23, +0.88] |
| whisper-turbo | +0.07 pp [-0.24, +0.37] | +0.14 pp [-0.19, +0.48] | +0.45 pp [+0.10, +0.84] | +1.51 pp [+0.99, +2.12] | +2.96 pp [+2.28, +3.68] | +0.19 pp [-0.12, +0.50] | +0.12 pp [-0.27, +0.55] |
