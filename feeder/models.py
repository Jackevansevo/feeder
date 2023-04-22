import datetime as dt
from typing import List
from urllib.parse import urlparse

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func, select
from sqlalchemy.orm import (
    Mapped,
    column_property,
    mapped_column,
    relationship,
    validates,
)
from sqlalchemy.schema import CheckConstraint

from .db import db


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="user")
    categories: Mapped[List["Category"]] = relationship(back_populates="user")
    entries: Mapped[List["UserEntry"]] = relationship(back_populates="user")
    password: Mapped[str]
    email: Mapped[str]


class Category(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="categories")

    subscriptions: Mapped[List["Subscription"]] = relationship(
        back_populates="category"
    )
    name: Mapped[str]

    @validates("name")
    def validate_some_string(self, _, name) -> str:
        if not name:
            raise ValueError("name cannot be empty")
        return name


class Subscription(db.Model):
    __table_args__ = (UniqueConstraint("user_id", "feed_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="subscriptions")

    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    category: Mapped["Category"] = relationship(back_populates="subscriptions")

    feed_id: Mapped[int] = mapped_column(ForeignKey("feed.id"), nullable=False)
    feed: Mapped["Feed"] = relationship(back_populates="subscribers")

    entries: Mapped[List["UserEntry"]] = relationship(
        back_populates="subscription", cascade="all, delete"
    )


class UserEntry(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="entries")

    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscription.id"))
    subscription: Mapped["Subscription"] = relationship(back_populates="entries")

    entry_id: Mapped[int] = mapped_column(ForeignKey("entry.id"))
    entry: Mapped["Entry"] = relationship()

    read: Mapped[bool]


class Feed(db.Model):
    __table_args__ = (UniqueConstraint("feed_link"),)
    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str]

    feed_link: Mapped[str]
    site_link: Mapped[str]

    entries: Mapped[List["Entry"]] = relationship(back_populates="feed")
    subscribers: Mapped[List["Subscription"]] = relationship(back_populates="feed")

    def __init__(self, title=None, site_link=None, feed_link=None, **kwargs):
        if title is None and site_link is not None:
            title = site_link

        if site_link is None and feed_link is not None:
            # TODO Maybe check the length of the feed_link path (i.e. how many sections)
            site_link = urlparse(feed_link).netloc
        super().__init__(
            title=title, site_link=site_link, feed_link=feed_link, **kwargs
        )


class Entry(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str]
    title: Mapped[str]
    content: Mapped[str] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(String, nullable=True)

    feed_id: Mapped[int] = mapped_column(ForeignKey("feed.id"))
    feed: Mapped["Feed"] = relationship(back_populates="entries")

    published: Mapped[dt.datetime] = mapped_column(DateTime, nullable=True)
    updated: Mapped[dt.datetime] = mapped_column(DateTime, nullable=True)

    def __init__(
        self,
        title=None,
        content=None,
        summary=None,
        published=None,
        updated=None,
        **kwargs
    ):
        if content is None and summary is not None:
            content = summary

        if published is None and updated is not None:
            published = updated

        super().__init__(
            title=title,
            content=content,
            summary=summary,
            published=published,
            updated=updated,
            **kwargs
        )


Subscription.unread_count = column_property(
    select(func.count(UserEntry.id))
    .where(UserEntry.subscription_id == Subscription.id)
    .where(UserEntry.read is False)
    .correlate_except(UserEntry)
    .scalar_subquery()
)
