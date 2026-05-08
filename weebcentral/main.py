from weebcentral import tools, fetch
from weebcentral.constants import *
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    fetcher = fetch.Fetcher(True, "socks5h://172.18.192.1:1080")
    results = fetcher.search("attack on titan")
    chapter_list = fetcher.query_chapters(results[0])
    chapter_urls = fetcher.query_chapter_images(chapter_list[0])
    
    tools.rprint(chapter_urls)

    return 0

if __name__ == "__main__":
    exit(main())