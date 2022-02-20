import pytest

from migri.interfaces import ConnectionBackend


def test_connection_backend_min_args_not_satisfied():
    """If no db_name or connection is provided, raise an error"""
    with pytest.raises(RuntimeError):
        _ = ConnectionBackend()
