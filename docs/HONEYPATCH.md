# Honeypatch

Honeypatch is stand-alone tool to inject traps into arbitrary, text-based payload.

> [!IMPORTANT]
> Honeypatch is still in development and only in a proof-of-concept stage.
> It is not integrated with the rest of Honeyquest yet.

## 🚀 Usage

List all available honeywire templates.

```sh
honeypatch list -p ./querydb/honeyaml
```

Inject additional headers into HTTP responses.

```sh
honeypatch inject -p ./querydb/honeyaml -w httpheader-apiserver ./docs/examples/http-response.txt
honeypatch inject -p ./querydb/honeyaml -w httpheader-devtoken ./docs/examples/http-response.txt
```

### List of available arguments

Please refer to the `--help` command for more information.
