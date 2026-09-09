normaliser: `whisper_en`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3-asr-0.6b | clean | 200 | 130 ms [120, 140] | 420 ms [400, 440] | 98% | 9.3 [7.7, 11.2] | 4.3 [3.7, 6.2] | 0.09 [0.08, 0.10] | 0.34 s [0.30, 0.37] | 0.213 | 12.4 | 0 | 0 | 75 |
| qwen3-asr-0.6b | pots_babble10 | 200 | 160 ms [160, 180] | 500 ms [480, 520] | 96% | 19.8 [16.7, 23.5] | 10.0 [8.0, 13.3] | 0.15 [0.14, 0.17] | 0.34 s [0.30, 0.37] | 0.212 | 12.4 | 0 | 0 | 76 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen3-asr-0.6b | pots_babble10 | +30 [+20, +40] ms | +80 [+60, +100] ms | +10.5 [+7.6, +13.3] | +5.7 [+3.3, +8.3] | +0.06 [+0.04, +0.08] | -0.00 [-0.03, +0.03] s |
