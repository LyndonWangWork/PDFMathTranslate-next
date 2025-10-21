## CLI Profiling (JSONL + cProfile)

### Enable JSONL tracer

```bash
pdf2zh_next --profile --profile-file ./.perf/run.jsonl -i input.pdf -o out/
```

It writes one JSON line per section/stage. Example line:

```json
{"timestamp":"2025-10-21T10:00:01Z","section":"initialize_config","duration_ms":35.7}
```

### Enable cProfile in translation subprocess

```bash
pdf2zh_next --cprofile --cprofile-dir ./.perf --cprofile-topn 30 -i input.pdf -o out/
```

This dumps `.prof` files per input file, and optionally prints Top-N cumulative results to console.


