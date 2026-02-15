"""
Smart Notes Pack Commands.

Implements:
    - docs/sdk/commands.md#the-command-decorator
    - docs/sdk/context.md#storage-api

This module provides four commands for managing personal notes:
    - save-note: Create or update a note by title
    - get-note: Retrieve a note by title
    - list-notes: List all saved notes
    - delete-note: Delete a note by title

See Also:
    - docs/sdk/context.md (for Context API)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# SDK placeholder types (replaced at runtime by huitzo-sdk)
# ---------------------------------------------------------------------------

if TYPE_CHECKING:

    class StorageService(Protocol):
        """Protocol for the Huitzo storage service."""

        async def set(self, key: str, data: dict[str, Any]) -> None: ...
        async def get(self, key: str) -> dict[str, Any] | None: ...
        async def list(self, prefix: str, limit: int = 100) -> list[dict[str, Any]]: ...
        async def delete(self, key: str) -> bool: ...

    class LogService(Protocol):
        """Protocol for the Huitzo logging service."""

        def info(self, message: str) -> None: ...
        def warning(self, message: str) -> None: ...
        def error(self, message: str) -> None: ...

    class Context(Protocol):
        """Protocol for the Huitzo execution context."""

        storage: StorageService
        log: LogService


def command(
    name: str,
    *,
    namespace: str,
    timeout: int = 60,
    retries: int = 3,
    queue: str = "default",
) -> Any:
    """Decorator placeholder for the @command pattern.

    When huitzo-sdk 2.0.0 is available, this will be replaced by the real
    decorator. See docs/sdk/commands.md for details.
    """

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

STORAGE_PREFIX = "note:"


class SaveNoteArgs(BaseModel):
    """Arguments for the save-note command."""

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Title of the note (used as unique key)",
    )
    content: str = Field(
        min_length=1,
        max_length=10_000,
        description="Body text of the note",
    )


class GetNoteArgs(BaseModel):
    """Arguments for the get-note command."""

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Title of the note to retrieve",
    )


class ListNotesArgs(BaseModel):
    """Arguments for the list-notes command."""

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of notes to return",
    )


class DeleteNoteArgs(BaseModel):
    """Arguments for the delete-note command."""

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Title of the note to delete",
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@command("save-note", namespace="notes", timeout=30)
async def save_note(args: SaveNoteArgs, ctx: Context) -> dict[str, Any]:
    """Save or update a note by title.

    If a note with the same title already exists it will be overwritten.

    Args:
        args: Note title and content.
        ctx: Huitzo context providing storage and logging.

    Returns:
        The saved note data including timestamps.
    """
    key = f"{STORAGE_PREFIX}{args.title}"
    now = datetime.now(UTC).isoformat()

    # Check if note already exists (for updated_at tracking)
    existing = await ctx.storage.get(key)

    note_data: dict[str, Any] = {
        "title": args.title,
        "content": args.content,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }

    await ctx.storage.set(key, note_data)

    action = "Updated" if existing else "Created"
    ctx.log.info(f"{action} note: {args.title}")

    return note_data


@command("get-note", namespace="notes", timeout=15)
async def get_note(args: GetNoteArgs, ctx: Context) -> dict[str, Any]:
    """Retrieve a note by its title.

    Args:
        args: Title of the note to retrieve.
        ctx: Huitzo context providing storage and logging.

    Returns:
        The note data, or an error message if not found.
    """
    key = f"{STORAGE_PREFIX}{args.title}"
    note = await ctx.storage.get(key)

    if note is None:
        ctx.log.warning(f"Note not found: {args.title}")
        return {"error": "not_found", "message": f"Note '{args.title}' not found"}

    ctx.log.info(f"Retrieved note: {args.title}")
    return note


@command("list-notes", namespace="notes", timeout=15)
async def list_notes(args: ListNotesArgs, ctx: Context) -> dict[str, Any]:
    """List all saved notes with an optional limit.

    Args:
        args: Limit for the number of notes returned.
        ctx: Huitzo context providing storage and logging.

    Returns:
        A list of notes and the total count.
    """
    notes = await ctx.storage.list(STORAGE_PREFIX, limit=args.limit)

    ctx.log.info(f"Listed {len(notes)} notes (limit={args.limit})")

    return {
        "notes": notes,
        "count": len(notes),
        "limit": args.limit,
    }


@command("delete-note", namespace="notes", timeout=15)
async def delete_note(args: DeleteNoteArgs, ctx: Context) -> dict[str, Any]:
    """Delete a note by its title.

    Args:
        args: Title of the note to delete.
        ctx: Huitzo context providing storage and logging.

    Returns:
        Confirmation of deletion, or an error if the note was not found.
    """
    key = f"{STORAGE_PREFIX}{args.title}"
    deleted = await ctx.storage.delete(key)

    if not deleted:
        ctx.log.warning(f"Note not found for deletion: {args.title}")
        return {"error": "not_found", "message": f"Note '{args.title}' not found"}

    ctx.log.info(f"Deleted note: {args.title}")
    return {"deleted": True, "title": args.title}
