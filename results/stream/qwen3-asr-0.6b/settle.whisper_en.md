normaliser: `whisper_en`  prefixes: first 1.0 s, step 0.5 s  aligner: `qwen3-forced-aligner-0.6b`

**Settle metrics** (95% bootstrap CI over utterances; lags quantised by the step, read differences not absolutes)

| model | condition | n | median lag | p90 lag | lag defined | revisions /100 (pooled) | revisions /100 (median utt) | unstable tail | agree before end | stream RTF | ×audio | empty partials | exploded partials | max partial words |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3-asr-0.6b | clean | 2620 | 140 ms [120, 140] | 420 ms [420, 420] | 98% | 8.8 [8.3, 9.2] | 5.9 [5.6, 6.2] | 0.10 [0.10, 0.10] | 0.36 s [0.35, 0.36] | 0.202 | 11.7 | 0 | 0 | 96 |
| qwen3-asr-0.6b | pots_babble10 | 2620 | 160 ms [160, 180] | 500 ms [500, 520] | 96% | 20.2 [19.0, 21.5] | 12.5 [11.8, 13.0] | 0.16 [0.15, 0.16] | 0.31 s [0.30, 0.32] | 0.198 | 11.7 | 2 | 0 | 96 |

**Change vs clean, same utterances, paired 95% CI** (an interval that excludes 0 means the condition really changed how the model settles)

| model | condition | Δ median lag | Δ p90 lag | Δ revisions /100 (pooled) | Δ revisions /100 (median utt) | Δ unstable tail | Δ agree before end |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen3-asr-0.6b | pots_babble10 | +20 [+20, +40] ms | +80 [+80, +100] ms | +11.4 [+10.3, +12.8] | +6.6 [+5.9, +7.2] | +0.06 [+0.05, +0.06] | -0.04 [-0.05, -0.04] s |
