import click


@click.group()
def cli():
    pass


@click.command()
def migrate():
    click.echo('Migrating')


def main():
    cli.add_command(migrate)
    cli()
