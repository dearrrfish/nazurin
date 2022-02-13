from time import time

from nazurin.database import Database
from nazurin.models import Illust

from .api import Fuliba
from .config import COLLECTIONS

patterns = [
    # https://fuliba2021.net/2022017.html/2
    r"(fuliba2021\.net)/(\d+)\.html(/\d)?"
]


async def handle(match, **kwargs) -> Illust:
    site_url = match.group(1)
    post_id = match.group(2)
    page_num_match = match.group(3)
    if page_num_match:
        page_num = int(page_num_match[1:])
    else:
        page_num = 1

    db = Database().driver()
    collection = db.collection(COLLECTIONS)
    api = Fuliba().site(site_url)

    illust = await api.view(post_id, page_num)
    illust.metadata["collected_at"] = time()
    await collection.insert(int(f"{post_id}{page_num}"), illust.metadata)
    return illust
