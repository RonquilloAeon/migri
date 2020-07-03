import warnings
from typing import Optional

import click


class Echo:
    @classmethod
    def error(cls, message: str):
        click.secho(message, bold=True, fg="red")

    @classmethod
    def info(cls, message: str):
        click.echo(message)

    @classmethod
    def success(cls, message: str):
        click.secho(message, bold=True)


def deprecated(message: str, end_of_life: Optional[str] = None):
    """Use to warn of deprecation or pending deprecation. If end_of_life is provided,
    will append message with version in which functionality will be deprecated.
    And PendingDeprecationWarning will be used. Otherwise, DeprecationWarning will be
    used.

    :param message: Deprecation message
    :type message: str
    :param end_of_life: Version in which functionality will be deprecated
    :type end_of_life: str, optional
    """
    if end_of_life:
        message = f"{message} Will be removed in {end_of_life}."
        warning = PendingDeprecationWarning
    else:
        warning = DeprecationWarning

    warnings.warn(message, warning, stacklevel=2)
