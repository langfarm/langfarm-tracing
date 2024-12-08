from sqlalchemy import Text, text, UniqueConstraint
from sqlalchemy.orm import mapped_column

from langfarm_tracing.schema import TableBase, TZDateTime


class ApiKey(TableBase):
    __tablename__ = "api_keys"
    __table_args__ = (
        UniqueConstraint("hashed_secret_key", name="uq_hashed_secret_key"),
        UniqueConstraint("fast_hashed_secret_key", name="uq_fast_hashed_secret_key"),
        UniqueConstraint("public_key", name="uq_public_key"),
    )

    id = mapped_column(Text, primary_key=True)
    created_at = mapped_column(TZDateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    note = mapped_column(Text)
    public_key = mapped_column(Text, nullable=False, index=True)
    hashed_secret_key = mapped_column(Text, nullable=False, index=True)
    display_secret_key = mapped_column(Text, nullable=False)
    last_used_at = mapped_column(TZDateTime)
    expires_at = mapped_column(TZDateTime)
    project_id = mapped_column(Text, nullable=False, index=True)
    fast_hashed_secret_key = mapped_column(Text, index=True)
