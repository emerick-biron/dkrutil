import os
import shlex
import sys

import docker
import rich_click as click
from click import ClickException
from docker.errors import DockerException

from ..core.docker_client import get_docker_client


@click.group(help="Manage Docker secrets")
def secret():
    pass


@secret.command(
    help="Create a secret stored in a Docker volume from a file or from standard input"
)
@click.argument("name", required=True)
@click.argument("source", required=False, metavar="FILE|-")
@click.pass_context
def create(ctx, name: str, source: str | None):
    try:
        client = get_docker_client()
    except DockerException as exc:
        raise ClickException(str(exc))

    if source in (None, "-"):
        secret_content = sys.stdin.read().strip()
    else:
        if not os.path.isfile(source):
            raise click.BadParameter(
                message="File does not exist.",
                param_hint="source",
                ctx=ctx
            )
        try:
            with open(source, "r", encoding="utf-8") as f:
                secret_content = f.read().strip()
        except Exception as e:
            raise click.BadParameter(
                message=f"Failed to read file: {e}",
                param_hint="source",
                ctx=ctx
            )
    if not secret_content:
        raise click.BadParameter("Secret content is empty", param_hint="source")

    try:
        client.volumes.get(name)
        raise click.ClickException(f"Volume '{name}' already exists.")
    except docker.errors.NotFound:
        client.volumes.create(name=name)
        click.secho(f"Created volume '{name}'", fg="green")

    try:
        escaped = shlex.quote(secret_content)

        client.containers.run(
            image="alpine",
            command=f"sh -c \"printf %s {escaped} > /mnt/{name}\"",
            volumes={name: {"bind": "/mnt", "mode": "rw"}},
            remove=True,
        )
        click.secho(f"Secret written to volume '{name}'", fg="green")
    except Exception as e:
        raise click.ClickException(f"Failed to write secret to volume: {e}")
