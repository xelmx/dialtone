# dialtone

**How much worse do speech-to-text models get on phone-quality audio?**

Every public speech-to-text leaderboard scores models on clean, 16 kHz studio
recordings. Phone calls are 8 kHz, G.711 mu-law, and band-limited — roughly a
tenth of the audio detail. The model that wins on studio audio is not
necessarily the model that wins on a call, and nobody publishes the gap.

This repo measures it.

## Status: step 3

Three models, one dataset, eight conditions, batch accuracy only. The goal so
far is a defensible number per model and a degradation chain that has been
listened to and argued about — not a leaderboard.

| condition | what it is |
|---|---|
| `clean` | the recording as shipped, 16 kHz |
| `g711u` | anti-aliased down to 8 kHz → G.711 mu-law encode/decode → back to 16 kHz |
| `pots` | as above, plus a 300–3400 Hz band-pass before the codec (classic analogue line) |
| `pink10` | 1/f noise at 10 dB SNR, no line — the stationary-noise control (room, road, HVAC) |
| `babble10` | six other LibriSpeech speakers at 10 dB SNR, no line — background talkers |
| `pots_babble10` | babble at the microphone, *then* the `pots` line — the realistic bad phone call |
| `opus12` | Opus (libopus, `voip`) at 12 kbps — a WebRTC call on poor bandwidth |
| `opus8` | Opus at 8 kbps with a 4 kHz cutoff — narrowband VoIP, the codec-era `pots` |

Noise is added before the line, at a whole-clip RMS signal-to-noise ratio,
seeded from the audio bytes so every run is bit-identical. Babble never
includes the target's own speaker. Opus goes through `ffmpeg`/`libopus`, the
same encoder real clients use, and the decoded audio is aligned back to the
input length.

## Results so far

LibriSpeech test-clean, **all 2620 utterances** (40 speakers), RTX 4060,
Whisper English normaliser. Every gap is WER(condition) − WER(clean) on the
same utterances with a paired bootstrap 95% interval — the number that says
whether a condition actually hurt.

**WER by condition**

| model | clean | g711u | pots | opus12 | opus8 | pink10 | babble10 | pots_babble10 | RTF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| whisper-large-v3-turbo (fp16, 809M) | 1.91% | 1.94% | 2.11% | 1.96% | 2.17% | 2.37% | **3.36%** | 5.60% | 0.027 |
| parakeet-tdt-0.6b-v3 (fp32, 600M) | 1.93% | 1.98% | 2.00% | 1.99% | 2.16% | 2.36% | 3.91% | **4.79%** | **0.007** |
| Qwen3-ASR-0.6B (bf16, 600M) | 2.13% | 2.21% | 2.37% | 2.18% | 2.52% | 2.56% | 3.53% | 5.25% | 0.015 |

**Gap vs clean, percentage points, paired 95% CI**

| model | g711u | pots | opus12 | opus8 | pink10 | babble10 | pots_babble10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| whisper-turbo | +0.03 [−0.05, +0.11] | +0.20 [+0.04, +0.42] | +0.05 [−0.05, +0.15] | +0.26 [+0.15, +0.37] | +0.46 [+0.33, +0.57] | +1.45 [+1.22, +1.71] | **+3.69 [+3.04, +4.92]** |
| parakeet | +0.05 [−0.03, +0.13] | +0.08 [+0.01, +0.15] | +0.06 [+0.01, +0.13] | +0.24 [+0.14, +0.34] | +0.43 [+0.33, +0.54] | **+1.99 [+1.75, +2.26]** | +2.87 [+2.64, +3.10] |
| Qwen3-ASR | +0.09 [+0.03, +0.15] | +0.25 [+0.18, +0.33] | +0.06 [−0.01, +0.11] | +0.39 [+0.31, +0.48] | +0.43 [+0.35, +0.52] | +1.41 [+1.26, +1.57] | +3.12 [+2.89, +3.35] |

Sanity: Parakeet's model card reports 1.93 on this set; Qwen's reports 2.11.
The harness reproduces both.

What the numbers say:

- **Codecs are not the problem.** G.711, Opus at 12 kbps, Opus at 8 kbps
  narrowband — every codec-only condition costs every model under 0.4 pp.
  Opus 12 kbps is indistinguishable from clean audio for all three. Opus 8
  kbps behaves like the analogue line (`pots`), and Qwen3-ASR is the model
  most sensitive to both narrowband conditions.
