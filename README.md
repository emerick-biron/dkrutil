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

Or install it using [Poetry](https://python-poetry.org/) for development:

```bash
poetry install
```

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

Install dependencies:

```bash
poetry install
```

Run the tool locally:

```bash
poetry run dkrutil --help
```

