from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

import config  # noqa: F401  — loads .env before db.session reads DATABASE_URL
from db.session import DATABASE_URL
from models.entities import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
# Use DATABASE_URL directly — do NOT route through ConfigParser, which would
# treat '%' (from a percent-encoded password) as interpolation syntax.


def run_migrations_offline() -> None:
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, future=True)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
