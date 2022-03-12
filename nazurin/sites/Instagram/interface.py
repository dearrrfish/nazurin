from time import time

from nazurin.database import Database
from nazurin.models import Illust

from .api import Instagram
from .config import COLLECTION

patterns = [
    # https://www.instagram.com/p/CXoHOpuuFq0/
    r'((?:www\.)?instagram\.com)/p/([\w-]+)',

    # https://bibliogram.pussthecat.org/p/CPMtbzij2wS
    r'((?:[^/]+\.)?bibliogram\.[^/]+)/p/([\w-]+)'

]

async def handle(match, **kwargs) -> Illust:
    site_url = match.group(1)
    status_id = match.group(2)
    db = Database().driver()
    collection = db.collection(COLLECTION)
    illust = await Instagram().fetch(site_url, status_id)
    illust.metadata['collected_at'] = time()
    await collection.insert(status_id, illust.metadata)
    return illust
