# used in workflow after download of github-pages artifact
import os
import sys
from html.parser import HTMLParser

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
                found_url = value.split('?')[0].split("#")[0].split("'")[0].rstrip('/').rstrip('/')
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
        print(f"{url} {' '.join(sorted(anchors))}")
