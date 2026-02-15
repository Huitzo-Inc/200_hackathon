"""
Data Cruncher Pack Commands.

Implements:
    - docs/sdk/commands.md#the-command-decorator
    - docs/sdk/context.md#files-api
    - docs/sdk/context.md#storage-api
    - docs/sdk/integrations.md#llm-integration

This module provides three commands for a data analysis workflow:
    - analyze-file: Read a CSV, compute column statistics, store results
    - ai-insights: Feed stored statistics to LLM for natural language insights
    - export-report: Write analysis results to a downloadable CSV

See Also:
    - docs/sdk/context.md (for Context API)
"""

from __future__ import annotations

import csv
import io
import statistics
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# SDK placeholder types (replaced at runtime by huitzo-sdk)
# ---------------------------------------------------------------------------

if TYPE_CHECKING:

    class StorageService(Protocol):
        async def set(self, key: str, data: dict[str, Any]) -> None: ...
        async def get(self, key: str) -> dict[str, Any] | None: ...

    class LLMService(Protocol):
        async def complete(
            self,
            prompt: str,
            system: str | None = None,
            model: str = "gpt-4o-mini",
            response_format: str | None = None,
            temperature: float = 0.7,
        ) -> Any: ...

    class FilesService(Protocol):
        async def read_csv(self, file_path: str) -> list[dict[str, str]]: ...
        async def write(self, file_path: str, content: str) -> str: ...

    class LogService(Protocol):
        def info(self, message: str) -> None: ...
        def warning(self, message: str) -> None: ...
        def error(self, message: str) -> None: ...

    class Context(Protocol):
        storage: StorageService
        llm: LLMService
        files: FilesService
        log: LogService


def command(
    name: str,
    *,
    namespace: str,
    timeout: int = 60,
    retries: int = 3,
    queue: str = "default",
) -> Any:
    """Decorator placeholder for the @command pattern."""

    def decorator(func: Any) -> Any:
        func._command_name = name
        func._command_namespace = namespace
        func._command_timeout = timeout
        func._command_retries = retries
        func._command_queue = queue
        return func

    return decorator


# ---------------------------------------------------------------------------
# Argument Models
# ---------------------------------------------------------------------------

STORAGE_PREFIX = "analysis:"


class AnalyzeFileArgs(BaseModel):
    """Arguments for the analyze-file command."""

    file_path: str = Field(
        min_length=1,
        max_length=500,
        description="Path to the CSV file to analyze",
    )
    column_name: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the numeric column to compute statistics for",
    )


class AIInsightsArgs(BaseModel):
    """Arguments for the ai-insights command."""

    analysis_id: str = Field(
        min_length=1,
        max_length=100,
        description="ID of a previous analyze-file result",
    )


