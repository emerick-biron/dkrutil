import requests
import rich_click as click
from click import ClickException, UsageError
from rich.live import Live
from rich.panel import Panel

from .rich import find_tags_progress


@click.group(help="Manage Docker images")
def image():
    pass


@image.command(help="Retrieve all tags of a Docker Hub image, optionally filtering by digest or tag")
@click.argument("image", required=True)
@click.option("-d", "--digest", required=False, help="Filter tags by specific SHA256 digest")
@click.option("-t", "--tag", required=False, help="Filter by specific tag")
def tags(image: str, digest: str, tag: str):
    if digest and tag:
        raise UsageError("Options --digest (-d) and --tag (-t) are mutually exclusive")

    if digest and digest.startswith("sha256:"):
        digest = digest.split(":", 1)[1]

    base_url = "https://hub.docker.com"
    parts = image.split("/")
    base_path = f"/v2/repositories/library/{image}/tags" if len(
        parts) == 1 else f"/v2/namespaces/{parts[0]}/repositories/{'/'.join(parts[1:])}/tags"
    url = f"{base_url}{base_path}"

    if tag:
        resp = requests.get(f"{url}/{tag}")
        if resp.status_code != requests.codes.ok:
            raise ClickException(f"Error getting image {image}: {resp.status_code} {resp.text}")

        data = resp.json()
        digest = data["digest"]

    with Live(Panel(find_tags_progress, border_style="green"), transient=True) as live:
        find_tags_progress.add_task("Looking for tags matching your search", total=None)

        while url:
            resp = requests.get(url, params={"page": 1, "page_size": 100})
            if resp.status_code != requests.codes.ok:
                raise ClickException(f"Error getting image {image}: {resp.status_code} {resp.text}")

            data = resp.json()
            filtered_tags = [f"[green bold]Found:[/] {t["name"]}" for t in data.get("results", [])
                             if not digest or digest in t.get("digest", "")]
            if filtered_tags:
                live.console.print("\n".join(filtered_tags), highlight=False)

            url = data.get("next")
