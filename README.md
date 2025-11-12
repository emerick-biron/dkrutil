# Dkrutil

Dkrutil is a command-line tool that provides utility functions for managing Docker containers, volumes, images, and
secrets.  
It simplifies common tasks like listing running containers, backing up and restoring volumes, retrieving Docker image
tags from Docker Hub, and securely managing secrets via Docker volumes.

## Installation

You can install dkrutil directly from PyPI:

```bash
pip install dkrutil
```

For isolated environments and ease of management, you can use `pipx`:

```bash
pipx install dkrutil
```

Or install it using [uv](https://github.com/astral-sh/uv) for development:

```bash
uv pip install dkrutil
```

> [!WARNING]
> Some `dkrutil` commands (e.g., **volume backups** and **secrets management**) require **root privileges**.  
> If you installed `dkrutil` in a user-local directory (e.g., `~/.local/bin` via `pip` or `pipx`), make sure the `dkrutil` binary is > accessible to `root`.  
> For this add this alias to your shell configuration (e.g., `~/.bashrc` or `~/.zshrc`):
> ```bash
> alias dkrutil='sudo -E $(echo ~/.local/bin/dkrutil)'
> ```
> This ensures `dkrutil` can be used in scripts or commands requiring `sudo`.

## Usage

Dkrutil provides the `dkrutil` command with various subcommands.

### Containers

#### List running containers

```bash
dkrutil container ps
```

Options:

- `-a, --all` → Show all containers, including stopped ones.

### Volumes

#### Backup Docker volumes

```bash
dkrutil volume backup -d /path/to/backup
```

Options:

- `-d, --backup-directory` → Directory where the volumes will be backed up.
- `-i, --include` → Regex pattern to include specific volumes (can be repeated).
- `-I, --ignore` → Regex pattern to ignore specific volumes (can be repeated).
- `-v, --verbose` → Show skipped volumes in real time.

#### Restore Docker volumes

```bash
dkrutil volume restore -d /path/to/backup
```

Options:

- `-d, --backup-directory` → Directory containing the backup files.

### Images

#### Retrieve all tags of an image

```bash
dkrutil image tags alpine
```

Options:

- `-d, --digest` → Filter tags by a specific SHA256 digest.
- `-t, --tag` → Retrieve the digest of a specific tag.

### Secrets

#### Create a secret stored in a Docker volume

```bash
dkrutil secret create <name> [FILE|-]
```

This command stores a secret securely inside a Docker named volume.

- If `FILE` is omitted or set to `-`, the content is read from standard input.
- A file named `<name>` will be created inside the volume `<name>` with the secret content.
- If the volume already exists, the command will fail (no overwrite).

Examples:

```bash
# From a file
dkrutil secret create db_password ./my-password.txt

# From stdin
echo "supersecret" | dkrutil secret create db_password
```

## Configuration

Dkrutil uses the `docker` Python library to interact with the Docker API. Ensure Docker is installed and running
before using this tool.

## Development

Clone the repository:

```bash
git clone https://github.com/emerick-biron/dkrutil.git
cd dkrutil
```

Install dependencies with uv:

```bash
uv pip install -e .
```

Run the tool locally:

```bash
dkrutil --help
```

Build the package:

```bash
uv build
```

