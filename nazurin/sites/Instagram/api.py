import os, re
from typing import List, Tuple

from nazurin.models import Caption, Illust, Image
from nazurin.utils import Request, logger
from nazurin.utils.exceptions import NazurinError


class Instagram(object):
    async def fetch(self, site_url: str, status_id: str) -> Illust:
        """Fetch & return instagram images and information."""
        bib_url, html = await self.getHtml(site_url, status_id)
        imgs, meta_images = self.getImages(bib_url, status_id, html)
        caption, meta = self.buildCaption(bib_url, status_id, html)
        meta["images"] = meta_images
        return Illust(imgs, caption, meta)

    async def getInstances(self):
        api = "https://bibliogram.art/api/instances"
        async with Request() as request:
            async with request.get(api) as response:
                if response.status != 200:
                    raise NazurinError("No available Bibliogram instance found")
                instances = await response.json()
                return instances["data"]

    async def getHtml(self, site_url: str, status_id: str):
        """Get a post from page."""
        bib_urls = []
        if "bibliogram" in site_url:
            bib_urls.append("https://" + site_url)
        else:
            bib_instances = await self.getInstances()
            for bib in bib_instances:
                bib_urls.append(bib["address"])

        # Loop proxies for fetching post content
        postHtml = ""
        for bib_url in bib_urls:
            api = bib_url + "/p/" + status_id
            try:
                logger.info(f"requesting proxy site: {api}")
                async with Request() as request:
                    async with request.get(api) as response:
                        if response.status == 200:
                            postHtml = await response.text()
                            return bib_url, postHtml
                        else:
                            continue
            except:
                continue

        if postHtml == "":
            raise NazurinError("Unable to fetch post content via bibliogram proxy")

    def getImages(self, bib_url: str, status_id: str, html: str) -> List[dict]:
        """
        Extract post data from html as example below:

        <img class="sized-image" src="..." width="1000" height="1000">
        """
        images = []
        regex = r'<img class="sized-image"([\s\S]*?)>'
        src_regex = r'src="([\s\S]+?)"'
        width_regex = r'width="(\d+?)"'
        height_regex = r'height="(\d+?)"'
        matches = re.findall(regex, html, re.MULTILINE)
        if not matches:
            raise NazurinError("No post image found")

        for str in matches:
            src_match = re.search(src_regex, str)
            src = bib_url + src_match.group(1)
            width_match = re.search(width_regex, str)
            width = int(width_match.group(1))
            height_match = re.search(height_regex, str)
            height = int(height_match.group(1))
            images.append({"src": src, "width": width, "height": height})

        if not len(images):
            raise NazurinError("No successful processed image")

        imgs = [
            Image(
                # Instagram convert all uploaded photos to jpeg, so use .jpg ext should be safe
                f"Instagram - {status_id} - {i}.jpg",
                images[i]["src"],
                images[i]["src"],
                width=images[i]["width"],
                height=images[i]["height"],
            )
            for i in range(len(images))
        ]

        return imgs, images

    def buildCaption(self, bib_url: str, status_id: str, html: str) -> dict:
        """
        Extract and build message caption from html as example below:

        <p class="structured-text description">....</p>
        """

        author_regex = r'<a class="name" [\s\S]*?>([\s\S]+?)</a>'
        author_match = re.search(author_regex, html)
        author = author_match.group(1)
        author = author.replace('@', '')

        desc_regex = r'<p class="structured-text description">([\s\S]*?)</p>'
        desc_match = re.search(desc_regex, html, re.MULTILINE)
        desc = desc_match.group(1)
        desc = re.sub(r"<a [\s\S]*?>", "", desc)
        desc = desc.replace("</a>", "").strip()

        meta = {
            "user": author,
            "desc": desc,
            "instagram_url": f"https://www.instagram.com/p/{status_id}",
            "bibliogram_url": f"{bib_url}/p/{status_id}",
        }

        return Caption(meta), meta
