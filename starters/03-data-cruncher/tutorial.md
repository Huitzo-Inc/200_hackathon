# Tutorial: Data Cruncher

**Goal:** Build a 3-command data analysis pipeline in 20 minutes.

**Prerequisites:** Complete [01-smart-notes](../01-smart-notes/) and [02-ai-content-toolkit](../02-ai-content-toolkit/) first.

---

## Step 1: The Multi-Command Workflow Pattern

In previous templates, each command worked independently. Data Cruncher introduces a **workflow** where commands build on each other:

```
1. analyze-file  -->  Reads CSV, computes stats, stores results
2. ai-insights   -->  Reads stored stats, asks LLM for insights
3. export-report -->  Reads stored stats, writes CSV report
```

Commands share data through `ctx.storage`. The `analysis_id` returned by `analyze-file` is the key that links the workflow together.

## Step 2: Reading CSV Files with `ctx.files`

Open `src/data_cruncher/commands.py` and look at the `analyze-file` command:

```python
@command("analyze-file", namespace="data", timeout=60, queue="medium")
async def analyze_file(args: AnalyzeFileArgs, ctx: Context) -> dict[str, Any]:
    # Read the CSV file
    rows = await ctx.files.read_csv(args.file_path)

    # Verify column exists
    available_columns = list(rows[0].keys())
    if args.column_name not in available_columns:
        return {"error": "column_not_found", ...}

    # Extract numeric values and compute stats
    values = _parse_numeric_column(rows, args.column_name)
    stats = _compute_statistics(values)

    # Store results with a unique ID
    analysis_id = f"analysis-{uuid.uuid4().hex[:8]}"
    await ctx.storage.set(f"analysis:{analysis_id}", analysis_data)

    return analysis_data
```

Key points:
- `ctx.files.read_csv()` returns a list of dictionaries (one per row)
- Each dictionary maps column names to string values
- You need to parse numeric values yourself (see `_parse_numeric_column`)
- Results are stored with a unique ID for later retrieval

## Step 3: Computing Statistics

The helper function `_compute_statistics` uses Python's built-in `statistics` module:

```python
import statistics

def _compute_statistics(values: list[float]) -> dict[str, Any]:
    return {
        "count": len(values),
        "sum": round(sum(values), 2),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }
```

No external dependencies needed for basic statistics.

## Step 4: Chaining Commands with Storage

The `ai-insights` command retrieves the stored analysis:

```python
@command("ai-insights", namespace="data", timeout=60)
async def ai_insights(args: AIInsightsArgs, ctx: Context) -> dict[str, Any]:
    # Retrieve stored analysis
    analysis = await ctx.storage.get(f"analysis:{args.analysis_id}")

    if analysis is None:
        return {"error": "not_found", ...}

    # Feed statistics to LLM
    stats = analysis["statistics"]
    response = await ctx.llm.complete(
        prompt=f"Analyze these stats: mean={stats['mean']}, ...",
        response_format="json",
    )

    return {
        "ai_summary": response.get("summary", ""),
        "ai_insights": response.get("insights", []),
        "ai_recommendations": response.get("recommendations", []),
    }
```

This pattern is powerful: one command does the heavy lifting (parsing, computing), and another command adds intelligence (AI analysis). Users can run `ai-insights` multiple times on the same data.

## Step 5: Writing Files with `ctx.files.write()`

The `export-report` command demonstrates file output:

```python
import csv
import io

output = io.StringIO()
writer = csv.writer(output)

writer.writerow(["Metric", "Value"])
for metric, value in stats.items():
    writer.writerow([metric, value])

csv_content = output.getvalue()
written_path = await ctx.files.write(args.output_path, csv_content)
```

Key points:
- Build CSV content in memory using `io.StringIO` + `csv.writer`
- `ctx.files.write()` handles the actual file writing
- It returns the path where the file was saved

## Step 6: Error Handling

Data Cruncher demonstrates several error handling patterns:

```python
# Empty file
if not rows:
    return {"error": "empty_file", "message": "..."}

# Missing column
if args.column_name not in available_columns:
    return {"error": "column_not_found", "message": "...", "available": available_columns}

# No numeric data
if not values:
    return {"error": "no_numeric_data", "message": "..."}

# Analysis not found
if analysis is None:
    return {"error": "not_found", "message": "..."}
```

Return structured error responses rather than raising exceptions. This gives callers clear, actionable feedback.

## Step 7: Run the Tests

```bash
pytest -v
```

The tests mock all three services (files, storage, LLM):

```python
ctx = MagicMock()
ctx.files.read_csv = AsyncMock(return_value=SAMPLE_ROWS)
ctx.storage.set = AsyncMock()
ctx.storage.get = AsyncMock(return_value=stored_analysis)
ctx.llm.complete = AsyncMock(return_value=llm_response)
```

## Step 8: Try the Full Workflow

```bash
huitzo pack dev
```

```bash
# 1. Analyze the sample CSV
curl -X POST http://localhost:8080/api/v1/commands/data/analyze-file \
  -H "Content-Type: application/json" \
  -d '{"file_path":"examples/sample-data/sales.csv","column_name":"revenue"}'
# Note the analysis_id from the response

# 2. Get AI insights (replace with your analysis_id)
curl -X POST http://localhost:8080/api/v1/commands/data/ai-insights \
  -H "Content-Type: application/json" \
  -d '{"analysis_id":"analysis-abc12345"}'

# 3. Export report
curl -X POST http://localhost:8080/api/v1/commands/data/export-report \
  -H "Content-Type: application/json" \
  -d '{"analysis_id":"analysis-abc12345","output_path":"output/report.csv"}'
```

## Step 9: Experiment

1. **Add a `compare` command** that takes two analysis IDs and compares their statistics
2. **Support multiple columns** in `analyze-file` (analyze all numeric columns at once)
3. **Add chart descriptions** to the AI insights (ask the LLM to suggest visualizations)
4. **Add a `top-rows` command** that returns the rows with the highest values in a column

## What You Learned

- `ctx.files.read_csv()` reads CSV files into list-of-dict format
- `ctx.files.write()` writes output files
- Multi-command workflows share data through `ctx.storage`
- The `analysis_id` pattern connects related operations
- Combining storage + LLM + files enables powerful data pipelines

## Next Step

Move on to **[04-lead-engine](../04-lead-engine/)** to learn HTTP APIs, email integration, and multi-command business workflows.
