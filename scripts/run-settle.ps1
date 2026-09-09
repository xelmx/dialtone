# Streaming settle run: forced-align all references once, then transcribe growing
# prefixes of every utterance for each model and condition, then the settle tables.
# Resumable per (utterance, prefix). ~8 h on an RTX 4060 for 2 conditions x 3 models.
#
# Runs the interpreter directly (`python -m dialtone`) rather than `uv run`: Windows
# Smart App Control blocks uv's unsigned .venv\Scripts\*.exe launchers on some machines.
param(
  [string]$Conditions = "clean,pots_babble10",
  [string]$Manifest = "manifests/librispeech-test-clean-2620.txt"
)
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root
$py = "$env:APPDATA\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
$env:PYTHONPATH = "$root\src;$root\.venv\Lib\site-packages"
$models = @(
  @{ id = "C:/Users/lyle/Projects/models/stt/parakeet-tdt-0.6b-v3"; out = "results/stream/parakeet-tdt-0.6b-v3" },
  @{ id = "Qwen/Qwen3-ASR-0.6B-hf";                                   out = "results/stream/qwen3-asr-0.6b" },
  @{ id = "C:/Users/lyle/Projects/models/stt/whisper-large-v3-turbo";  out = "results/stream/whisper-turbo" }
)
"START $(Get-Date -Format s)  conditions=$Conditions manifest=$Manifest"
"ALIGN $(Get-Date -Format s)"
& $py -m dialtone align $Manifest
if ($LASTEXITCODE -ne 0) { "FAILED align exit $LASTEXITCODE"; exit 1 }
foreach ($entry in $models) {
  $id = $entry.id
  $out = $entry.out
  "MODEL $id -> $out  $(Get-Date -Format s)"
  & $py -m dialtone stream $Manifest --model $id --conditions $Conditions --out $out
  if ($LASTEXITCODE -ne 0) { "FAILED $id exit $LASTEXITCODE"; exit 1 }
}
$dirs = @("results/stream/parakeet-tdt-0.6b-v3", "results/stream/qwen3-asr-0.6b", "results/stream/whisper-turbo")
& $py -m dialtone settle @dirs --out results/stream/settle.whisper_en.md
& $py -m dialtone settle @dirs --normalizer basic --out results/stream/settle.basic.md
"DONE $(Get-Date -Format s)"
