import os
import re
from datetime import datetime

import rich_click as click
from click import BadParameter
from click import ClickException, UsageError
from docker.errors import DockerException
from rich.live import Live
from rich.panel import Panel

from .rich import volumes_progress
from ..core.docker_client import get_docker_client


@click.group(help="Manage Docker volumes")
def volume():
    pass


@volume.command(help="Backup Docker volumes to a specified directory")
@click.option(
    "-d",
    "--backup-directory",
    required=True,
    type=click.Path(exists=True, file_okay=False, writable=True),
    help="Directory where Docker volume backups will be stored"
)
@click.option("-I", "--ignore", multiple=True, help="Regex pattern to ignore specific volumes (can be repeated)")
@click.option("-i", "--include", multiple=True, help="Regex pattern to include specific volumes (can be repeated)")
@click.option("-v", "--verbose", is_flag=True, help="Show skipped volumes in real time")
def backup(backup_directory: str, ignore: list[str], include: list[str], verbose: bool):
    try:
        client = get_docker_client()
    except DockerException as exc:
        raise ClickException(str(exc))

    backup_directory = os.path.abspath(backup_directory)

    if not os.path.isdir(backup_directory):
        raise BadParameter(f"Backup directory '{backup_directory}' does not exist")

    all_volumes = [v.name for v in client.volumes.list()]
    if include:
        selected_volumes = [v for v in all_volumes if any(re.search(pattern, v) for pattern in include)]
    else:
        selected_volumes = all_volumes
    selected_volumes = [v for v in selected_volumes if not any(re.search(pattern, v) for pattern in ignore)]

    if not selected_volumes:
        raise UsageError("No volumes match the provided filters.")

    date_suffix = datetime.now().strftime("%Y-%m-%d")

    click.secho(f"Backing up Docker volumes to {backup_directory}", fg="blue", bold=True)

    with Live(Panel(volumes_progress, border_style="green"), transient=True) as live:
        task = volumes_progress.add_task("Backing up volumes", total=len(selected_volumes))

        for volume_name in all_volumes:
            if volume_name not in selected_volumes:
                if verbose:
                    live.console.print(f"[yellow bold]Skipped:[/] {volume_name}")
                continue

            backup_filename = f"{volume_name}_{date_suffix}.tar.gz"

            try:
                client.containers.run(
                    image="alpine",
                    command=f"tar czf /backup/{backup_filename} -C /volume .",
                    volumes={
                        volume_name: {"bind": "/volume", "mode": "ro"},
                        backup_directory: {"bind": "/backup", "mode": "rw"},
                    },
                    remove=True
                )
                live.console.print(f"[green bold]Backed up:[/] {volume_name}")
            except Exception as e:
                live.console.print(f"[red bold]Error:[/]     {volume_name} - {e}", highlight=False)
            finally:
                volumes_progress.update(task, advance=1)

    click.secho("Finished Successfully", fg="green", bold=True)


@volume.command(help="Restore Docker volumes from a backup directory")
@click.option(
    "-d",
    "--backup-directory",
    required=True,
    type=click.Path(exists=True, file_okay=False, readable=True),
    help="Directory containing Docker volume backup files"
)
def restore(backup_directory: str):
    try:
        client = get_docker_client()
    except DockerException as exc:
        raise ClickException(str(exc))

    backup_directory = os.path.abspath(backup_directory)

    if not os.path.isdir(backup_directory):
        raise BadParameter(f"Backup directory '{backup_directory}' does not exist")

    backup_files = [f for f in os.listdir(backup_directory) if f.endswith(".tar.gz")]

    if not backup_files:
        raise UsageError(f"No backup files found in directory '{backup_directory}'")

    click.secho(f"Restoring Docker volumes from {backup_directory}", fg="blue")

    with Live(Panel(volumes_progress, border_style="green"), transient=True) as live:
        task = volumes_progress.add_task("Restoring volumes", total=len(backup_files))
        for backup_file in backup_files:
            volume_name = backup_file.rsplit("_", 1)[0]

            existing_volumes = [v.name for v in client.volumes.list()]
            if volume_name not in existing_volumes:
                client.volumes.create(name=volume_name)

            try:
                client.containers.run(
                    image="alpine",
                    command=f"tar xzf /backup/{backup_file} -C /volume",
                    volumes={
                        volume_name: {"bind": "/volume", "mode": "rw"},
                        backup_directory: {"bind": "/backup", "mode": "ro"},
                    },
                    remove=True
                )
                live.console.print(f"[green bold]Restored:[/] {volume_name}")
            except Exception as e:
                live.console.print(f"[red bold]Error:[/]    {volume_name} - {e}", highlight=False)
            finally:
                volumes_progress.update(task, advance=1)

    click.secho("Finished Successfully", fg="green", bold=True)
