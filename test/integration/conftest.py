from test import aiomysql, asyncpg


def pytest_configure(config):
    aiomysql.configure(config)
    asyncpg.configure(config)


def pytest_unconfigure(config):
    aiomysql.unconfigure(config)
    asyncpg.unconfigure(config)
