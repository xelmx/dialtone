normaliser: `whisper_en`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | clean | 200 | 80 ms [80, 100] | 520 ms [440, 680] | 98% | 40.4 [31.2, 53.3] | 30.0 [26.7, 33.3] | 0.40 [0.30, 0.55] | 0.40 s [0.37, 0.43] | 0.069 | 12.4 | 54 | 2 | 166 |
| parakeet-tdt-0.6b-v3 | pots_babble10 | 200 | 160 ms [160, 180] | 960 ms [780, 1180] | 96% | 78.1 [44.7, 123.2] | 31.6 [26.7, 36.4] | 0.89 [0.39, 1.55] | 0.35 s [0.31, 0.38] | 0.355 | 12.4 | 118 | 4 | 816 |
| qwen3-asr-0.6b | clean | 200 | 130 ms [120, 140] | 420 ms [400, 440] | 98% | 9.3 [7.7, 11.2] | 4.3 [3.7, 6.2] | 0.09 [0.08, 0.10] | 0.34 s [0.30, 0.37] | 0.213 | 12.4 | 0 | 0 | 75 |
| qwen3-asr-0.6b | pots_babble10 | 200 | 160 ms [160, 180] | 500 ms [480, 520] | 96% | 19.8 [16.7, 23.5] | 10.0 [8.0, 13.3] | 0.15 [0.14, 0.17] | 0.34 s [0.30, 0.37] | 0.212 | 12.4 | 0 | 0 | 76 |
| whisper-turbo | clean | 200 | 100 ms [100, 120] | 440 ms [420, 461] | 98% | 21.9 [16.9, 28.7] | 15.0 [12.5, 16.7] | 0.20 [0.18, 0.22] | 0.36 s [0.32, 0.39] | 0.374 | 12.4 | 1 | 0 | 77 |
| whisper-turbo | pots_babble10 | 200 | 160 ms [140, 160] | 620 ms [540, 700] | 96% | 44.3 [34.5, 58.4] | 28.9 [25.0, 31.8] | 0.44 [0.35, 0.62] | 0.31 s [0.28, 0.35] | 0.377 | 12.4 | 1 | 1 | 148 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | pots_babble10 | +80 [+60, +100] ms | +440 [+200, +700] ms | +37.6 [+1.5, +83.0] | +1.6 [-4.0, +7.8] | +0.49 [-0.02, +1.18] | -0.06 [-0.09, -0.02] s |
| qwen3-asr-0.6b | pots_babble10 | +30 [+20, +40] ms | +80 [+60, +100] ms | +10.5 [+7.6, +13.3] | +5.7 [+3.3, +8.3] | +0.06 [+0.04, +0.08] | -0.00 [-0.03, +0.03] s |
| whisper-turbo | pots_babble10 | +60 [+20, +60] ms | +180 [+100, +260] ms | +22.4 [+12.6, +35.0] | +13.9 [+10.3, +17.2] | +0.24 [+0.14, +0.41] | -0.04 [-0.08, -0.01] s |
