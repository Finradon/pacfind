# pacfind

`pacfind` shows how packages are installed on your system (`pacman`, `paru`, or `flatpak`).

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
