normaliser: `basic`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | clean | 2620 | 100 ms [100, 100] | 600 ms [540, 620] | 98% | 51.4 [46.7, 56.5] | 33.3 [33.3, 35.7] | 0.50 [0.44, 0.57] | 0.38 s [0.37, 0.39] | 0.062 | 11.7 | 919 | 41 | 509 |
| parakeet-tdt-0.6b-v3 | pots_babble10 | 2620 | 200 ms [180, 200] | 1200 ms [1120, 1280] | 95% | 93.9 [83.3, 106.2] | 36.7 [35.0, 38.5] | 1.07 [0.92, 1.25] | 0.32 s [0.31, 0.33] | 0.063 | 11.7 | 1950 | 104 | 1019 |
| qwen3-asr-0.6b | clean | 2620 | 140 ms [120, 140] | 420 ms [420, 420] | 98% | 9.1 [8.7, 9.5] | 6.2 [5.9, 6.7] | 0.10 [0.10, 0.11] | 0.35 s [0.35, 0.36] | 0.202 | 11.7 | 0 | 0 | 96 |
| qwen3-asr-0.6b | pots_babble10 | 2620 | 160 ms [160, 180] | 500 ms [500, 520] | 95% | 20.7 [19.5, 22.0] | 12.5 [12.5, 13.6] | 0.16 [0.16, 0.17] | 0.31 s [0.30, 0.32] | 0.198 | 11.7 | 2 | 0 | 96 |
| whisper-turbo | clean | 2620 | 120 ms [120, 120] | 460 ms [440, 460] | 97% | 30.3 [27.6, 33.4] | 18.2 [17.4, 19.2] | 0.26 [0.23, 0.30] | 0.35 s [0.34, 0.36] | 0.366 | 11.7 | 13 | 9 | 444 |
| whisper-turbo | pots_babble10 | 2620 | 160 ms [160, 160] | 620 ms [600, 640] | 94% | 44.3 [41.0, 47.9] | 30.0 [28.6, 31.2] | 0.44 [0.40, 0.49] | 0.32 s [0.31, 0.33] | 0.361 | 11.7 | 2 | 14 | 302 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | pots_babble10 | +100 [+80, +100] ms | +600 [+540, +700] ms | +42.5 [+30.6, +54.7] | +3.3 [+0.4, +5.1] | +0.57 [+0.40, +0.75] | -0.05 [-0.07, -0.04] s |
| qwen3-asr-0.6b | pots_babble10 | +20 [+20, +40] ms | +80 [+80, +100] ms | +11.6 [+10.5, +12.9] | +6.2 [+5.8, +7.5] | +0.06 [+0.06, +0.07] | -0.05 [-0.05, -0.04] s |
| whisper-turbo | pots_babble10 | +40 [+40, +40] ms | +160 [+140, +180] ms | +14.0 [+9.9, +18.2] | +11.8 [+10.6, +13.2] | +0.18 [+0.13, +0.24] | -0.03 [-0.04, -0.02] s |
