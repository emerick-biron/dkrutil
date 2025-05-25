import rich_click as click
from click import ClickException
from docker.errors import DockerException

from ..core.docker_client import get_docker_client


@click.group(help="Manage Docker containers")
def container():
    pass


@container.command(help="List running Docker containers")
@click.option("-a", "--all", is_flag=True, default=False, help="Show all containers (including stopped ones)")
def ps(all: bool):
    try:
        client = get_docker_client()
    except DockerException as exc:
        raise ClickException(str(exc))

    containers = client.containers.list(all=all)
    container_names = sorted(container.name for container in containers)

    if not container_names:
        click.secho("No containers found", fg="yellow")
    else:
        click.secho("\n".join(container_names), fg="blue")
