# weebcentral-downloader

A command-line tool for searching and downloading manga from [weebcentral.com](https://weebcentral.com). Supports batch downloads, CBZ packing, proxy usage, and a local database for offline search.

> **License:** GNU General Public License v3.0

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Option 1 — Clone and install with pip](#option-1--clone-and-install-with-pip)
  - [Option 2 — Download and install the wheel](#option-2--download-and-install-the-wheel)
- [Usage](#usage)
  - [Basic search and download](#basic-search-and-download)
  - [Local database](#local-database)
  - [Selecting chapters](#selecting-chapters)
  - [CBZ archives](#cbz-archives)
  - [Exporting image URLs to JSON](#exporting-image-urls-to-json)
  - [Proxy and TLS](#proxy-and-tls)
  - [All flags](#all-flags)
- [Examples](#examples)

---

## Features

- Search manga online or locally via a cached SQLite database
- Interactive fuzzy search (local mode) powered by `fzf`
- Rich formatted search-result tables (online mode)
- Batch chapter downloads with configurable concurrency
- Optional CBZ archive creation per chapter
- Export chapter image URLs to JSON instead of downloading
- Proxy support (HTTP/HTTPS/SOCKS with `requests[socks]`)
- TLS verification toggle for restrictive network environments

---

## Requirements

- Python **3.8** or newer
- [`fzf`](https://github.com/junegunn/fzf) installed and available on your `PATH` (required for local database search)

---

## Installation

### Option 1 — Clone and install with pip

This is the recommended approach if you want to track the latest commits or contribute.

```bash
git clone https://git.theazizi.ir/Arthur/weebcentral-downloader.git
cd weebcentral-downloader
pip install .
```

To install in editable/development mode (changes to the source take effect immediately):

```bash
pip install -e .
```

### Option 2 — Download and install the wheel

If a pre-built wheel is available from the repository's releases page, you can install it directly without cloning:

```bash
pip install weebcentral_downloader-0.0.1-py3-none-any.whl
```

---

After either installation method the `weebcentral-dl` command will be available in your shell:

```bash
weebcentral-dl --help
```

---

## Usage

### Basic search and download

Running the command with a search query performs an **online search** and displays the results in a table. You then pick a title by number and choose which chapters to download.

```bash
weebcentral-dl "one piece"
```

If you omit the query you will be prompted for it interactively:

```bash
weebcentral-dl
# Search query: _
```

### Local database

The local database is a SQLite file that mirrors the weebcentral catalogue. It enables instant offline fuzzy search via `fzf` and is useful if you search frequently.

**Build or refresh the database** (this fetches every title from the site and may take several minutes):

```bash
weebcentral-dl --update-database
```

**Search using the local database:**

```bash
weebcentral-dl --local "berserk"
# or
weebcentral-dl -l "berserk"
```

An `fzf` picker will open pre-filtered with your query. If the database file does not exist yet, the tool will tell you exactly what command to run to create it.

### Selecting chapters

The `--range` / `-r` flag controls which chapters are downloaded. The following values are accepted:

| Value | Meaning |
|---|---|
| `all`, `a`, `t`, `total` | Every chapter |
| `l`, `latest`, `last`, `new` | The most recently released chapter only |
| `N` | The single chapter at position N (1-indexed) |
| `N:M` | Chapters from position N up to and including M |

If `--range` is not provided you will be prompted after selecting a title.

```bash
weebcentral-dl "chainsaw man" --range latest
weebcentral-dl "chainsaw man" -r 1:10
weebcentral-dl "chainsaw man" -r 42
```

### CBZ archives

Use `--cbz` to pack each downloaded chapter into a `.cbz` file (a ZIP archive readable by most comic readers such as Komga, Kavita, or CDisplayEx).

```bash
weebcentral-dl "vinland saga" --range all --cbz
```

Add `--remove-files` to delete the raw image files after packing, keeping only the `.cbz`:

```bash
weebcentral-dl "vinland saga" --range all --cbz --remove-files
```

`--remove-files` has no effect when used without `--cbz`.

### Exporting image URLs to JSON

If you want the direct image URLs without downloading anything (e.g. to feed into another tool), use `--json`. A file named `<Title>_chapters.json` will be written to the current directory.

```bash
weebcentral-dl "blue lock" --range 1:5 --json
```

The output format is:

```json
[
  {
    "name": "Chapter 1",
    "id": "...",
    "url": "https://weebcentral.com/chapters/...",
    "images": [
      "https://cdn.example.com/page1.jpg",
      "https://cdn.example.com/page2.jpg"
    ]
  }
]
```

### Proxy and TLS

Pass a proxy URL with `--proxy`. HTTP, HTTPS, and SOCKS5 proxies are supported (SOCKS requires the `requests[socks]` extra, which is installed by default):

```bash
weebcentral-dl "naruto" --proxy http://127.0.0.1:8080
weebcentral-dl "naruto" --proxy socks5://127.0.0.1:1080
```

Disable TLS certificate verification with `--no-tls` (useful behind corporate firewalls or intercepting proxies):

```bash
weebcentral-dl "naruto" --no-tls
```

### All flags

```
usage: weebcentral-dl [-h] [-l] [-u] [--no-tls] [--proxy URL]
                      [-r RANGE] [--cbz] [--remove-files] [-j N] [--json]
                      [search_query]

positional arguments:
  search_query          Title or keywords to search for.

options:
  -h, --help            Show this help message and exit.

search:
  -l, --local           Use the local database for fuzzy search.
  -u, --update-database
                        Fetch / refresh the local manga database.

network:
  --no-tls              Disable TLS certificate verification.
  --proxy URL           Proxy URL (e.g. http://127.0.0.1:8080).

download:
  -r RANGE, --range RANGE
                        Chapters to download: all / latest / N / N:M
  --cbz                 Pack images into a .cbz archive per chapter.
  --remove-files        Delete raw images after packing (requires --cbz).
  -j N                  Number of concurrent download threads (default: 4).
  --json                Write chapter image URLs to a JSON file instead of downloading.
```

---

## Examples

```bash
# Interactive: prompts for query, then for range
weebcentral-dl

# Download all chapters of a title as CBZ archives, 8 threads
weebcentral-dl "demon slayer" --range all --cbz -j 8

# Download only the latest chapter
weebcentral-dl "one punch man" -r latest

# Download chapters 20 through 50 and keep only the CBZ files
weebcentral-dl "jujutsu kaisen" -r 20:50 --cbz --remove-files

# Offline fuzzy search, then download chapters 1–5
weebcentral-dl --local -r 1:5

# Refresh the local database, then search it
weebcentral-dl --update-database
weebcentral-dl --local "berserk"

# Export image URLs for the first 3 chapters to JSON
weebcentral-dl "solo leveling" -r 1:3 --json

# Use a SOCKS5 proxy with TLS disabled
weebcentral-dl "attack on titan" --proxy socks5://127.0.0.1:1080 --no-tls
```