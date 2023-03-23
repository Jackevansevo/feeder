import datetime as dt
from typing import List

from sqlalchemy import ForeignKey, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from .db import db


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="user")
    categories: Mapped[List["Category"]] = relationship(back_populates="user")
    entries: Mapped[List["UserEntry"]] = relationship(back_populates="user")
    email: Mapped[str]


class Category(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="categories")

    subscriptions: Mapped[List["Subscription"]] = relationship(
        back_populates="category"
    )
    name: Mapped[str]


class Subscription(db.Model):
    __table_args__ = (UniqueConstraint("user_id", "feed_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="subscriptions")

    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    category: Mapped["Category"] = relationship(back_populates="subscriptions")

    feed_id: Mapped[int] = mapped_column(ForeignKey("feed.id"), nullable=False)
    feed: Mapped["Feed"] = relationship(back_populates="subscribers")

    entries: Mapped[List["UserEntry"]] = relationship(back_populates="subscription")


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
    __table_args__ = (UniqueConstraint("url"),)
    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str]
    url: Mapped[str]
    link: Mapped[str]

    entries: Mapped[List["Entry"]] = relationship(back_populates="feed")
    subscribers: Mapped[List["Subscription"]] = relationship(back_populates="feed")


class Entry(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str]
    title: Mapped[str]
    content: Mapped[str]

    feed_id: Mapped[int] = mapped_column(ForeignKey("feed.id"))
    feed: Mapped["Feed"] = relationship(back_populates="entries")

    published: Mapped[dt.datetime]


Subscription.unread_count = column_property(
    select(func.count(UserEntry.id))
    .where(UserEntry.subscription_id == Subscription.id)
    .where(UserEntry.read == False)
    .correlate_except(UserEntry)
    .scalar_subquery()
)
