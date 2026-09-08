# Full LibriSpeech test-clean (2620 utterances) x every condition x 3 models, sequentially.
# Resumable: re-running skips anything already done, per model and per condition.
#
# Runs the interpreter directly (`python -m dialtone`) rather than `uv run`: Windows
# Smart App Control blocks uv's unsigned .venv\Scripts\*.exe launchers on some machines.
# NB: PowerShell variables are case-insensitive - do not name the manifest $M next to a loop $m.
param(
  [string]$Conditions = "clean,g711u,pots,pink10,babble10,pots_babble10,opus12,opus8"
)
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root
$py = "$env:APPDATA\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
$env:PYTHONPATH = "$root\src;$root\.venv\Lib\site-packages"
$manifest = "manifests/librispeech-test-clean-2620.txt"
$models = @(
  @{ id = "C:/Users/lyle/Projects/models/stt/parakeet-tdt-0.6b-v3"; out = "results/full/parakeet-tdt-0.6b-v3" },
  @{ id = "Qwen/Qwen3-ASR-0.6B-hf";                                   out = "results/full/qwen3-asr-0.6b" },
  @{ id = "C:/Users/lyle/Projects/models/stt/whisper-large-v3-turbo";  out = "results/full/whisper-turbo" }
)
"START $(Get-Date -Format s)  conditions=$Conditions"
if (-not (Test-Path $manifest)) { & $py -m dialtone manifest -n 2620 --seed 42 }
foreach ($entry in $models) {
  $id = $entry.id
  $out = $entry.out
  "MODEL $id -> $out  $(Get-Date -Format s)"
  & $py -m dialtone run $manifest --model $id --conditions $Conditions --out $out
  if ($LASTEXITCODE -ne 0) { "FAILED $id exit $LASTEXITCODE"; exit 1 }
}
$dirs = @("results/full/parakeet-tdt-0.6b-v3", "results/full/qwen3-asr-0.6b", "results/full/whisper-turbo")
& $py -m dialtone compare @dirs --out results/full/compare.whisper_en.md
& $py -m dialtone compare @dirs --normalizer basic --out results/full/compare.basic.md
& $py -m dialtone inspect @dirs --out results/full/inspect.whisper_en.md
"DONE $(Get-Date -Format s)"
