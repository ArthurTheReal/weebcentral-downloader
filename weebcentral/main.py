"""
main.py - CLI entrypoint for weebcentral manga downloader
"""

import argparse
import json
import os
import sys
from pathlib import Path
import urllib3

from rich.console import Console
from rich.table import Table
from rich import print as rprint

from weebcentral.fetch import Fetcher
from weebcentral.download import Downloader
from weebcentral.database import update_database, search_local
from weebcentral.tools import range_parser, notic, warn, error, success
from weebcentral.constants import DEFAULT_DOWNLOAD_PATH, DEFAULT_DATABASE_PATH

console = Console()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



def build_fetcher(args) -> Fetcher:
    return Fetcher(
        disable_tls=args.no_tls,
        proxy=args.proxy,
    )


def build_downloader(args) -> Downloader:
    return Downloader(
        disable_tls=args.no_tls,
        proxy=args.proxy,
    )


def show_results_table(results: list[dict]) -> None:
    """Render online search results as a numbered Rich table."""
    table = Table(
        title="Search Results",
        show_lines=True,
        highlight=True,
    )
    table.add_column("#",       style="bold cyan",   no_wrap=True, justify="right")
    table.add_column("Title",   style="bold white",  no_wrap=False)
    table.add_column("Author",  style="green")
    table.add_column("Year",    style="yellow",      no_wrap=True)
    table.add_column("Status",  style="magenta",     no_wrap=True)
    table.add_column("Type",    style="blue",        no_wrap=True)
    table.add_column("Tags",    style="dim")

    for idx, item in enumerate(results, start=1):
        tags = ", ".join(item.get("tags", []))
        table.add_row(
            str(idx),
            item.get("name", "N/A"),
            item.get("author", "N/A"),
            item.get("year", "N/A"),
            item.get("status", "N/A"),
            item.get("type", "N/A"),
            tags,
        )

    console.print(table)


def pick_from_results(results: list[dict]) -> dict | None:
    """
    Ask the user to pick one result from the displayed table.
    Returns the chosen result dict, or None if the user aborts.
    """
    while True:
        raw = input(f"Select a title [1-{len(results)}] (or 'q' to quit): ").strip()
        if raw.lower() in ("q", "quit", "exit"):
            return None
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(results):
                return results[idx - 1]
        warn(f"Please enter a number between 1 and {len(results)}.")


def count_downloaded_chapters(manga_name: str) -> int:
    """Return how many chapter folders/files already exist for a given title."""
    base = Path(DEFAULT_DOWNLOAD_PATH).expanduser().resolve() / manga_name
    if not base.exists():
        return 0

    return sum(1 for _ in base.iterdir())


def online_search(fetcher: Fetcher, query: str) -> dict | None:
    """
    Run an online search, display results in a table, and let the user pick.
    Returns the chosen manga info dict, or None.
    """
    notic(f"Searching online for: '{query}' …")
    results = fetcher.search(query)

    if not results:
        error("No results found.")
        return None

    show_results_table(results)
    return pick_from_results(results)


def local_search(query: str) -> dict | None:
    """
    Run a fuzzy search against the local SQLite database.
    Returns a manga info dict (with 'name' and 'id'), or None.
    """
    db_path = Path(DEFAULT_DATABASE_PATH).expanduser().resolve()
    if not db_path.exists():
        error(
            f"Local database not found at: {db_path}\n"
            "  To build it, run the program with the --update-database / -u flag:\n"
            "      python main.py -u"
        )
        sys.exit(1)

    result = search_local(query)


    if result == 0 or not result:
        return None

    return result


