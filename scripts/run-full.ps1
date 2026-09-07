# Full LibriSpeech test-clean (2620 utterances) x 3 conditions x 3 models, sequentially.
# Resumable: re-running skips anything already done.
# NB: PowerShell variables are case-insensitive - do not name the manifest $M next to a loop $m.
Set-Location (Join-Path $PSScriptRoot "..")
$manifest = "manifests/librispeech-test-clean-2620.txt"
$models = @(
  @{ id = "C:/Users/lyle/Projects/models/stt/parakeet-tdt-0.6b-v3"; out = "results/full/parakeet-tdt-0.6b-v3" },
  @{ id = "Qwen/Qwen3-ASR-0.6B-hf";                                   out = "results/full/qwen3-asr-0.6b" },
  @{ id = "C:/Users/lyle/Projects/models/stt/whisper-large-v3-turbo";  out = "results/full/whisper-turbo" }
)
"START $(Get-Date -Format s)"
if (-not (Test-Path $manifest)) { uv run dialtone manifest -n 2620 --seed 42 }
foreach ($entry in $models) {
  $id = $entry.id
  $out = $entry.out
  "MODEL $id -> $out  $(Get-Date -Format s)"
  uv run dialtone run $manifest --model $id --out $out
  if ($LASTEXITCODE -ne 0) { "FAILED $id exit $LASTEXITCODE"; exit 1 }
}
$dirs = @("results/full/parakeet-tdt-0.6b-v3", "results/full/qwen3-asr-0.6b", "results/full/whisper-turbo")
uv run dialtone compare @dirs --out results/full/compare.whisper_en.md
uv run dialtone compare @dirs --normalizer basic --out results/full/compare.basic.md
"DONE $(Get-Date -Format s)"
