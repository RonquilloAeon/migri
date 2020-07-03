import nox


@nox.session(python="3.7", reuse_venv=True)
def dev(session):
    """For creating a development virtual environment. Handy for setting interpreter in
    IDE.
    """
    session.install(".")


@nox.session(python="3.7", reuse_venv=True)
def format(session):
    session.install("black")
    session.run("black", "migri", "test")


@nox.session(python="3.7", reuse_venv=True)
def check(session):
    session.install("flake8")
    session.run("flake8", "migri")


@nox.session(python=["3.7", "3.8"], reuse_venv=True)
def test(session):
    session.install("-r", "test-requirements.txt")
    session.run("pytest", "--cov=migri", *session.posargs)
