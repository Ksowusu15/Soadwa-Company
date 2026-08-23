"""Add client testimonials

Revision ID: 7f42a1e9c2d1
Revises: 0a2c5e85c896
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa

revision = "7f42a1e9c2d1"
down_revision = "0a2c5e85c896"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "testimonial",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_name", sa.String(length=120), nullable=False),
        sa.Column("client_title", sa.String(length=160), nullable=True),
        sa.Column("testimonial", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("image", sa.String(length=255), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("testimonial", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_testimonial_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_testimonial_display_order"), ["display_order"], unique=False)
        batch_op.create_index(batch_op.f("ix_testimonial_is_active"), ["is_active"], unique=False)


def downgrade():
    with op.batch_alter_table("testimonial", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_testimonial_is_active"))
        batch_op.drop_index(batch_op.f("ix_testimonial_display_order"))
        batch_op.drop_index(batch_op.f("ix_testimonial_created_at"))
    op.drop_table("testimonial")
