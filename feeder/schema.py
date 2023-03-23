import datetime as dt
from typing import List, Optional

import strawberry

from .resolvers import (
    add_feed,
    add_subscription,
    get_categories,
    get_category,
    get_entry,
    get_feed,
    get_feeds,
    get_subscription,
    get_subscriptions,
    get_user,
    get_user_entry,
    get_users,
)


@strawberry.type
class User:
    id: Optional[int]
    subscriptions: List["Subscription"]
    categories: List["Category"]
    entries: List["UserEntry"]
    email: str


@strawberry.type
class Category:
    id: Optional[int]

    user_id: Optional[int]
    user: Optional["User"]

    subscriptions: List["Subscription"]
    name: str


@strawberry.type
class Subscription:
    id: Optional[int]

    user_id: Optional[int]
    user: Optional["User"]

    category_id: Optional[int]
    category: Optional["Category"]

    feed_id: Optional[int]
    feed: Optional["Feed"]

    entries: List["UserEntry"]

    unread_count: int


@strawberry.type
class Feed:
    id: Optional[int]
    title: str
    url: str
    link: str

    entries: List["Entry"]
    subscribers: List["Subscription"]


@strawberry.type
class UserEntry:
    id: Optional[int]

    user_id: Optional[int]
    user: Optional["User"]

    entry_id: Optional[int]
    entry: Optional["Entry"]

    subscription_id: Optional[int]
    subscription: Optional["Subscription"]

    read: bool


@strawberry.type
class Entry:
    id: Optional[int]
    link: str
    title: str
    content: str

    feed_id: Optional[int]
    feed: Optional[Feed]

    published: dt.datetime


@strawberry.type
class Query:
    feeds: List[Feed] = strawberry.field(resolver=get_feeds)
    users: List[User] = strawberry.field(resolver=get_users)
    entries: List[Entry] = strawberry.field(resolver=get_feeds)
    subscriptions: List[Subscription] = strawberry.field(resolver=get_subscriptions)
    categories: List[Category] = strawberry.field(resolver=get_categories)

    @strawberry.field
    async def user(self, id: strawberry.ID) -> Optional[User]:
        return await get_user(id)

    @strawberry.field
    async def feed(self, id: strawberry.ID) -> Optional[Feed]:
        return await get_feed(id)

    @strawberry.field
    async def subscription(self, id: strawberry.ID) -> Optional[Subscription]:
        return await get_subscription(id)

    @strawberry.field
    async def entry(self, id: strawberry.ID) -> Optional[Entry]:
        return await get_entry(id)

    @strawberry.field
    async def user_entry(self, id: strawberry.ID) -> Optional[UserEntry]:
        return await get_user_entry(id)

    @strawberry.field
    async def category(self, id: strawberry.ID) -> Optional[Category]:
        return await get_category(id)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_feed(self, url: str) -> Optional[Feed]:
        return await add_feed(url)

    @strawberry.mutation
    async def add_subscription(
        self, url: str, user_id: int, category: Optional[str]
    ) -> Optional[Subscription]:
        return await add_subscription(url, user_id, category=category)
