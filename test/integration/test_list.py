from subprocess import Popen, PIPE

import pytest
from freezegun import freeze_time

pytestmark = pytest.mark.asyncio

postgresql_automated_migrations = {
    "0001_initial.sql": """
    CREATE TABLE organization (
        id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        name text NOT NULL,
        domain text NOT NULL
    );
    """,
    "0002_user_table.sql": """
    CREATE TABLE organization_user (
        id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        organization_id integer REFERENCES organization(id) NOT NULL,
        first_name text NOT NULL,
        last_name text NOT NULL,
        email text NOT NULL
    );
    """,
    "0003_ticket_table.sql": """
    CREATE TABLE ticket (
        id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        organization_id integer REFERENCES organization(id) NOT NULL,
        user_id integer REFERENCES organization_user(id)NOT NULL,
        created_at timestamptz NOT NULL,
        name text NOT NULL,
        description text NOT NULL
    );
    """,
}


def test_list_none_migrated(
    automated_migration_manager,
    generic_db_migri_command_base_args,
    migrations,
    postgresql_conn_factory,
    postgresql_connection_details,
):
    # Place migrations
    for name, content in postgresql_automated_migrations.items():
        automated_migration_manager(name, "create", content=content)

    args = generic_db_migri_command_base_args(postgresql_connection_details) + [
        "list",
        "-m",
        migrations["automated"],
    ]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    # Check output
    assert stdout.decode("utf-8") == (
        "0001_initial...not applied\n"
        "0002_user_table...not applied\n"
        "0003_ticket_table...not applied\n"
    )


@freeze_time("2020-8-12 20:30:01")
def test_list_all_migrated(
    automated_migration_manager,
    generic_db_migri_command_base_args,
    migrations,
    postgresql_conn_factory,
    postgresql_connection_details,
):
    # Place migrations
    for name, content in postgresql_automated_migrations.items():
        automated_migration_manager(name, "create", content=content)

    # Migrate
    args = generic_db_migri_command_base_args(postgresql_connection_details) + [
        "migrate",
        "-m",
        migrations["automated"],
    ]
    p = Popen(args, stdout=PIPE)
    p.communicate()

    # List migrations
    args = generic_db_migri_command_base_args(postgresql_connection_details) + [
        "list",
        "-m",
        migrations["automated"],
    ]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    # Check output
    assert stdout.decode("utf-8") == (
        "0001_initial...applied on 2020-08-12T20:30:01\n"
        "0002_user_table...applied on 2020-08-12T20:30:01\n"
        "0003_ticket_table...applied on 2020-08-12T20:30:01\n"
    )


@freeze_time("2020-8-12 20:30:01")
def test_list_partially_applied(
    automated_migration_manager,
    generic_db_migri_command_base_args,
    migrations,
    postgresql_conn_factory,
    postgresql_connection_details,
):
    # Place one migration
    automated_migration_manager(
        "0001_initial.sql",
        "create",
        content=postgresql_automated_migrations["0001_initial.sql"],
    )

    # Migrate migration
    args = generic_db_migri_command_base_args(postgresql_connection_details) + [
        "migrate",
        "-m",
        migrations["automated"],
    ]
    p = Popen(args, stdout=PIPE)
    p.communicate()

    # Place other migrations
    pending_migrations = ["0002_user_table.sql", "0003_ticket_table.sql"]

    for migration in pending_migrations:
        automated_migration_manager(
            migration, "create", content=postgresql_automated_migrations[migration]
        )

    # List migrations
    args = generic_db_migri_command_base_args(postgresql_connection_details) + [
        "list",
        "-m",
        migrations["automated"],
    ]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    # Check output
    assert stdout.decode("utf-8") == (
        "0001_initial...applied on 2020-08-12T20:30:01\n"
        "0002_user_table...not applied\n"
        "0003_ticket_table...not applied\n"
    )
