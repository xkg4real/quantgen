"""Transport for opt-in, single-request news connectivity checks."""


def get_once(url, **kwargs):
    # A fresh requests session has no retries. Exclude redirects as well.
    import requests
    return requests.get(url, allow_redirects=False, **kwargs)
