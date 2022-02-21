from __future__ import with_statement

import logging.config
import os
from logging.config import fileConfig, dictConfig

import geoalchemy2
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context
from app.db.base import Base  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
from app.main import logging_config

config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None


target_metadata = Base.metadata

exclude_tables = config.get_section("alembic:exclude").get("tables", "").split(",")


def include_object(object, name, type_, *args, **kwargs):
    if type_ == "index":
        if name.startswith("idx") and name.endswith("geom"):
            return False
        else:
            return True
    return not (type_ == "table" and name in exclude_tables)


def get_url():
    debugging_config: str = os.getenv("DEBUGGING_CONFIG", None)
    if debugging_config is not None and len(debugging_config):
        load_dotenv(debugging_config)
    # if settings.USE_CONTAINER_TESTING_DB:
    #     return settings.SQLALCHEMY_DATABASE_TESTING_URI
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    server = os.getenv("POSTGRES_SERVER", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "app")
    return f"postgresql://{user}:{password}@{server}:{port}/{db}"


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def render_item(_, obj, autogen_context):
    """Apply custom rendering for selected items."""
    if isinstance(obj, geoalchemy2.types.Geometry):
        autogen_context.imports.add("from geoalchemy2.types import Geometry")
        return "%r" % obj

    # default rendering for other objects
    return False


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
