import os
from typing import List, Optional
from urllib.parse import unquote

from aiohttp.client_exceptions import ClientResponseError
from bs4 import BeautifulSoup

from nazurin.models import Caption, Illust, Image
from nazurin.utils import Request
from nazurin.utils.exceptions import NazurinError


class Fuliba(object):
    def site(self, site_url: Optional[str] = "fuliba2021.net"):
        self.url = site_url
        return self

    async def getPost(self, post_id: int, page_num: int):
        url = "https://" + self.url + "/" + str(post_id) + ".html/" + str(page_num)
        async with Request() as request:
            async with request.get(url) as response:
                try:
                    response.raise_for_status()
                except ClientResponseError as err:
                    raise NazurinError(err) from None
                response = await response.text()
        soup = BeautifulSoup(response, "html.parser")
        title_tag = soup.head.title
        img_tags = soup.find("article", class_="article-content").find_all("img")
        tag_tags = soup.find(class_="article-tags").find_all("a")
        info = {
            "post_id": post_id,
            "page_num": page_num,
            "url": url,
            "title": title_tag.string,
            "tags": [t.string for t in tag_tags],
        }
        return info, img_tags

    async def view(self, post_id: int, page_num: int) -> Illust:
        info, img_tags = await self.getPost(post_id, page_num)
        imgs = self.getImages(post_id, img_tags)
        caption = self.buildCaption(info)
        return Illust(imgs, caption, info)

    def getImages(self, post_id, img_tags) -> List[Image]:
        imgs = []
        for i in range(len(img_tags)):
            img = img_tags[i]
            file_url = img["src"]
            name = unquote(os.path.basename(file_url))
            width = img.get("data-width")
            height = img.get("data-width")
            if width and height:
                imgs.append(
                    Image(
                        f"Fuliba - {post_id} - {name}",
                        file_url,
                        width=width,
                        height=height,
                    )
                )
        return imgs

    def buildCaption(self, info) -> Caption:
        """Build media caption."""
        tags = "#" + " #".join(info["tags"])
        caption = Caption(
            {
                "title": info["title"],
                "url": info["url"],
                "tags": tags,
            }
        )
        return caption
