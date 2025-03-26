import rich_click as click

from .container import container
from .image import image
from .secret import secret
from .volume import volume


@click.group(help="Dkrutil – Docker utility CLI")
def dkrutil():
    pass


dkrutil.add_command(volume)
dkrutil.add_command(image)
dkrutil.add_command(container)
dkrutil.add_command(secret)

if __name__ == "__main__":
    dkrutil()
