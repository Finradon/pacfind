# pacfind

`pacfind` shows how packages are installed on your system (`pacman`, `paru`, `flatpak`, `pip`, `npm`, or `cargo`).

The codebase is structured so additional OS-specific backends can be added without changing the CLI entrypoint.

## Usage

```bash
./pacfind [name] [-m MANAGER] [-s SOURCE]
```

At least one of `name`, `-m/--manager`, or `-s/--source` is required.

## Examples

Find packages matching a name:

```bash
./pacfind firefox
```

List all packages installed with one manager:

```bash
./pacfind --manager pacman
./pacfind -m paru
./pacfind -m flatpak
./pacfind -m pip
./pacfind -m npm
./pacfind -m cargo
```

List all packages from one source:

```bash
./pacfind --source flathub
./pacfind -s extra
```

Combine filters:

```bash
./pacfind --manager flatpak --source flathub
./pacfind firefox --manager pacman
```

## Tests

Run the hermetic test suite with:

```bash
pytest
```

The tests stub command execution and do not depend on the package managers installed on the machine running them.
