"""embedding column'nın eklenmesi

Revision ID: 44851c3e617f
Revises: 595b5624d59c
Create Date: 2026-11-07 13:53:57.248769

"""

from collections.abc import Sequence

import pgvector
import pgvector.sqlalchemy
import sqlalchemy as sa

from alembic import op
from app.config import settings

# revision identifiers, used by Alembic.
revision: str = "44851c3e617f"
down_revision: str | Sequence[str] | None = "595b5624d59c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "posts",
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=settings.EMBEDDING_DIMENSIONS),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_posts_embedding",
        "posts",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_posts_embedding", table_name="posts", postgresql_using="hnsw")
    op.drop_column("posts", "embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
