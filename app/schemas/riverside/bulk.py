"""Riverside bulk operations and pagination schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(
        default_factory=list,
        description="List of items for the current page",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of items",
        examples=[100],
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number",
        examples=[1],
    )
    page_size: int = Field(
        ...,
        ge=1,
        description="Number of items per page",
        examples=[20],
    )
    pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages",
        examples=[5],
    )
    has_next: bool = Field(
        ...,
        description="Whether there is a next page",
        examples=[True],
    )
    has_previous: bool = Field(
        ...,
        description="Whether there is a previous page",
        examples=[False],
    )


class BulkUpdateItem(BaseModel):
    """Single item for bulk update operation."""

    id: int = Field(
        ...,
        description="ID of the item to update",
        examples=[1],
    )
    updates: dict = Field(
        ...,
        description="Dictionary of fields to update",
        examples=[{"status": "completed", "evidence_notes": "Verified"}],
    )


class BulkUpdateRequest(BaseModel):
    """Request schema for batch update operations."""

    items: list[BulkUpdateItem] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of items to update",
    )


class BulkUpdateResponse(BaseModel):
    """Response schema for batch update operations."""

    processed: int = Field(
        ...,
        ge=0,
        description="Number of items processed",
        examples=[50],
    )
    succeeded: int = Field(
        ...,
        ge=0,
        description="Number of successful updates",
        examples=[48],
    )
    failed: int = Field(
        ...,
        ge=0,
        description="Number of failed updates",
        examples=[2],
    )
    errors: list[dict] = Field(
        default_factory=list,
        description="List of errors if any",
        examples=[[{"id": 5, "error": "Item not found"}]],
    )
