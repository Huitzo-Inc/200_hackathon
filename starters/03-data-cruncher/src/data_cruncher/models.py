"""
Module: models
Description: Pydantic models for data cruncher arguments and responses.

Implements:
    - docs/sdk/commands.md#argument-validation

Note: The commands module defines its own argument models inline.
This module provides the canonical model definitions for reference
and external usage.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Argument models (mirrored from commands.py for external use)
# ---------------------------------------------------------------------------


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
