import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.db.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url():
    """Get the database URL from settings"""
    # Handle SQLite specially for alembic
    if 'sqlite' in settings.DATABASE_URL.lower():
        return settings.DATABASE_URL.replace('sqlite://', 'sqlite:///')
    # If PostgreSQL with asyncpg, convert to standard URL for alembic
    elif '+asyncpg' in settings.DATABASE_URL:
        return settings.DATABASE_URL.replace('+asyncpg', '')
    return str(settings.DATABASE_URL)

def run_migrations_offline() -> None:
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
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # If using SQLite, we need to use a different approach
    if 'sqlite' in settings.DATABASE_URL.lower():
        # Configure using SQLAlchemy sync API for SQLite
        from sqlalchemy import create_engine
        connectable = create_engine(get_url())
        with connectable.connect() as connection:
            context.configure(
                connection=connection, 
                target_metadata=target_metadata
            )
            with context.begin_transaction():
                context.run_migrations()
    else:
        # For PostgreSQL or other async-supported DBs, use the async approach
        config_section = config.get_section(config.config_ini_section)
        url = get_url()
        config_section["sqlalchemy.url"] = url

        connectable = async_engine_from_config(
            config_section,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
