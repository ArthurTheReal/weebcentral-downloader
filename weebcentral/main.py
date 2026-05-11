from weebcentral import tools, fetch, download, database
from weebcentral.constants import *
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    fetcher = fetch.Fetcher(True, "socks5h://172.18.192.1:1080")
    # results = fetcher.search("attack on titan")
    # chapter_list = fetcher.query_chapters(results[0])
    # chapter_urls = fetcher.query_chapter_images(chapter_list[0])
    
    # downloader = download.Downloader(True, "socks5h://172.18.192.1:1080")
    # downloader.download_chapter(results[0]["name"], chapter_list[0]["name"], chapter_urls, workers=5, create_cbz=True, remove_files=False)

    database.update_database(fetcher)
    database.search_local()

    return 0

if __name__ == "__main__":
    exit(main())