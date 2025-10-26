import os
import re
from datetime import datetime

import rich_click as click
from click import BadParameter
from click import ClickException, UsageError
from docker.errors import DockerException
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .rich import volumes_progress
from ..core.docker_client import get_docker_client


def get_volumes_sizes(client, volume_names: list[str]) -> dict[str, int]:
    """Get sizes of multiple Docker volumes efficiently using docker system df."""
    try:
        df_data = client.df()
        volumes_data = df_data.get('Volumes', [])

        size_map = {}
        for vol_data in volumes_data:
            vol_name = vol_data.get('Name')
            if vol_name in volume_names:
                usage_data = vol_data.get('UsageData', {})
                size = usage_data.get('Size', 0) if usage_data else 0
                size_map[vol_name] = size if size else 0

        for vol_name in volume_names:
            if vol_name not in size_map:
                size_map[vol_name] = 0

        return size_map
    except Exception:
        return {vol_name: 0 for vol_name in volume_names}


def stream_container_logs(container, volume_name: str, live, task, backup_filepath: str = None):
    """Stream container logs with rolling buffer and optional progress tracking."""
    log_buffer = []
    max_lines = 10
    last_file_size = 0

    processing_text = f"[cyan bold]Processing:[/] {volume_name}"
    live.update(Panel(Group(processing_text, volumes_progress), border_style="green"))
    for log in container.logs(stream=True, follow=True):
        log_line = log.decode('utf-8').strip()
        if log_line:
            log_buffer.append(log_line)
            if len(log_buffer) > max_lines:
                log_buffer.pop(0)

            if backup_filepath and os.path.exists(backup_filepath):
                current_file_size = os.path.getsize(backup_filepath)
                size_diff = current_file_size - last_file_size
                if size_diff > 0:
                    volumes_progress.update(task, advance=size_diff)
                    last_file_size = current_file_size

            log_lines = [processing_text] + [f"[dim]{line}[/dim]" for line in log_buffer]
            log_text = Text.from_markup("\n".join(log_lines))
            live.update(Panel(Group(log_text, volumes_progress), border_style="green"))

    live.update(Panel(volumes_progress, border_style="green"))
    return last_file_size


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
    click.secho("Calculating volumes sizes...", fg="blue")

    volume_sizes = get_volumes_sizes(client, selected_volumes)
    total_size = sum(volume_sizes.values())

    with Live(Panel(volumes_progress, border_style="green"), transient=True) as live:
        task = volumes_progress.add_task(
            "Backing up volumes",
            total=total_size if total_size > 0 else 1,
            current_volume=0,
            total_volumes=len(selected_volumes)
        )

        volume_count = 0
        for volume_name in all_volumes:
            if volume_name not in selected_volumes:
                if verbose:
                    live.console.print(f"[yellow bold]Skipped:[/] {volume_name}")
                continue

            backup_filename = f"{volume_name}_{date_suffix}.tar.gz"
            backup_filepath = os.path.join(backup_directory, backup_filename)
            volume_size = volume_sizes.get(volume_name, 0)
            volume_count += 1
            volumes_progress.update(task, current_volume=volume_count)

            try:
                container = client.containers.run(
                    image="alpine",
                    command=f"tar cvzf /backup/{backup_filename} -C /volume .",
                    volumes={
                        volume_name: {"bind": "/volume", "mode": "ro"},
                        backup_directory: {"bind": "/backup", "mode": "rw"},
                    },
                    detach=True
                )

                last_file_size = stream_container_logs(container, volume_name, live, task, backup_filepath)

                result = container.wait()
                container.remove()

                if volume_size > 0:
                    volumes_progress.update(task, advance=max(0, volume_size - last_file_size))

                if result['StatusCode'] == 0:
                    live.console.print(f"[green bold]Backed up:[/] {volume_name}")
                else:
                    live.console.print(f"[red bold]Error:[/]     {volume_name} - Exit code {result['StatusCode']}",
                                       highlight=False)
            except Exception as e:
                live.console.print(f"[red bold]Error:[/]     {volume_name} - {e}", highlight=False)
                if volume_size > 0:
                    volumes_progress.update(task, advance=volume_size)

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

    total_size = sum(os.path.getsize(os.path.join(backup_directory, f)) for f in backup_files)

    with Live(Panel(volumes_progress, border_style="green"), transient=True) as live:
        task = volumes_progress.add_task(
            "Restoring volumes",
            total=total_size if total_size > 0 else 1,
            current_volume=0,
            total_volumes=len(backup_files)
        )

        volume_count = 0
        for backup_file in backup_files:
            volume_name = backup_file.rsplit("_", 1)[0]
            backup_filepath = os.path.join(backup_directory, backup_file)
            file_size = os.path.getsize(backup_filepath)
            volume_count += 1
            volumes_progress.update(task, current_volume=volume_count)

            existing_volumes = [v.name for v in client.volumes.list()]
            if volume_name not in existing_volumes:
                client.volumes.create(name=volume_name)

            try:
                container = client.containers.run(
                    image="alpine",
                    command=f"tar xvzf /backup/{backup_file} -C /volume",
                    volumes={
                        volume_name: {"bind": "/volume", "mode": "rw"},
                        backup_directory: {"bind": "/backup", "mode": "ro"},
                    },
                    detach=True
                )

                stream_container_logs(container, volume_name, live, task)

                result = container.wait()
                container.remove()

                volumes_progress.update(task, advance=file_size)

                if result['StatusCode'] == 0:
                    live.console.print(f"[green bold]Restored:[/] {volume_name}")
                else:
                    live.console.print(f"[red bold]Error:[/]    {volume_name} - Exit code {result['StatusCode']}",
                                       highlight=False)
            except Exception as e:
                live.console.print(f"[red bold]Error:[/]    {volume_name} - {e}", highlight=False)
                volumes_progress.update(task, advance=file_size)

    click.secho("Finished Successfully", fg="green", bold=True)
