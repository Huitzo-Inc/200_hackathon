"""
Tests for the smart-notes pack commands.

Implements:
    - docs/sdk/commands.md#testing-commands

Tests cover:
    - Pydantic argument validation for all four commands
    - Command execution with mocked Context
    - Storage interactions (set, get, list, delete)
    - Edge cases (not found, duplicate titles, limits)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from smart_notes.commands import (
    DeleteNoteArgs,
    GetNoteArgs,
    ListNotesArgs,
    SaveNoteArgs,
    delete_note,
    get_note,
    list_notes,
    save_note,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_ctx(
    storage_get: Any = None,
    storage_list: Any = None,
    storage_delete: bool = True,
) -> MagicMock:
    """Build a mock Context with configurable storage responses."""
    ctx = MagicMock()
    ctx.storage.set = AsyncMock()
    ctx.storage.get = AsyncMock(return_value=storage_get)
    ctx.storage.list = AsyncMock(return_value=storage_list or [])
    ctx.storage.delete = AsyncMock(return_value=storage_delete)
    ctx.log = MagicMock()
    return ctx


# ---------------------------------------------------------------------------
# SaveNoteArgs validation
# ---------------------------------------------------------------------------


class TestSaveNoteArgs:
    """Validate SaveNoteArgs Pydantic model."""

    def test_valid(self) -> None:
        args = SaveNoteArgs(title="Hello", content="World")
        assert args.title == "Hello"
        assert args.content == "World"

    def test_empty_title_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SaveNoteArgs(title="", content="Body")

    def test_empty_content_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SaveNoteArgs(title="Title", content="")

    def test_title_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SaveNoteArgs(title="x" * 201, content="Body")

    def test_content_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SaveNoteArgs(title="Title", content="x" * 10_001)


# ---------------------------------------------------------------------------
# GetNoteArgs validation
# ---------------------------------------------------------------------------


class TestGetNoteArgs:
    """Validate GetNoteArgs Pydantic model."""

    def test_valid(self) -> None:
        args = GetNoteArgs(title="Meeting Notes")
        assert args.title == "Meeting Notes"

    def test_empty_title_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GetNoteArgs(title="")


# ---------------------------------------------------------------------------
# ListNotesArgs validation
# ---------------------------------------------------------------------------


class TestListNotesArgs:
    """Validate ListNotesArgs Pydantic model."""

    def test_default_limit(self) -> None:
        args = ListNotesArgs()
        assert args.limit == 10

    def test_custom_limit(self) -> None:
        args = ListNotesArgs(limit=50)
        assert args.limit == 50

    def test_zero_limit_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListNotesArgs(limit=0)

    def test_negative_limit_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListNotesArgs(limit=-5)

    def test_over_max_limit_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ListNotesArgs(limit=101)


# ---------------------------------------------------------------------------
# DeleteNoteArgs validation
# ---------------------------------------------------------------------------


class TestDeleteNoteArgs:
    """Validate DeleteNoteArgs Pydantic model."""

    def test_valid(self) -> None:
        args = DeleteNoteArgs(title="Old Note")
        assert args.title == "Old Note"

    def test_empty_title_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DeleteNoteArgs(title="")


# ---------------------------------------------------------------------------
# save_note command
# ---------------------------------------------------------------------------


class TestSaveNote:
    """Test save_note command execution."""

    @pytest.mark.asyncio
    async def test_creates_new_note(self) -> None:
        ctx = _make_ctx(storage_get=None)
        args = SaveNoteArgs(title="New Note", content="Some content")

        result = await save_note(args, ctx)

        assert result["title"] == "New Note"
        assert result["content"] == "Some content"
        assert "created_at" in result
        assert "updated_at" in result
        ctx.storage.set.assert_awaited_once()
        ctx.log.info.assert_called()

    @pytest.mark.asyncio
    async def test_updates_existing_note(self) -> None:
        existing = {
            "title": "Old",
            "content": "Old content",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        ctx = _make_ctx(storage_get=existing)
        args = SaveNoteArgs(title="Old", content="Updated content")

        result = await save_note(args, ctx)

        assert result["content"] == "Updated content"
        # created_at should be preserved from the original note
        assert result["created_at"] == "2026-01-01T00:00:00+00:00"


# ---------------------------------------------------------------------------
# get_note command
# ---------------------------------------------------------------------------


class TestGetNote:
    """Test get_note command execution."""

    @pytest.mark.asyncio
    async def test_returns_existing_note(self) -> None:
        note = {"title": "Hello", "content": "World", "created_at": "now", "updated_at": "now"}
        ctx = _make_ctx(storage_get=note)
        args = GetNoteArgs(title="Hello")

        result = await get_note(args, ctx)

        assert result["title"] == "Hello"
        assert result["content"] == "World"

    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        ctx = _make_ctx(storage_get=None)
        args = GetNoteArgs(title="Missing")

        result = await get_note(args, ctx)

        assert result["error"] == "not_found"
        ctx.log.warning.assert_called()


# ---------------------------------------------------------------------------
# list_notes command
# ---------------------------------------------------------------------------


class TestListNotes:
    """Test list_notes command execution."""

    @pytest.mark.asyncio
    async def test_returns_notes(self) -> None:
        notes = [
            {"title": "A", "content": "a"},
            {"title": "B", "content": "b"},
        ]
        ctx = _make_ctx(storage_list=notes)
        args = ListNotesArgs(limit=10)

        result = await list_notes(args, ctx)

        assert result["count"] == 2
        assert result["limit"] == 10
        assert len(result["notes"]) == 2

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        ctx = _make_ctx(storage_list=[])
        args = ListNotesArgs()

        result = await list_notes(args, ctx)

        assert result["count"] == 0
        assert result["notes"] == []


# ---------------------------------------------------------------------------
# delete_note command
# ---------------------------------------------------------------------------


class TestDeleteNote:
    """Test delete_note command execution."""

    @pytest.mark.asyncio
    async def test_deletes_existing_note(self) -> None:
        ctx = _make_ctx(storage_delete=True)
        args = DeleteNoteArgs(title="Remove Me")

        result = await delete_note(args, ctx)

        assert result["deleted"] is True
        assert result["title"] == "Remove Me"

    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        ctx = _make_ctx(storage_delete=False)
        args = DeleteNoteArgs(title="Missing")

        result = await delete_note(args, ctx)

        assert result["error"] == "not_found"
        ctx.log.warning.assert_called()
