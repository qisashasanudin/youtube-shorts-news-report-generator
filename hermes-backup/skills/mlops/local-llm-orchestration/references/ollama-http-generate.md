## Ollama local HTTP API

- Endpoint: POST http://localhost:11434/api/generate
- Request body: {"model":"<model>","prompt":"<text>","stream":false}
- Response: {"response":"<text>","done":true}

## Windows quick-start

1. winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
2. ollama pull gemma4:4b
3. ollama serve

## Known install issue

Large installer downloads (OllamaSetup.exe ~1.29 GB) can time out via winget when the network is unstable. If that happens, retry or consider an alternative installer source.