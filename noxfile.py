import nox


@nox.session(python="3.7", reuse_venv=True)
def test(session):
    session.install("-r", "test-requirements.txt")
    session.run("pytest", *session.posargs)
