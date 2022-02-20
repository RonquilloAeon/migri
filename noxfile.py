import nox


def _install_dev_dependencies(session):
    session.install("aiomysql")
    session.install("aiosqlite")
    session.install("asyncpg")
    session.install("-r", "test-requirements.txt")


@nox.session(python="3.7", reuse_venv=True)
def dev(session):
    """For creating a development virtual environment. Handy for setting interpreter in
    IDE.
    """
    _install_dev_dependencies(session)


@nox.session(python="3.7", reuse_venv=True)
def format(session):
    session.install("black")
    session.run("black", "migri", "test", *session.posargs)


@nox.session(python="3.7", reuse_venv=True)
def lint(session):
    session.install("flake8")
    session.run("flake8", "migri")


@nox.session(python=["3.7", "3.8", "3.9", "3.10"], reuse_venv=True)
@nox.parametrize("db_library", ["aiomysql", "aiosqlite", "asyncpg"])
def test_by_dialect(session, db_library):
    session.install("-e", ".")
    session.install(db_library)
    session.install("-r", "test-requirements.txt")

    session.run("pytest", f"test/{db_library}")


@nox.session(python=["3.7", "3.8", "3.9", "3.10"], reuse_venv=True)
def test(session):
    _install_dev_dependencies(session)

    session.run("pytest", "--cov=migri", *session.posargs)
