from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from aiomysql import Connection as MySQLConnection
    from aiosqlite import Connection as SQLiteConnection
    from asyncpg import Connection as PostgreSQLConnection

from migri.elements import Query
from migri.utils import Echo

Database = Union["MySQLConnection", "PostgreSQLConnection", "SQLiteConnection"]


@dataclass
class ConnectionBackend:
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_pass: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[Union[int, str]] = None
    # For providing backwards compatibility, to be removed in 1.1.0
    db: Optional[Database] = None
    _dialect: ClassVar[str] = "unknown"
    connection: ClassVar[object] = None

    def __post_init__(self):
        # Subclasses can make use of driver-specific db connection instances
        if not self.connection and not self.db_name:
            raise RuntimeError("Expected db_name or connection")

    async def __aenter__(self) -> "ConnectionBackend":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return self

    async def connect(self):
        raise NotImplementedError

    @property
    def database(self) -> Database:
        return self.db

    @property
    def dialect(self) -> str:
        return self._dialect

    async def disconnect(self):
        raise NotImplementedError

    async def execute(self, query: Query):
        raise NotImplementedError

    async def fetch(self, query: Query) -> Dict[str, Any]:
        raise NotImplementedError

    async def fetch_all(self, query: Query) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def transaction(self) -> "TransactionBackend":
        raise NotImplementedError


class TransactionBackend:
    def __init__(self, connection: ConnectionBackend):
        self._connection = connection

    async def __aenter__(self) -> "TransactionBackend":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()

    async def start(self):
        raise NotImplementedError

    async def commit(self):
        raise NotImplementedError

    async def rollback(self):
        raise NotImplementedError


class Task:
    def __init__(self, connection: ConnectionBackend):
        self.echo = Echo
        self._connection = connection

    async def run(self, *args, **kwargs):
        raise NotImplementedError
