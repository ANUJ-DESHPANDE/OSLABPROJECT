# Start the optional local explanation model. The web app works for search and
# calculated scheduling without it, but generated explanations need this server.
# All paths point inside this project; no hosted API key is used.
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtime = Join-Path $projectRoot 'data/private/llama-vulkan/llama-server.exe'

if (-not (Test-Path -LiteralPath $runtime)) {
    Write-Error 'Local llama.cpp runtime is missing. Install Ollama or download the official llama.cpp Windows runtime.'
    exit 1
}

$candidates = @(
    # Exact size catches an incomplete download before the model is launched.
    @{ Name = 'qwen3-4b-ollama.gguf'; Size = 2497280480 }
)
$selected = $null
foreach ($candidate in $candidates) {
    $path = Join-Path $projectRoot ('data/private/' + $candidate.Name)
    if ((Test-Path -LiteralPath $path) -and (Get-Item -LiteralPath $path).Length -eq $candidate.Size) {
        $selected = $path
        break
    }
}

if (-not $selected) {
    Write-Error 'No complete GGUF model was found in data/private/. Download a model before starting the local explanation server.'
    exit 1
}

Write-Host "Starting local model: $(Split-Path -Leaf $selected)"
Write-Host 'Leave this window open while using OS Lab Companion.'
& $runtime --model $selected --host 127.0.0.1 --port 8080 --ctx-size 4096 --parallel 1 --n-gpu-layers 99
