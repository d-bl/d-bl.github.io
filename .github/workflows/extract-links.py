# used in workflow after download of github-pages artifact
import os
import sys
from html.parser import HTMLParser
import requests
from bs4 import BeautifulSoup

if len(sys.argv) < 2:
    print("Usage: python urls.py <repo>")
    sys.exit(1)

repo = sys.argv[1]


class URLExtractor(HTMLParser):
    def __init__(self, file_path):
        super().__init__()
        self.anchor_urls = dict()
        self.file_path = file_path
        self.attrs = {'href', 'src', 'data-src', 'data-href', 'action', 'poster'}

    def handle_starttag(self, tag, attrs):
        for attr, value in attrs:
            if attr.lower() in self.attrs and value and not value.startswith('javascript'):
                found_url = value.split('?')[0].split("#")[0].split("'")[0].rstrip('/')
                if found_url.endswith('/.'):
                    found_url = found_url[:-2]
                if found_url.startswith('/'):
                    found_url = 'https://d-bl.github.io' + found_url
                elif not (found_url.startswith('http://') or found_url.startswith('https://')):
                    found_url = f'https://d-bl.github.io/{repo}/' + os.path.normpath(os.path.join(self.file_path, found_url))
                if found_url not in self.anchor_urls:
                    self.anchor_urls[found_url] = set()
                if attr.lower() == 'href' and '#' in value:
                    self.anchor_urls[found_url].add(value.split('#')[1])


anchor_urls = dict()
for root, _, files in os.walk('.'):
    for file in files:
        if file.endswith('.html'):
            file_path = os.path.relpath(os.path.dirname(os.path.join(root, file)), '.')
            with open(os.path.join(root, file), encoding='utf-8') as f:
                parser = URLExtractor(file_path)
                parser.feed(f.read())
                anchor_urls.update(parser.anchor_urls)

with open('collected-urls.txt', 'w', encoding='utf-8') as out:
    for url, anchors in sorted(anchor_urls.items()):
        if anchors:
            print(f"{url} {' #' + ' #'.join(sorted(anchors))}")
        else:
            print(f"{url}")

print ("\nProblematic URLs:\n")
for url, anchors in sorted(anchor_urls.items()):
    if not anchors:
        response = requests.head(url, allow_redirects=True, timeout=5)
        exists = response.status_code in (200, 301, 302)
        if not exists:
            print(f"{response.status_code} {url}")


print ("\nMissing anchors:\n")
for url, anchors in sorted(anchor_urls.items()):
    if anchors:
        response = requests.get(url, allow_redirects=True)
        if response.status_code != 200:
            print(f"{response.status_code} {url}")
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            for anchor in anchors:
                if not (soup.find(id=anchor) or soup.find(attrs={'name': anchor})):
                    print(f"{url}#{anchor}")