- **Stationary noise doesn't separate the models either.** Pink noise at
  10 dB costs +0.43 to +0.46 pp — the same for all three, intervals fully
  overlapping.
- **Background talkers are the first large effect, and the first ranking
  reversal.** Six competing speakers at 10 dB cost +1.4 to +2.0 pp — ten
  times the worst codec. Parakeet, untouchable on the line, is the *most*
  affected here (+1.99); Whisper (+1.45) and Qwen (+1.41) are tied. The
  error breakdown shows why: Parakeet's deletions quadruple (127 → 580) —
  a pure acoustic model *drops* words a competing voice covers — while the
  language-model-backed Qwen mostly substitutes: it guesses through the
  overlap, and guesses wrong less often than Parakeet says nothing.
- **Talkers plus the line is worse than the sum of its parts, for every
  model.** `pots_babble10` costs +2.9 to +3.7 pp; for each model that is
  1.3–2× the sum of `pots` and `babble10` alone. The band-limiting removes
  exactly the high-frequency cues a recogniser uses to separate voices.
- **And the ranking flips again.** Whisper — best under babble alone — is
  the worst once the line is added (+3.69 pp, 5.60% absolute), with the
  lopsided interval that means a heavy tail. This time it is not dropped
  segments but **hallucinated repetition**: on noisy narrowband audio a few
  short clips explode — one 8-word utterance came back as 240 words, and
  Whisper's ten worst utterances carry 12% of its errors against ~5% for
  the other two models. For a phone agent that is the nastiest failure
  mode here: not a missed word but a confident paragraph nobody said.
  Parakeet, worst under babble alone, is the *least* damaged in
  combination (+2.87, 4.79%) and its errors stay spread out.
- **So "which model for phone audio" has no single answer.** Quiet line:
  any of them, take the fastest. Noisy room on a good connection: Whisper
  or Qwen. Noisy room over a real narrowband line — the actual bad phone
  call — Parakeet, which is also 4× faster than Whisper while still in
  fp32.
- **Two caveats bigger than most of the gaps.** 419 of 2620 utterances
  (16%) are wrong for all three models identically — names, archaic words,
  normaliser mangling — a floor under every number here. And under
  `--normalizer basic`, Whisper's codec-condition gaps turn *negative* (it
  emits fewer digits and abbreviations on degraded audio), so the
  normaliser can flip the sign of a small effect. The babble and
  babble-plus-line effects survive either normaliser.

Reproduce: `uv run dialtone compare results/full/*/` and
`uv run dialtone inspect results/full/*/`; tables in `results/full/`.

## Run it

```sh
uv sync                                  # Python 3.12, CUDA 12.8 torch
uv run pytest                            # codec + chain tests, no GPU needed
uv run dialtone fetch                    # LibriSpeech test-clean, ~350 MB
uv run dialtone manifest -n 200 --seed 42
uv run dialtone listen manifests/librispeech-test-clean-200.txt   # hear it first
uv run dialtone listen manifests/librispeech-test-clean-200.txt \
    --conditions clean,babble10,pots_babble10,opus8              # ...and the harsh ones

M=manifests/librispeech-test-clean-200.txt
uv run dialtone run $M --model openai/whisper-large-v3-turbo   --out results/whisper-turbo
uv run dialtone run $M --model nvidia/parakeet-tdt-0.6b-v3     --out results/parakeet-tdt-0.6b-v3
uv run dialtone run $M --model Qwen/Qwen3-ASR-0.6B-hf          --out results/qwen3-asr-0.6b

uv run dialtone report  results/whisper-turbo                  # one model
uv run dialtone compare results/*/                             # all of them, one table
uv run dialtone inspect results/*/                             # which utterances moved, and why
```

`python -m dialtone ...` is equivalent to `dialtone ...` and works where the
venv's launcher stubs can't run (Windows Smart App Control blocks uv's
unsigned `.venv/Scripts/*.exe` on some machines; the interpreter itself is
fine — point `PYTHONPATH` at `src` and `.venv/Lib/site-packages`).

`--model` takes a Hugging Face hub id or a local path; the adapter is picked
from the checkpoint's `model_type`. `run` is resumable: results are appended
per utterance, and a restart skips what is already done. `--limit 3` gives a
smoke test.

