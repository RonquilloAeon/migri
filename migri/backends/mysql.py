import re
from typing import Any, Dict, List

import aiomysql

from migri.elements import Query
from migri.interfaces import ConnectionBackend, TransactionBackend


class MySQLConnection(ConnectionBackend):
    dialect = "mysql"

    @staticmethod
    def _compile(query: Query) -> dict:
        q = query.statement
        v = []

        if query.placeholders:
            for p in query.placeholders:
                # Append value
                v.append(query.values[p.replace("$", "")])

                # Substitute
                q = re.sub(f"\\{p}", "%s", q)

        return {"query": q, "values": v}

    async def connect(self):
        ...

    async def disconnect(self):
        ...

    async def execute(self, query: Query):
        ...

    async def fetch(self, query: Query) -> Dict[str, Any]:
        ...

    async def fetch_all(self, query: Query) -> List[Dict[str, Any]]:
        ...

    def transaction(self) -> "TransactionBackend":
        ...


class MySQLTransaction(TransactionBackend):
    async def start(self):
        ...

    async def commit(self):
        ...

    async def rollback(self):
        ...
