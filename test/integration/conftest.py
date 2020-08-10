from test.asyncpg import configure, unconfigure


def pytest_configure(config):
    configure(config)


def pytest_unconfigure(config):
    unconfigure(config)