class ExportReportArgs(BaseModel):
    """Arguments for the export-report command."""

    analysis_id: str = Field(
        min_length=1,
        max_length=100,
        description="ID of a previous analyze-file result",
    )
    output_path: str = Field(
        min_length=1,
        max_length=500,
        description="Path for the exported CSV report",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_statistics(values: list[float]) -> dict[str, Any]:
    """Compute descriptive statistics for a list of numbers."""
    sorted_values = sorted(values)
    return {
        "count": len(values),
        "sum": round(sum(values), 2),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
    }


def _parse_numeric_column(rows: list[dict[str, str]], column_name: str) -> list[float]:
    """Extract numeric values from a named column, skipping unparseable rows."""
    values: list[float] = []
    for row in rows:
        raw = row.get(column_name, "").strip()
        if raw:
            try:
                values.append(float(raw))
            except ValueError:
                continue
    return values


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@command("analyze-file", namespace="data", timeout=60, queue="medium")
async def analyze_file(args: AnalyzeFileArgs, ctx: Context) -> dict[str, Any]:
    """Read a CSV file, compute statistics on a column, and store the results.

    Args:
        args: File path and column name to analyze.
        ctx: Huitzo context providing files, storage, and logging.

    Returns:
        Analysis ID, column statistics, and row count.
    """
    # Read the CSV file
    rows = await ctx.files.read_csv(args.file_path)

    if not rows:
        return {"error": "empty_file", "message": f"No data found in {args.file_path}"}

    # Verify column exists
    available_columns = list(rows[0].keys())
    if args.column_name not in available_columns:
        return {
            "error": "column_not_found",
            "message": f"Column '{args.column_name}' not found. Available: {available_columns}",
        }

    # Extract numeric values and compute stats
    values = _parse_numeric_column(rows, args.column_name)

    if not values:
        return {
            "error": "no_numeric_data",
            "message": f"No numeric values found in column '{args.column_name}'",
        }

    stats = _compute_statistics(values)

    # Generate a unique analysis ID and store results
    analysis_id = f"analysis-{uuid.uuid4().hex[:8]}"
    analysis_data = {
        "analysis_id": analysis_id,
        "file_path": args.file_path,
        "column_name": args.column_name,
        "row_count": len(rows),
        "numeric_values_count": len(values),
        "statistics": stats,
        "columns": available_columns,
        "created_at": datetime.now(UTC).isoformat(),
    }

    await ctx.storage.set(f"{STORAGE_PREFIX}{analysis_id}", analysis_data)

    ctx.log.info(
        f"Analyzed {args.file_path}: {len(values)} values in '{args.column_name}', "
        f"mean={stats['mean']}, median={stats['median']}"
    )

    return analysis_data


@command("ai-insights", namespace="data", timeout=60, queue="medium")
async def ai_insights(args: AIInsightsArgs, ctx: Context) -> dict[str, Any]:
    """Feed stored analysis statistics to LLM for natural language insights.

    Args:
        args: Analysis ID from a previous analyze-file run.
        ctx: Huitzo context providing storage, LLM, and logging.

    Returns:
        AI-generated insights about the data, including trends and recommendations.
    """
    # Retrieve stored analysis
    analysis = await ctx.storage.get(f"{STORAGE_PREFIX}{args.analysis_id}")

    if analysis is None:
        return {
            "error": "not_found",
            "message": f"Analysis '{args.analysis_id}' not found. Run analyze-file first.",
        }

    stats = analysis["statistics"]

    prompt = f"""Analyze the following data statistics and provide actionable insights.

Data source: {analysis['file_path']}
Column analyzed: {analysis['column_name']}
Row count: {analysis['row_count']}

Statistics:
- Count: {stats['count']}
- Sum: {stats['sum']}
- Mean: {stats['mean']}
- Median: {stats['median']}
- Min: {stats['min']}
- Max: {stats['max']}
- Std Dev: {stats['stdev']}

Available columns in dataset: {analysis['columns']}

Respond as JSON:
{{
    "summary": "One-sentence summary of the data",
    "insights": ["insight 1", "insight 2", ...],
    "recommendations": ["recommendation 1", "recommendation 2", ...],
    "data_quality": "good" | "fair" | "poor"
}}"""

    system = (
        "You are a data analyst. Provide clear, actionable insights based on "
        "descriptive statistics. Focus on patterns, anomalies, and practical "
        "recommendations. Always respond with valid JSON."
    )

    response = await ctx.llm.complete(
        prompt=prompt,
        system=system,
        model="gpt-4o-mini",
        response_format="json",
        temperature=0.4,
    )

    result = {
        "analysis_id": args.analysis_id,
        "column_name": analysis["column_name"],
        "statistics": stats,
        "ai_summary": response.get("summary", ""),
        "ai_insights": response.get("insights", []),
        "ai_recommendations": response.get("recommendations", []),
        "data_quality": response.get("data_quality", "fair"),
    }

    ctx.log.info(f"Generated AI insights for {args.analysis_id}")

    return result


@command("export-report", namespace="data", timeout=60, queue="medium")
async def export_report(args: ExportReportArgs, ctx: Context) -> dict[str, Any]:
    """Write analysis results to a downloadable CSV report.

    Args:
        args: Analysis ID and output file path.
        ctx: Huitzo context providing storage, files, and logging.

    Returns:
        Confirmation with the output path and row count.
    """
    # Retrieve stored analysis
    analysis = await ctx.storage.get(f"{STORAGE_PREFIX}{args.analysis_id}")

    if analysis is None:
        return {
            "error": "not_found",
            "message": f"Analysis '{args.analysis_id}' not found. Run analyze-file first.",
        }

    stats = analysis["statistics"]

    # Build CSV content
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Analysis Report"])
    writer.writerow([f"Generated: {datetime.now(UTC).isoformat()}"])
    writer.writerow([f"Source: {analysis['file_path']}"])
    writer.writerow([f"Column: {analysis['column_name']}"])
    writer.writerow([])

    writer.writerow(["Metric", "Value"])
    writer.writerow(["Row Count", analysis["row_count"]])
    writer.writerow(["Numeric Values", analysis["numeric_values_count"]])
    for metric, value in stats.items():
        writer.writerow([metric.replace("_", " ").title(), value])

    csv_content = output.getvalue()

    # Write the report file
    written_path = await ctx.files.write(args.output_path, csv_content)

    ctx.log.info(f"Exported report to {written_path}")

    return {
        "exported": True,
        "analysis_id": args.analysis_id,
        "output_path": written_path,
        "metrics_count": len(stats),
    }
