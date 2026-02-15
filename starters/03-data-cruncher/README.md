# 03 - Data Cruncher

**Difficulty:** Intermediate | **Time:** 20 minutes | **Prerequisites:** Complete [02-ai-content-toolkit](../02-ai-content-toolkit/) first

Build a data analysis pipeline that reads CSV files, computes statistics, generates AI insights, and exports reports. This template teaches you how to combine storage, LLM, and file operations in a multi-command workflow.

---

## What You Will Learn

1. **`ctx.files.read_csv()`** - Reading CSV files into your commands
2. **Multi-command workflows** - Chain analyze -> insights -> export
3. **Combining services** - Storage + LLM + Files working together
4. **Data transformation** - Computing statistics and generating reports
5. **`ctx.files.write()`** - Writing output files

## Commands

| Command | Description | Arguments |
|---------|-------------|-----------|
| `analyze-file` | Read CSV, compute column statistics, store results | `file_path` (str), `column_name` (str) |
| `ai-insights` | Feed stored stats to LLM for insights | `analysis_id` (str) |
| `export-report` | Write analysis to downloadable CSV | `analysis_id` (str), `output_path` (str) |

## Workflow

```
CSV File --> [analyze-file] --> Storage
                                  |
                           [ai-insights] --> AI Summary + Recommendations
                                  |
                           [export-report] --> CSV Report
```

## Quick Start

```bash
# 1. Navigate to this template
cd starters/03-data-cruncher

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Start the dev server
huitzo pack dev

# 4. Analyze the sample data
curl -X POST http://localhost:8080/api/v1/commands/data/analyze-file \
  -H "Content-Type: application/json" \
  -d '{"file_path":"examples/sample-data/sales.csv","column_name":"revenue"}'

# 5. Use the returned analysis_id for insights and export
```

## Run Tests

```bash
cd starters/03-data-cruncher
pytest -v
```

## Project Structure

```
03-data-cruncher/
├── README.md
├── tutorial.md
├── pyproject.toml
├── huitzo.yaml
├── .env.example
├── src/
│   └── data_cruncher/
│       ├── __init__.py
│       └── commands.py
├── tests/
│   └── test_commands.py
└── examples/
    ├── test-commands.sh
    └── sample-data/
        └── sales.csv
```

## Services Used

- **Files** - `ctx.files.read_csv()`, `ctx.files.write()`
- **Storage** - `ctx.storage.set()`, `ctx.storage.get()`
- **LLM** - `ctx.llm.complete()` for AI-powered insights

## Sample Data

The included `examples/sample-data/sales.csv` contains 16 rows of sales data with columns: date, product, region, units_sold, unit_price, revenue.

## Next Step

Once you are comfortable with multi-command workflows, move on to:
**[04-lead-engine](../04-lead-engine/)** - HTTP APIs, email, and multi-command business workflows