Batches are formed by total audio seconds (`--max-batch-seconds`, default
160), longest utterances first, not by a fixed count — sixteen 30-second
clips and sixteen 3-second clips are very different amounts of GPU memory,
and a fixed count fell over on an 8 GB card partway through LibriSpeech. A
batch that still fails for lack of GPU capacity is retried one utterance at a
time.

The `opus*` conditions need `ffmpeg` with `libopus` on `PATH`
(`winget install Gyan.FFmpeg` on Windows); everything else is pure Python.

`scripts/run-full.ps1` runs the whole 2620-utterance set through every model
and every condition sequentially, detached, with a log — about an hour per
three conditions on an RTX 4060. Pass `-Conditions a,b,c` to run a subset.

## Models

| family | adapter | dtype (`--dtype auto`) | note |
|---|---|---|---|
| Whisper | `transformers` ASR pipeline | fp16 | `language=en`, `task=transcribe` forced |
| Parakeet TDT / CTC | `AutoModelForTDT` / `AutoModelForCTC` | fp32 | needs `librosa` (pulled in) |
| Qwen3-ASR | `Qwen3ASRForConditionalGeneration` | bf16 | **use the `-hf` checkpoints** (below) |

**Whisper memory trap.** Whisper pads every input to a 30 s window, so its
GPU cost is per *item*, not per audio second — a seconds budget alone lets a
batch of short clips balloon to 14+ windows. Combined with batch shapes that
change constantly (longest-first, then many short clips), the default CUDA
caching allocator fragments: per-batch time climbed 1.6 s → 20 s over a run
and then died with a raw CUDA OOM while most of the card was free. Three
things fix it, all in place: Whisper's adapter caps items per batch at 8,
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` is set before CUDA
initialises, and the cache is released between batches. Parakeet and
Qwen3-ASR don't pad to fixed windows and never showed the problem.

**Qwen3-ASR checkpoint trap.** `Qwen/Qwen3-ASR-0.6B` (no suffix) is laid out
for Qwen's own `qwen-asr` package. Loaded into the native transformers class,
every weight comes up missing and transformers *warns and initialises them at
random* — the model runs and emits confident nonsense. `Qwen/Qwen3-ASR-0.6B-hf`
is the converted layout. `dialtone` refuses to run any checkpoint with missing
weights (`models._load_checked`), so this fails loudly instead of quietly.

## Decisions that move the numbers

These are choices, not facts. Each is a named option so it can be changed and
the change seen.

- **Anti-alias before decimating.** `resample_poly` low-passes before dropping
  samples. Skipping this folds high frequencies into the band and quietly
  corrupts every result. It is the most common mistake in this kind of work.
- **Causal band-pass.** Real line equipment can't see the future, so `sosfilt`,
  not `sosfiltfilt`.
- **SNR is whole-clip RMS.** Noise is scaled against the mean power of the
  entire utterance, pauses included. LibriSpeech has little silence so this
  is close to a speech-active SNR; on real calls with long gaps the same
  number would mean noticeably louder noise during speech. An active-speech
  SNR (VAD-gated) is the alternative and would lower every noisy WER a
  little.
- **Babble is six talkers.** Fewer sounds like an intelligible competing
  voice (much harder for a recogniser, and a different experiment); more
  converges to speech-shaped stationary noise. Six is the conventional
  middle.
- **Text normalisation.** Default is OpenAI's English normaliser applied to
  *every* model's output — the Open ASR Leaderboard convention, so numbers are
  comparable to published ones. The spelling map is vendored in
  `src/dialtone/assets/` so scoring needs no model on disk. `--normalizer
  basic` shows how much the choice is worth (on Whisper-turbo it moves clean
  WER from 1.7% to 3.0% — ten times the phone-line effect). It also mangles
  archaic text: LibriSpeech's "million'd" becomes "1000000 would".
- **Uncertainty.** 95% bootstrap interval over utterances. A ranking without
  one is a guess.
- **Precision.** Follows each model card by default and is recorded in
  `run.json`. Cross-model speed (RTF) is therefore *not* apples to apples yet.

## Data

LibriSpeech test-clean (CC BY 4.0). The 200-utterance subset is pinned in
`manifests/` with its seed. Do not regenerate it once results exist.
