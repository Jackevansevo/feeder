import dateutil.parser


class RSSParser:
    def __init__(self, root):
        self.root = root

    def parse_entry(self, root):
        entry = {}

        for node in root:
            if node.tag == "title":
                if node.text:
                    entry["title"] = node.text
            elif node.tag == "link":
                if node.text:
                    entry["link"] = node.text
            elif node.tag == "description":
                if node.text:
                    entry["content"] = node.text
            elif node.tag == "pubDate":
                if node.text:
                    entry["published"] = dateutil.parser.parse(node.text)

        return entry

    def parse(self):
        feed = {}
        entries = []

        channel = self.root.find("channel")

        if not channel:
            return None, []

        for node in channel:
            if node.tag == "title":
                if node.text:
                    feed["title"] = node.text
            elif node.tag == "link":
                if node.text:
                    feed["link"] = node.text
            elif node.tag.endswith("link"):
                if "href" in node.keys():
                    href = node.get("href")
                    if href:
                        feed["url"] = href
            elif node.tag == "item":
                entries.append(self.parse_entry(node))

        return feed, entries
