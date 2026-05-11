"""
fetch.py - handles reciving information from weebcentral, stuff like searching
"""

from weebcentral.tools import *
from weebcentral.constants import *
from bs4 import BeautifulSoup
import requests


class Fetcher:
    def __init__(self, disable_tls=False, proxy=None):
        self.session = requests.Session()
        self.session.headers = random_headers()

        if disable_tls:
            self.session.verify = False

        if not proxy == None:
            self.session.proxies = {
                "http": proxy,
                "https": proxy
            }
        
    def search(self, query: str, offset=0) -> list[dict]:
        """
        output scheme:
            list( --> list of all results
                {
                    "name" -> title of the result
                    "url" -> link to results page
                    "image" -> thumbnile
                    "year" -> release year 
                    "status" -> publication status
                    "type" -> type (e.g. manga, manhwa etc.)
                    "author" -> author of the result
                    "tags" -> tags, list of strings
                    "id" -> id of said result, used in "url" as well
                },
                ...
            )
        """
        params = {
            'author': '',
            'text': query,
            'sort': 'Best Match',
            'order': 'Ascending',
            'official': 'Any',
            'display_mode': 'Full Display',
            'offset': offset
        }
        
        page = safe_get_request(self.session, f'{WEBSITE}/search/data', params=params)
        soup = BeautifulSoup(page.text, "html.parser")

        results = []

        for article in soup.find_all("article", {"class": "bg-base-300"}):
            sections = article.find_all("section")

            link = sections[0].find("a").get("href")
            name = sections[1].find("div").find("a").string
            image_url = sections[0].find("a").find(
                "article").find("picture").find("img").get("src")
            manga_id = link.split("/")[4]
            year = sections[1].find_all("div")[1].find("span").string
            status = sections[1].find_all("div")[2].find("span").string
            type_ = sections[1].find_all("div")[3].find("span").string
            author = sections[1].find_all("div")[4].find("span").string
            tags = []
            for tag in sections[1].find_all("div")[5].find_all("span"):
                tags.append(tag.string.replace(",", ""))

            results.append({
                "name": name,
                "url": link,
                "image": image_url,
                "year": year,
                "status": status,
                "type": type_,
                "author": author,
                "tags": tags,
                "id": manga_id,
            })

        return results
    
    def query_chapters(self, manga_info: dict) -> list[dict]:
        """
        input: manga information recived from search() function
        output scheme:
            list( --> list of all chapters the specific manga
                {
                    name: chapters name, used when saving the chapter to a .cbz file
                    url: url to the read-online page of the chapter
                    id: chapters id used in other functions
                },
                .
                ..
                ...
            )

        """

        chap_list = safe_get_request(self.session, f"{WEBSITE}/series/{manga_info['id']}/full-chapter-list")
        chap_list_soup = BeautifulSoup(chap_list.text, "html.parser")

        reuslts = []
        for div in chap_list_soup.find_all("div", {"class": "flex items-center"}):
            link = div.find("a").get("href")
            name = div.find("a").find_all("span")[1].find("span").string
            reuslts.append({
                "name": name,
                "url": link,
                "id": link.split("/")[-1]
            })

        reuslts.reverse()
        
        return reuslts
    

    def query_chapter_images(self, chapter_info: dict) -> list[str]:
        """
        input scheme: chapter recived from query_chapters() function
        output scheme:
            list( --> list of url's for each page of the chapter, the name of image files are in order by default
            )
        """

        chap_images = safe_get_request(self.session, f"{WEBSITE}/chapters/{chapter_info['id']}/images?is_prev=False&current_page=1&reading_style=long_strip")
        chap_images_soup = BeautifulSoup(chap_images.text, "html.parser")

        image_urls = []
        for img in chap_images_soup.find("section").find_all("img"):
            image_urls.append(img.get("src"))
        
        return image_urls