def export_to_json(manga_name: str, chapter_data: list[dict]) -> None:
    """
    Write chapter image URLs to a JSON file next to the working directory.
    Each entry contains the chapter name and its list of image URLs.
    """
    output_filename = f"{manga_name}_chapters.json".replace(" ", "_")
    output_path = Path(output_filename).resolve()

    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(chapter_data, fp, indent=2, ensure_ascii=False)

    success(f"Chapter image URLs saved to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="weebcentral",
        description="Scrape and download manga from weebcentral.com",
    )

    parser.add_argument(
        "search_query",
        nargs="?",
        default=None,
        help="Title (or keywords) to search for.",
    )

    parser.add_argument(
        "-l", "--local",
        action="store_true",
        help="Use the local database for fuzzy search instead of querying online.",
    )
    parser.add_argument(
        "-u", "--update-database",
        action="store_true",
        help="Fetch / refresh the local manga database from weebcentral.",
    )

    parser.add_argument(
        "--no-tls",
        action="store_true",
        help="Disable TLS certificate verification.",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        metavar="URL",
        help="Proxy URL to use for all connections (e.g. http://127.0.0.1:8080).",
    )

    parser.add_argument(
        "-r", "--range",
        default=None,
        metavar="RANGE",
        help=(
            "Which chapters to download. Examples: 'all', 'latest', '5', '3:10'. "
            "If omitted you will be prompted."
        ),
    )
    parser.add_argument(
        "--cbz",
        action="store_true",
        help="Pack downloaded images into a .cbz archive per chapter.",
    )
    parser.add_argument(
        "--remove-files",
        action="store_true",
        help="Delete raw image files after packing into .cbz (requires --cbz).",
    )
    parser.add_argument(
        "-j",
        dest="workers",
        type=int,
        default=4,
        metavar="N",
        help="Number of concurrent download threads (default: 4).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Instead of downloading, write chapter image URLs to a JSON file.",
    )

    args = parser.parse_args()

    if args.remove_files and not args.cbz:
        warn("--remove-files has no effect without --cbz; ignoring.")

    if args.update_database:
        notic("Updating local database — this may take a while …")
        fetcher = build_fetcher(args)
        update_database(fetcher)
        success("Local database updated successfully.")
        return

    query = args.search_query
    if not query:
        try:
            query = input("Search query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

    fetcher = build_fetcher(args)

    if args.local:
        manga = local_search(query)
    else:
        manga = online_search(fetcher, query)

    if manga is None:
        notic("No title selected. Exiting.")
        return

    manga_name = manga["name"]
    rprint(f"\n[bold green]Selected:[/bold green] {manga_name}")

    already = count_downloaded_chapters(manga_name)
    if already > 0:
        notic(
            f"{already} chapter(s) of '{manga_name}' are already downloaded "
            f"in {Path(DEFAULT_DOWNLOAD_PATH).expanduser() / manga_name}"
        )
    else:
        notic(f"No chapters of '{manga_name}' found locally yet.")

    notic("Fetching chapter list …")
    chapters = fetcher.query_chapters(manga)

    if not chapters:
        error("No chapters found for this title.")
        return

    notic(f"Found {len(chapters)} chapter(s).")

    range_str = args.range
    if not range_str:
        try:
            range_str = input(
                "Range to download [all / latest / N / N:M] (default: all): "
            ).strip() or "all"
        except (EOFError, KeyboardInterrupt):
            print()
            return

    selected_chapters = range_parser(range_str, chapters)
    notic(f"{len(selected_chapters)} chapter(s) selected for processing.")

    if args.json:
        notic("Fetching image URLs for selected chapters …")
        chapter_data = []
        for chap in selected_chapters:
            images = fetcher.query_chapter_images(chap)
            chapter_data.append({
                "name": chap["name"],
                "id": chap["id"],
                "url": chap["url"],
                "images": images,
            })

        export_to_json(manga_name, chapter_data)
        return

    downloader = build_downloader(args)

    for chap in selected_chapters:
        notic(f"Processing: {chap['name']}")
        images = fetcher.query_chapter_images(chap)

        if not images:
            warn(f"No images found for chapter '{chap['name']}', skipping.")
            continue

        result = downloader.download_chapter(
            manga_name=manga_name,
            chapter_name=chap["name"],
            chapter_images=images,
            workers=args.workers,
            create_cbz=args.cbz,
            remove_files=args.remove_files and args.cbz,
        )

        if result == 3:
            notic(f"'{chap['name']}' already exists as .cbz — skipped.")

    success("All done!")


if __name__ == "__main__":
    main()
