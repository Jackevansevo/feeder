import datetime as dt
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypedDict

import dateutil.parser


class Feed(TypedDict):
    title: Optional[str]
    site_link: Optional[str]
    feed_link: Optional[str]


class Entry(TypedDict):
    title: Optional[str]
    link: Optional[str]
    published: Optional[dt.datetime]
    summary: Optional[str]
    content: Optional[str]


def make_parser(data):
    if "rss" in data:
        return RSSParser(data)
    else:
        return AtomParser(data)


class Parser(Protocol):
    def parse_entries(
        self, entries: List[Dict[str, Any]] | Dict[str, Any]
    ) -> List[Entry]:
        if isinstance(entries, dict):
            entries = [entries]
        return [self.parse_entry(entry) for entry in entries]

    @abstractmethod
    def parse_entry(self, entry: Dict[str, Any]) -> Entry:
        ...

    @abstractmethod
    def parse(self) -> Tuple[Feed, List[Entry]]:
        ...

    def parse_text(self, value) -> Optional[str]:
        if value is None:
            return

        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            type_tag = value.get("@type")
            if type_tag in {"html", "text"}:
                return value.get("#text")
            if type_tag == "xhtml":
                div = value.get("div")
                if div:
                    return div.get("#text")
        raise Exception(f"Failed to handle: {value}")


class RSSParser(Parser):
    def __init__(self, data):
        self.data = data

    def parse_entry(self, data: Dict[str, Any]):
        published = data.get("pubDate")

        return {
            "title": data.get("title"),
            "link": data.get("link"),
            "published": dateutil.parser.parse(published) if published else None,
            "summary": data.get("description"),
            "content": self.parse_text(data.get("content") or data.get("content:encoded")),
        }

    def parse(self) -> Tuple[Feed, List[Entry]]:
        channel = self.data["rss"]["channel"]
        return {
            "title": channel.get("title"),
            "site_link": channel.get("link"),
            "feed_link": None,
        }, self.parse_entries(channel.get("item"))


class AtomParser(Parser):
    def __init__(self, data):
        self.data = data

    def parse_links(self, links):
        if isinstance(links, str):
            return links, None

        elif isinstance(links, list):
            if len(links) == 1:
                return links[0]["@href"], None

            site_link, feed_link = None, None
            for tag in links:
                rel = tag.get("@rel")
                if rel == "self":
                    feed_link = tag["@href"]
                elif rel == "alternate":
                    site_link = tag["@href"]

            if site_link is None and feed_link is not None:
                for tag in links:
                    if tag != feed_link:
                        site_link = tag["@href"]

            return site_link, feed_link

        return None, None

    def parse_link(
        self, value: Optional[str | Dict[str, str] | List[Dict[str, str]]]
    ) -> Optional[str]:
        """
        A single article might have a number of different links, i.e. to
        comments/replies or the main article
        """
        if value is None:
            return value

        if isinstance(value, str):
            breakpoint()
            return value

        elif isinstance(value, list):
            for link in value:
                return self.parse_link(link)

        elif isinstance(value, dict):
            href = value.get("@href")

            if value.get("@rel") == "alternate":
                if value.get("@type") == "text/html":
                    return href
                return href

            if href:
                return href

        breakpoint()

    def parse_entry(self, data):
        published = data.get("published")
        updated = data.get("updated")
        content = data.get("content")
        summary = data.get("summary")

        return {
            "title": self.parse_text(data.get("title")),
            "link": self.parse_link(data.get("link")),
            "summary": self.parse_text(summary) if summary else None,
            "content": self.parse_text(content) if content else None,
            "published": dateutil.parser.parse(published) if published else None,
            "updated": dateutil.parser.parse(updated) if updated else None,
        }

    def parse(self) -> Tuple[Feed, List[Entry]]:
        feed = self.data["feed"]
        site_link, feed_link = self.parse_links(feed["link"])
        return {
            "title": self.parse_text(feed.get("title")),
            "site_link": site_link,
            "feed_link": feed_link,
        }, self.parse_entries(feed.get("entry"))
