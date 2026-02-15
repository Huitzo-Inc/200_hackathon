"""
Tests for the data-cruncher pack commands.

Implements:
    - docs/sdk/commands.md#testing-commands

Tests cover:
    - Pydantic argument validation for all three commands
    - Statistics computation helper
    - Command execution with mocked Context (files, storage, LLM)
    - Error handling (missing files, missing columns, not-found analysis)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from data_cruncher.commands import (
    AIInsightsArgs,
    AnalyzeFileArgs,
    ExportReportArgs,
    _compute_statistics,
    _parse_numeric_column,
    ai_insights,
    analyze_file,
    export_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ROWS = [
    {"date": "2026-01-05", "product": "Widget A", "region": "North", "units_sold": "150", "revenue": "4498.50"},
    {"date": "2026-01-12", "product": "Widget B", "region": "South", "units_sold": "80", "revenue": "3999.20"},
    {"date": "2026-01-19", "product": "Widget A", "region": "East", "units_sold": "200", "revenue": "5998.00"},
    {"date": "2026-01-26", "product": "Widget C", "region": "West", "units_sold": "45", "revenue": "4499.55"},
]


def _make_ctx(
    file_rows: list[dict[str, str]] | None = None,
    storage_get: dict[str, Any] | None = None,
    llm_response: dict[str, Any] | None = None,
    written_path: str = "/output/report.csv",
) -> MagicMock:
    """Build a mock Context with configurable file, storage, and LLM responses."""
    ctx = MagicMock()
    ctx.files.read_csv = AsyncMock(return_value=file_rows or [])
    ctx.files.write = AsyncMock(return_value=written_path)
    ctx.storage.set = AsyncMock()
    ctx.storage.get = AsyncMock(return_value=storage_get)
    ctx.llm.complete = AsyncMock(return_value=llm_response or {})
    ctx.log = MagicMock()
    return ctx


# ---------------------------------------------------------------------------
# AnalyzeFileArgs validation
# ---------------------------------------------------------------------------


class TestAnalyzeFileArgs:
    def test_valid(self) -> None:
        args = AnalyzeFileArgs(file_path="data/sales.csv", column_name="revenue")
        assert args.file_path == "data/sales.csv"
        assert args.column_name == "revenue"

    def test_empty_file_path_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AnalyzeFileArgs(file_path="", column_name="revenue")

    def test_empty_column_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AnalyzeFileArgs(file_path="data/sales.csv", column_name="")


# ---------------------------------------------------------------------------
# AIInsightsArgs validation
# ---------------------------------------------------------------------------


class TestAIInsightsArgs:
    def test_valid(self) -> None:
        args = AIInsightsArgs(analysis_id="analysis-abc12345")
        assert args.analysis_id == "analysis-abc12345"

    def test_empty_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AIInsightsArgs(analysis_id="")


# ---------------------------------------------------------------------------
# ExportReportArgs validation
# ---------------------------------------------------------------------------


class TestExportReportArgs:
    def test_valid(self) -> None:
        args = ExportReportArgs(analysis_id="analysis-abc12345", output_path="report.csv")
        assert args.output_path == "report.csv"

    def test_empty_output_path_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExportReportArgs(analysis_id="analysis-abc12345", output_path="")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestComputeStatistics:
    def test_basic_stats(self) -> None:
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = _compute_statistics(values)
        assert stats["count"] == 5
        assert stats["sum"] == 150.0
        assert stats["mean"] == 30.0
        assert stats["median"] == 30.0
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0

    def test_single_value(self) -> None:
        stats = _compute_statistics([42.0])
        assert stats["count"] == 1
        assert stats["mean"] == 42.0
        assert stats["stdev"] == 0.0

    def test_two_values(self) -> None:
        stats = _compute_statistics([10.0, 20.0])
        assert stats["count"] == 2
        assert stats["mean"] == 15.0


class TestParseNumericColumn:
    def test_extracts_numbers(self) -> None:
        values = _parse_numeric_column(SAMPLE_ROWS, "units_sold")
        assert values == [150.0, 80.0, 200.0, 45.0]

    def test_skips_non_numeric(self) -> None:
        values = _parse_numeric_column(SAMPLE_ROWS, "product")
        assert values == []

    def test_missing_column_returns_empty(self) -> None:
        values = _parse_numeric_column(SAMPLE_ROWS, "nonexistent")
        assert values == []


# ---------------------------------------------------------------------------
# analyze_file command
# ---------------------------------------------------------------------------


class TestAnalyzeFile:
    @pytest.mark.asyncio
    async def test_analyzes_csv(self) -> None:
        ctx = _make_ctx(file_rows=SAMPLE_ROWS)
        args = AnalyzeFileArgs(file_path="data/sales.csv", column_name="revenue")

        result = await analyze_file(args, ctx)

        assert "analysis_id" in result
        assert result["column_name"] == "revenue"
        assert result["row_count"] == 4
        assert result["statistics"]["count"] == 4
        ctx.storage.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_file(self) -> None:
        ctx = _make_ctx(file_rows=[])
        args = AnalyzeFileArgs(file_path="empty.csv", column_name="revenue")

        result = await analyze_file(args, ctx)

        assert result["error"] == "empty_file"

    @pytest.mark.asyncio
    async def test_column_not_found(self) -> None:
        ctx = _make_ctx(file_rows=SAMPLE_ROWS)
        args = AnalyzeFileArgs(file_path="data/sales.csv", column_name="profit")

        result = await analyze_file(args, ctx)

        assert result["error"] == "column_not_found"

    @pytest.mark.asyncio
    async def test_no_numeric_data(self) -> None:
        ctx = _make_ctx(file_rows=SAMPLE_ROWS)
        args = AnalyzeFileArgs(file_path="data/sales.csv", column_name="product")

        result = await analyze_file(args, ctx)

        assert result["error"] == "no_numeric_data"


# ---------------------------------------------------------------------------
# ai_insights command
# ---------------------------------------------------------------------------


class TestAIInsights:
    @pytest.mark.asyncio
    async def test_generates_insights(self) -> None:
        stored = {
            "analysis_id": "analysis-abc12345",
            "file_path": "sales.csv",
            "column_name": "revenue",
            "row_count": 16,
            "numeric_values_count": 16,
            "statistics": {
                "count": 16,
                "sum": 82000.0,
                "mean": 5125.0,
                "median": 5248.25,
                "min": 3499.65,
                "max": 6998.60,
                "stdev": 950.0,
            },
            "columns": ["date", "product", "region", "units_sold", "revenue"],
        }
        llm_resp = {
            "summary": "Revenue is healthy with consistent growth.",
            "insights": ["Revenue is well-distributed", "Low standard deviation indicates consistency"],
            "recommendations": ["Focus on Widget A for highest volume"],
            "data_quality": "good",
        }
        ctx = _make_ctx(storage_get=stored, llm_response=llm_resp)
        args = AIInsightsArgs(analysis_id="analysis-abc12345")

        result = await ai_insights(args, ctx)

        assert result["ai_summary"] == "Revenue is healthy with consistent growth."
        assert len(result["ai_insights"]) == 2
        assert len(result["ai_recommendations"]) == 1
        assert result["data_quality"] == "good"
        ctx.llm.complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analysis_not_found(self) -> None:
        ctx = _make_ctx(storage_get=None)
        args = AIInsightsArgs(analysis_id="missing-id")

        result = await ai_insights(args, ctx)

        assert result["error"] == "not_found"


# ---------------------------------------------------------------------------
# export_report command
# ---------------------------------------------------------------------------


class TestExportReport:
    @pytest.mark.asyncio
    async def test_exports_csv(self) -> None:
        stored = {
            "analysis_id": "analysis-abc12345",
            "file_path": "sales.csv",
            "column_name": "revenue",
            "row_count": 16,
            "numeric_values_count": 16,
            "statistics": {
                "count": 16,
                "sum": 82000.0,
                "mean": 5125.0,
                "median": 5248.25,
                "min": 3499.65,
                "max": 6998.60,
                "stdev": 950.0,
            },
        }
        ctx = _make_ctx(storage_get=stored, written_path="/output/report.csv")
        args = ExportReportArgs(analysis_id="analysis-abc12345", output_path="report.csv")

        result = await export_report(args, ctx)

        assert result["exported"] is True
        assert result["output_path"] == "/output/report.csv"
        ctx.files.write.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analysis_not_found(self) -> None:
        ctx = _make_ctx(storage_get=None)
        args = ExportReportArgs(analysis_id="missing-id", output_path="report.csv")

        result = await export_report(args, ctx)

        assert result["error"] == "not_found"
