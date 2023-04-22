from typing import Optional

import httpx
import strawberry
import xmltodict
from sqlalchemy import select, update

from .db import db
from .models import Category, Entry, Feed, Subscription, User, UserEntry
from .parser import make_parser

# TODO logic + async workers to update feeds


async def get_user(id: strawberry.ID):
    return db.session.get(User, id)


async def get_feed(id: strawberry.ID):
    return db.session.get(Feed, id)


async def get_subscription(id: strawberry.ID):
    return db.session.get(Subscription, id)


async def delete_subscription(id: strawberry.ID):
    subscription = db.session.scalar(select(Subscription).where(Subscription.id == id))
    db.session.delete(subscription)
    db.session.commit()


async def get_entry(id: strawberry.ID):
    return db.session.get(Entry, id)


async def mark_as_read(id: strawberry.ID, user_id: strawberry.ID):
    user_entry = db.session.scalar(
        update(UserEntry)
        .where(UserEntry.id == id, UserEntry.user_id == user_id)
        .values(read=True)
        .returning(UserEntry)
    )
    db.session.commit()
    return user_entry


async def get_user_entry(id: strawberry.ID):
    return db.session.get(UserEntry, id)


async def get_category(id: strawberry.ID):
    return db.session.get(Category, id)


async def get_users():
    return db.session.scalars(select(User)).all()


async def get_feeds():
    return db.session.scalars(select(Feed)).all()


async def get_subscriptions():
    return db.session.scalars(select(Subscription)).all()


async def get_categories():
    return db.session.scalars(select(Category)).all()


async def add_subscription(
    url: str, user_id: int, category: Optional[str]
) -> Optional[Subscription]:
    # Check if the user exists
    if not db.session.get(User, user_id):
        return None

    feed = await fetch_feed(url)

    if feed is None:
        return None

    existing_subscription = db.session.scalar(
        select(Subscription)
        .join(Feed)
        .join(Category)
        .where(
            Feed.feed_link == feed.feed_link,
            Subscription.user_id == user_id,
        )
    )
    if existing_subscription:
        return existing_subscription

    category_record = None

    if category is not None and category is not strawberry.UNSET:
        category_record = db.session.scalar(
            select(Category).where(
                Category.name == category, Category.user_id == user_id
            )
        )
        if category_record is None:
            category_record = Category(name=category, user_id=user_id)

    subscription = Subscription(user_id=user_id, feed=feed, category=category_record)

    for entry in feed.entries:
        db.session.add(
            UserEntry(
                user_id=user_id, entry=entry, read=False, subscription=subscription
            )
        )

    db.session.add(subscription)
    db.session.commit()
    return subscription


async def add_feed(url: str) -> Optional[Feed]:
    feed = await fetch_feed(url)
    if feed is not None:
        db.session.add(feed)
        db.session.commit()
    return feed


USER_AGENT = "feeder/1 +https://github.com/Jackevansevo/feeder/"


async def fetch_feed(url: str) -> Optional[Feed]:
    # Check if the feed already exists
    existing_feed = db.session.scalar(select(Feed).where(Feed.feed_link == url))
    if existing_feed:
        return existing_feed

    async with httpx.AsyncClient(
        follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as client:
        resp = await client.get(url)

    # TODO How to gracefully return this error?
    resp.raise_for_status()

    data = xmltodict.parse(resp.content)

    parser = make_parser(data)

    parsed_feed, entries = parser.parse()
    if parsed_feed is None:
        return

    feed_link = parsed_feed.get("feed_link")
    if feed_link is None:
        parsed_feed["feed_link"] = str(resp.url)

    feed = Feed(entries=[Entry(**entry) for entry in entries], **parsed_feed)
    return feed


async def import_opml(content, user_id=1):
    data = xmltodict.parse(content)
    opml = data.get("opml")
    if not opml:
        raise Exception("not a valid opml file")

    body = opml.get("body", {})
    feed_links = set()
    for category_section in body.get("outline"):
        category_name = category_section.get("@text")
        category_section = category_section.get("outline")

        if isinstance(category_section, dict):
            category_section = [category_section]

        for feed_section in category_section:
            feed_link = feed_section.get("@xmlUrl")
            if feed_link is not None:
                if feed_link in feed_links:
                    continue

                feed_links.add(feed_link)
                await add_subscription(feed_link, user_id, category_name)
