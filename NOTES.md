# dialtone — my notes

Personal, plain-language notes. The README is the public version; this is the
one I'd read before an interview or before picking the project up again.

## What it is, in one line

A test bench that answers: *do speech-to-text models get worse on phone calls
than on clean recordings, by how much, and how fast do they make up their mind?*

## Why I built it

Everyone ranks speech-to-text models on clean studio recordings. My day job
runs those models on phone calls, which are far lower quality, and I had to
pick a model twice in two months by re-doing the evaluation from scratch each
time. Nobody had published the phone-quality gap. So: build the bench once,
publicly, with public data, and get the answer with real numbers.

It also fills a gap on my résumé — public proof that I can *measure* whether a
model is good, not just wire one up.

## The question, and how the bench answers it

1. Take free recordings that come with the correct transcript (LibriSpeech
   test-clean: 2,620 sentences, 40 speakers, 5.4 hours). That's the answer key.
2. Damage each recording the way a phone line does. Written from the spec, with
   tests: proper anti-alias filter, down to 8 kHz, the G.711 codec, the
   300–3400 Hz line band-pass, and later Opus, pink noise, and "babble" (six
   other people talking, never the same speaker, at a fixed loudness ratio).
3. Run each model on the clean and the damaged versions. Count the mistakes.
4. Report the *gap* between them, with a confidence interval computed on the
   same sentences (paired). If the interval doesn't cross zero, the damage was
   real. Otherwise it's noise, and I say so.

Three models: Whisper-large-v3-turbo (809M), Parakeet-TDT-0.6B, Qwen3-ASR-0.6B.
All run on my own RTX 4060. Two of them reproduce their published LibriSpeech
score to the digit — that's the proof the bench is right.

## Progress, in order (5–10 Sept 2026)

- **Step 1 — one model, 200 sentences.** Codec alone barely mattered. Good to
  know in week one, not month two.
- **Step 2 — three models, all 2,620.** Same conclusion, tight intervals.
  Caught a silent failure: one checkpoint loaded as random weights with only a
  warning. Built a guard so that can never pass quietly again.
- **Step 3 — noise and Opus.** This is where the models finally separated.
- **Step 4 — streaming.** Feed each recording a half-second at a time and
  watch the transcript change: when is each word committed, how often are words
  taken back, how many words behind the cursor can't be trusted. Word timing
  from a forced aligner, independent of the models. Seven hours of GPU.

## What we found

- **Codecs don't matter.** G.711, Opus 12 kbps, Opus 8 kbps — all under 0.4
  points for every model. Opus 12 kbps is indistinguishable from clean audio.
- **Background talkers do.** 4–10× the worst codec. And they flip the ranking:
  Parakeet, untouched by the line, is hurt most (it *drops* words a competing
  voice covers); the language-model-backed models guess through it.
- **Talkers plus the line is worse than the sum.** And it flips the ranking
  back — Whisper becomes worst, by hallucinating repetition (an 8-word
  sentence came back as 240 words).
- **Streaming stability ranks the models backwards.** Qwen — least accurate —
  has the calmest transcript (6 revisions per 100 words). Parakeet — most
  accurate, 4× faster — takes words back 33 per 100 and occasionally loops
  ("a little bit of a little bit of…"). Commit latency is the same for all
  three; the difference is how often they un-commit.
- **So there is no single winner.** Quiet line: fastest model. Noisy room, good
  connection: Whisper or Qwen. Noisy room on a real narrowband line: Parakeet.
  Showing partial transcripts to a caller: Qwen.
- **Two things bigger than most gaps:** 16% of sentences are wrong for all
  three models identically (names, archaic words, the text normaliser), and the
  choice of text normaliser can flip the sign of a small effect.

## Things that broke, and what they taught me

- Whisper thrashed GPU memory and died twice: it pads everything to 30 s, so
  cost is per item, not per second. Cap items per batch, use expandable
  allocator segments, free the cache between batches.
- Three GPU jobs at once got killed for *host* RAM (my work rig shares the
  machine). One GPU process at a time, always resumable to the row.
- A revision count depended on how the aligner broke ties. Replaced it with a
  definition that can't ("fewest edits with free appends"), pinned by a test.
- A few decoding loops dominated the pooled revision rate. Report the median
  utterance alongside, and count the loops explicitly. Surface, don't filter.
- Windows Smart App Control started blocking the venv launcher mid-project.
  `python -m dialtone` with the base interpreter works; documented.

## My role vs. the tool's role (honest version)

Claude Code wrote nearly all the code. I decided what question to ask, which
models and conditions matter, what counts as a fair comparison, and I read the
transcripts and listened to the samples to check the method. Every number in
the README is one I can explain and defend. That's the part that's mine.

## Numbers to remember

- 2,620 sentences · 3 models · 8 conditions · 37,053 prefixes per streaming run
- Clean WER: 1.91 / 1.93 / 2.13% (Whisper / Parakeet / Qwen)
- Worst codec: < 0.4 pp. Talkers: +1.4 to +2.0 pp. Talkers + line: +2.9 to +3.7 pp.
- Revisions per 100 words: Qwen 6, Whisper 15, Parakeet 33.
- Parakeet is 4× faster than Whisper in fp32 and reproduces its model card (1.93).

Repo: github.com/xelmx/dialtone · 48 tests · public, MIT.
