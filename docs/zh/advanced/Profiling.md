## CLI 性能分析（JSONL + cProfile）

### 启用 JSONL 埋点

```bash
pdf2zh_next --profile --profile-file ./.perf/run.jsonl -i input.pdf -o out/
```

每个阶段/区段输出一行 JSONL，示例：

```json
{"timestamp":"2025-10-21T10:00:01Z","section":"initialize_config","duration_ms":35.7}
```

### 启用 cProfile（翻译子进程）

```bash
pdf2zh_next --cprofile --cprofile-dir ./.perf --cprofile-topn 30 -i input.pdf -o out/
```

会为每个输入文件生成 `.prof`，并可在控制台打印累计耗时 Top-N。


