from subprocess import Popen, PIPE

import pytest

from migri.elements import Query

pytestmark = pytest.mark.asyncio


async def test_list_none_migrated(
    generic_db_migri_command_base_args,
    migrations,
    postgresql_connection_details,
    postgresql_db,
):
    ...
