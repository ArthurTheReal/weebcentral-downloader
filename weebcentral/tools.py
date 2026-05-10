"""
tools.py - helper functions
"""

from rich import print as rprint
from requests import Session
from random import choice
from weebcentral.constants import USER_AGENTS
import os
import pathlib
import zipfile


### Loging

def notic(msg):
    rprint(f"[italic blue] [NOTIC] {msg}")


def warn(msg):
    rprint(f"[bold yellow] [WARNING]: {msg}")


def error(msg):
    rprint(f"[bold red] [ERROR]: {msg}")


def success(msg):
    rprint(f"[italic green] [SUCCESS] {msg}")


def safe_get_request(session: Session, url: str, params: dict = {}, retries: int = 10):
    """
        takes a requests.session and does the get requsts, handles errors and retries if one occures.
        it assumes that headers and other settings are already added to the seassion object
    """

    retries_count = 0
    successful_resposne = False
    while retries_count < retries:
        try:
            response = session.get(url, params=params)
            
            if response.status_code != 200:
                error(f" [try {retries_count + 1}/{retries_count}] resposne code error: {response.status_code}")
                retries_count += 1
                continue
            
            successful_resposne = True
            break
        
        except Exception as e:
            error(f" [try {retries_count + 1}/{retries_count}] error: {e}")
            retries_count += 1
            continue

    if not successful_resposne:
        error(f" could not make the requests after {retries} retries, terminating...")
        exit(1)
    
    return response


def range_parser(r: str, chapter_list: list[dict]):
    """
    parses the 'range' argument, which is used to specify which chapters should be downloaded
        all, a, t, total or empty input --> download all chapters
        l, latest, last, new --> download the last chapter
        n:m --> download chapters from index n to m
        NUM --> download the chapter with index number of NUM
    """
    
    if r.lower() in ["all", "a", "t", "total", None]:
        return chapter_list

    if r.lower() in ["l", "latest", "last", "new"]:
        return [chapter_list[-1]]

    if ":" in r:
        a, b = r.split(":")
        if int(a) > len(chapter_list) or int(a) <= 0:
            error(
                f"{a} was specified for lower boundary of download range while the chapters start with {chapter_list[0]["name"]}")
            exit(1)

        if int(b) > len(chapter_list) or int(b) <= 0:
            error(f"{b} was specified for upper bboundary of download range while there is only {len(chapter_list)} chapters avalable")
            exit(1)

        return chapter_list[int(a) - 1: int(b)]

    if r.isdigit():
        if int(r) > len(chapter_list) or int(r) <= 0:
            error(
                f"{r} is out of range, there are only {len(chapter_list)} chapters avalible")
            exit(1)

        return [chapter_list[int(r)-1]]
    else:
        error(f"invalid range {r}")
        exit(1)

def random_headers():
    return {
        'User-Agent': choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Sec-GPC': '1',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }

def make_cbz(files: list[str], output: str, del_files=False, input_dir=".") -> int:
    with zipfile.ZipFile(output, "w") as file:
        for f in files:
            filepath = os.path.join(input_dir, f)
            if not pathlib.Path(filepath).exists():
                error(f"file not found: {f}\n      could not make the cbz file {output}")
                exit(1)

            file.write(filepath, arcname=f)
            if del_files:
                os.remove(filepath)

    return 0


def chmkdir(p: str) -> int:
    pth = pathlib.Path(p)
    if not pth.exists():
        os.mkdir(str(pth))
        os.chdir(str(pth))
        return 0
    else:
        if pth.is_file():
            error(f"{p} is not a directory")
            exit(1)
                  
        os.chdir(str(pth))
        return 0