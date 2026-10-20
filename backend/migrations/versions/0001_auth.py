"""账号与服务端会话；仅初始化本次功能的表。"""
from alembic import op
import sqlalchemy as sa

revision = "0001_auth"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(20), nullable=False),
        sa.Column("username_normalized", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(10), server_default="user", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("username_normalized", name="uq_users_username_normalized"),
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
        sa.CheckConstraint("char_length(username) BETWEEN 3 AND 20", name="ck_users_username_length"),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False),
        sa.Column("csrf_token", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
        sa.CheckConstraint("octet_length(token_hash) = 32", name="ck_sessions_token_hash_length"),
        sa.CheckConstraint("expires_at > created_at", name="ck_sessions_expiry"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])


def downgrade():
    op.drop_table("sessions")
    op.drop_table("users")
