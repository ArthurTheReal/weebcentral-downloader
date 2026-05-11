from weebcentral.fetch import Fetcher
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import os
import sqlite3
from pyfzf import FzfPrompt
from weebcentral.tools import *


def dump_database_from_servers(fetcher: Fetcher):
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False
    ) as prog:
        task = prog.add_task("[blue bold] fetching database:", total=None)
        
        counter = 0
        while True:
            search_result = fetcher.search("", offset=counter)
            if search_result == []:
                notic("database is dumped")
                break

            results.extend(search_result)
            
            prog.update(task, refresh=True, description=f"[blue bold] fetching database: {len(results)} items have been recived")
            counter += 32

    return results

def update_database(fetcher):
    if Path("data.db").exists():
        os.remove("data.db")
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE manga(name, url, image, year, status, type, author, id, tags)")
    data = dump_database_from_servers(fetcher)
    for item in data:
        cur.execute("INSERT INTO manga VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            item["name"],
            item["url"],
            item["image"],
            item["year"],
            item["status"],
            item["type"],
            item["author"],
            item["id"],
            ",".join(item["tags"])
        ))

    con.commit()
    con.close()

def fetch_local_database(fields: list[str]):
    for i in fields:
        if not i in ["name", "url", "image", "year", "status", "type", "author", "id", "tags"]:
            error(f"{i} is not a valid field of data")
            exit(1)

    if not Path("data.db").exists():
        error("data.db not found, please dump a database from online source first")
        exit(1)

    con = sqlite3.connect("data.db")
    cur = con.cursor()
    result = cur.execute(f"SELECT {','.join(fields)} from manga")
    return list(result)


def search_local(prompt=""):
    names = []
    names_ids = {}

    for i in fetch_local_database(["name", "id"]):
        names.append(i[0])
        names_ids[i[0]] = i[1]

    fzf = FzfPrompt()
    result = fzf.prompt(names, f"--query '{prompt}' --layout=reverse")
    return {
        "name": result[0],
        "id": names_ids[result[0]]
    }