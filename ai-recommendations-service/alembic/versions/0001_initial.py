"""initial recommendation jobs"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    status = sa.Enum("queued", "processing", "completed", "failed", "cancelled", name="jobstatus")
    op.create_table("recommendation_jobs", sa.Column("id", postgresql.UUID(), primary_key=True), sa.Column("external_job_id", postgresql.UUID(), nullable=False), sa.Column("site_id", sa.Integer(), nullable=False), sa.Column("site_domain", sa.String(253), nullable=False), sa.Column("recommendation_type", sa.String(20), nullable=False), sa.Column("input_data", sa.JSON(), nullable=False), sa.Column("result", sa.JSON()), sa.Column("status", status, nullable=False), sa.Column("attempt", sa.Integer(), nullable=False), sa.Column("openai_model", sa.String(100)), sa.Column("input_tokens", sa.Integer()), sa.Column("output_tokens", sa.Integer()), sa.Column("error_message", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("deleted_at", sa.DateTime(timezone=True)))
    op.create_index("ix_recommendation_jobs_external_job_id", "recommendation_jobs", ["external_job_id"], unique=True)
    op.create_index("ix_recommendation_jobs_site_id", "recommendation_jobs", ["site_id"])
    op.create_index("ix_recommendation_jobs_status", "recommendation_jobs", ["status"])
def downgrade():
    op.drop_table("recommendation_jobs")
    sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)
