from sqlalchemy import Text, text, UniqueConstraint, Numeric
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

class Model(TableBase):
    __tablename__ = "models"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "model_name", "start_date", "unit"
            , name="models_project_id_model_name_start_date_unit_key"
        ),
    )

    id = mapped_column(Text, primary_key=True)
    created_at = mapped_column(TZDateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = mapped_column(TZDateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    project_id = mapped_column(Text)
    model_name = mapped_column(Text, nullable=False, index=True)
    match_pattern = mapped_column(Text, nullable=False)
    start_date = mapped_column(TZDateTime)
    input_price = mapped_column(Numeric)
    output_price = mapped_column(Numeric)
    total_price = mapped_column(Numeric)
    unit = mapped_column(Text)
    tokenizer_config = mapped_column(Text)
    tokenizer_id = mapped_column(Text)
