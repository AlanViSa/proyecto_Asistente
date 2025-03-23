from setuptools import setup, find_packages

setup(
    name="salon-assistant",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.27.1",
        "pydantic>=2.0.0",
        "sqlalchemy[asyncio]>=2.0.25",
        "alembic>=1.13.1",
        "asyncpg>=0.29.0",
    ],
) 