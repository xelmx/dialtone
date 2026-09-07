# dialtone

**How much worse do speech-to-text models get on phone-quality audio?**

Every public speech-to-text leaderboard scores models on clean, 16 kHz studio
recordings. Phone calls are 8 kHz, G.711 mu-law, and band-limited — roughly a
tenth of the audio detail. The model that wins on studio audio is not
necessarily the model that wins on a call, and nobody publishes the gap.

This repo measures it.

## Status: step 2

Three models, one dataset, three conditions, batch accuracy only. The goal so
far is a defensible number per model and a degradation chain that has been
listened to and argued about — not a leaderboard.

| condition | what it is |
|---|---|
| `clean` | the recording as shipped, 16 kHz |
| `g711u` | anti-aliased down to 8 kHz → G.711 mu-law encode/decode → back to 16 kHz |
| `pots` | as above, plus a 300–3400 Hz band-pass before the codec (classic analogue line) |

## Results so far

LibriSpeech test-clean, **all 2620 utterances** (40 speakers), RTX 4060,
Whisper English normaliser. "gap" is WER(condition) − WER(clean) on the same
utterances, with a paired bootstrap 95% interval — the number that says
whether the phone line actually hurt.

| model | params | clean WER | g711u WER | pots WER | gap g711u | gap pots | RTF |
|---|---:|---:|---:|---:|---:|---:|---:|
| whisper-large-v3-turbo (fp16) | 809M | 1.91% | 1.94% | 2.11% | +0.03 pp [−0.05, +0.11] | +0.20 pp [+0.04, +0.42] | 0.027 |
| parakeet-tdt-0.6b-v3 (fp32) | 600M | 1.93% | 1.98% | 2.00% | +0.05 pp [−0.03, +0.13] | +0.08 pp [+0.01, +0.15] | **0.007** |
| Qwen3-ASR-0.6B (bf16) | 600M | 2.13% | 2.21% | 2.37% | +0.09 pp [+0.03, +0.15] | **+0.25 pp [+0.18, +0.33]** | 0.015 |

Sanity: Parakeet's model card reports 1.93 on this set; Qwen's reports 2.11.
The harness reproduces both.

What the numbers say:

- **The G.711 codec by itself (`g711u`) does not measurably hurt Whisper or
  Parakeet.** Both intervals straddle zero. Qwen3-ASR shows a small but real
  effect (+0.09 pp).
- **Add the 300–3400 Hz line band-pass (`pots`) and the models separate.**
  Qwen3-ASR degrades clearly (+0.25 pp, +12% relative; 99 utterances go from
  right to wrong, 36 the other way). Parakeet barely moves (+0.08 pp,
  practically nothing). Whisper's +0.20 pp is real but *heavy-tailed*: the
  wide interval comes from a handful of long utterances where the chunked
  pipeline drops a whole segment (one 34 s clip lost 47 of 96 words). Whisper's
  phone-line risk is catastrophic-per-utterance, not gradual — a different
  failure mode from Qwen's diffuse confusions (*edison → anderson*, *this →
  his*, *worth while → worthwhile*).
- **Parakeet is the practical answer for phone audio in this test:** tied
  with Whisper-turbo on clean accuracy, the least affected by the line, and
  4× faster than Whisper while still in fp32.
- **419 of 2620 utterances (16%) are wrong for all three models in the same
  way** — names (*stephanos dedalos*, *brother mac ardle brother keogh*),
  archaic words (*woodbegirt*, *greeing*), and normaliser mangling
  (*million'd → 1000000 would*). That floor is bigger than every gap above.
  A large share of "2% WER" on this set is not the model's fault.
- **The normaliser can flip the sign.** Under `--normalizer basic`
  Whisper-turbo's clean WER is 3.48% and it gets *better* on phone audio
  (−0.44 pp on `g711u`, interval excludes zero) — because on degraded audio
  it emits fewer digits and abbreviations, which basic normalisation counts
  as errors. Parakeet and Qwen keep their ordering under either. The
  normaliser is a bigger decision than the codec.

Reproduce: `uv run dialtone compare results/full/*/` and
`uv run dialtone inspect results/full/*/`; tables in `results/full/`.

## Run it

```sh
uv sync                                  # Python 3.12, CUDA 12.8 torch
uv run pytest                            # codec + chain tests, no GPU needed
uv run dialtone fetch                    # LibriSpeech test-clean, ~350 MB
uv run dialtone manifest -n 200 --seed 42
uv run dialtone listen manifests/librispeech-test-clean-200.txt   # hear it first

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

`scripts/run-full.ps1` runs the whole 2620-utterance set through every model
sequentially, detached, with a log — about an hour on an RTX 4060.

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
