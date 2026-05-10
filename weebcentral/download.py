"""
donwload.py - handles the downloads
"""

import requests
from weebcentral.tools import *
import os
from urllib import parse
from pathlib import Path
from concurrent import futures
from rich.progress import Progress


class Downloader:
    def __init__(self, disable_tls = False, proxy = None):
        self.session = requests.Session()
        self.session.headers = random_headers()

        if disable_tls:
            self.session.verify = False

        if not proxy == None:
            self.session.proxies = {
                "http": proxy,
                "https": proxy
            }
    
    def download(self, url, skip_if_exists = True, outdir="./"):
        res = safe_get_request(self.session, url)

        filename = os.path.join(outdir, os.path.basename(parse.urlparse(url).path))
        if os.path.exists(filename) and skip_if_exists:
            return 0
        
        with open(filename, "wb") as file:
            for chunk in res.iter_content(10*1024):
                file.write(chunk)

        return 0

    def download_chapter(self, manga_name: str, chapter_name: str, chapter_images: list[str], workers=4, create_cbz=False, remove_files=False) -> int:
        output_cbz = Path(manga_name + "/" + chapter_name + ".cbz")
        if output_cbz.exists():
            return 3
                
        download_path = str(Path(manga_name + "/" + chapter_name))
        os.makedirs(download_path, exist_ok=True)

        with Progress() as prog:
            task = prog.add_task(
                f"[blue bold] Downloading {chapter_name}", total=len(chapter_images))
            with futures.ThreadPoolExecutor(max_workers=10) as executor:
                threads = []
                threads_urls = {}
                for url in chapter_images:
                    threads.append(
                        executor.submit(self.download, url, True, download_path)
                    )
                    threads_urls[executor.submit(self.download, url, True, download_path)] = url

                for thread in futures.as_completed(threads):
                    if thread.result() != 0:
                        threads.append(
                            executor.submit(self.download, threads_urls[thread], True, download_path)
                        )
                        warn(
                            f"connection error with code {thread.result()} while downloading images of chapter, retrying...")

                    prog.update(task, refresh=True, advance=1)

        if create_cbz:
            file_names = [
                os.path.basename(parse.urlparse(url).path) for url in chapter_images
            ]
            make_cbz(file_names, str(output_cbz), remove_files, input_dir=download_path)
            
        os.chdir("../..")