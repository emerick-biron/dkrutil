import sys

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, ProgressColumn
from rich.style import Style
from rich.text import Text as RichText


def format_size(size: float) -> str:
    """Format size in bytes to human-readable format."""
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size_float = float(size)

    while size_float >= 1024 and unit_index < len(units) - 1:
        size_float /= 1024
        unit_index += 1

    if size_float < 10:
        return f"{size_float:.1f}{units[unit_index]}"
    else:
        return f"{size_float:.0f}{units[unit_index]}"


class VolumeCountColumn(ProgressColumn):
    """Renders volume count."""

    def render(self, task):
        """Render volume count."""
        current = task.fields.get("current_volume", 0)
        total = task.fields.get("total_volumes", 0)
        return RichText(f"{current}/{total}", style="bold")


class FileSizeColumn(ProgressColumn):
    """Renders completed/total file sizes."""

    def render(self, task):
        """Render file sizes."""
        completed = format_size(task.completed)
        total = format_size(task.total)
        return RichText(f"{completed}/{total}", style="bold")


bar_back_style = Style(color="red")
bar_style = Style(color="cyan")

is_utf8 = sys.stdout.encoding == "utf-8"
SEPARATOR = "[bold]•" if is_utf8 else "[bold]+"
ELLIPSIS = "…" if is_utf8 else "..."
PROGRESS_PERCENT = "[bold blue]{task.percentage:>3.1f}%"

BAR_MAX = BarColumn(
    bar_width=None,
    style=bar_back_style,
    complete_style=bar_style,
    finished_style=bar_style,
)

find_tags_progress = Progress(
    SpinnerColumn(style="white bold"),
    TextColumn(f"[bold blue]{{task.description}} {ELLIPSIS}", justify="right"),
)

volumes_progress = Progress(
    SpinnerColumn(style="white bold"),
    TextColumn(f"[bold blue]{{task.description}} {ELLIPSIS}", justify="right"),
    BAR_MAX,
    PROGRESS_PERCENT,
    SEPARATOR,
    VolumeCountColumn(),
    SEPARATOR,
    FileSizeColumn(),
)
