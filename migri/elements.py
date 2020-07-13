import re
from typing import Any, Dict, List, Optional

Values = Optional[Dict[str, Any]]


class Query:
    """Query element. Use $-based substitutions for safe parameter substitutions across
    databases.

    :param statement: Query statement in `string.Template` format
        (e.g. "SELECT * FROM applied_migration WHERE id = $id)
    :type statement: str
    :param values: Dictionary of values that will be used to substitute placeholders
        (e.g. {"id": 2})
    :type values: dict, optional
    """

    def __init__(self, statement: str, values: Values = None):
        self._statement = statement
        self._values = values

    @property
    def placeholders(self) -> List[str]:
        return re.findall(r"\$(?:[_a-z][_a-z0-9]*)", self._statement)

    @property
    def statement(self) -> str:
        return self._statement

    @property
    def values(self) -> Values:
        return self._values
