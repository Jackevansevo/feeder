import xml.etree.ElementTree as ET
from typing import Optional

import httpx
import strawberry
from sqlalchemy import select
from strawberry.types import Info

from .db import db
from .models import Category, Entry, Feed, Subscription, User, UserEntry
from .parser import RSSParser


async def get_user(id: strawberry.ID):
    return db.session.get(User, id)


async def get_feed(id: strawberry.ID):
    return db.session.get(Feed, id)


async def get_subscription(id: strawberry.ID):
    return db.session.get(Subscription, id)


async def get_entry(id: strawberry.ID):
    return db.session.get(Entry, id)


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

    feed = await add_feed(url)
    if feed is None:
        return None

    existing_subscription = db.session.scalar(
        select(Subscription)
        .join(Feed)
        .join(Category)
        .where(Subscription.feed == feed, Subscription.user_id == user_id)
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
    # Check if the feed already exists
    existing_feed = db.session.scalar(select(Feed).where(Feed.url == url))
    if existing_feed:
        return existing_feed

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url)

    # TODO How to gracefully return this error?
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    if root.tag == "rss":
        parser = RSSParser(root)
    else:
        raise NotImplementedError(f"{root.tag} not implemented")

    parsed_feed, entries = parser.parse()
    if parsed_feed is None:
        return

    feed_url = parsed_feed.get("url")
    if feed_url is None:
        parsed_feed["url"] = str(resp.url)

    feed = Feed(entries=[Entry(**entry) for entry in entries], **parsed_feed)
    db.session.add(feed)
    db.session.commit()
    return feed
