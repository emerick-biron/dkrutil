import sys

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.style import Style

bar_back_style = Style(color="red")
bar_style = Style(color="cyan")

is_utf8 = sys.stdout.encoding == "utf-8"
SEPARATOR = "[bold]•" if is_utf8 else "[bold]+"
ELLIPSIS = "…" if is_utf8 else "..."
PROGRESS_PERCENT = "[bold blue]{task.percentage:>3.1f}%"
COMPLETED_TOTAL = "{task.completed}/{task.total}"

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
    COMPLETED_TOTAL,
)
