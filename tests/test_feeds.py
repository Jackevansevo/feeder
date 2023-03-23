import pytest

from feeder import create_app
from feeder.db import db
from feeder.models import Feed


@pytest.fixture()
def app():
    app = create_app(db_uri="sqlite://")
    app.config.update(
        {
            "TESTING": True,
        }
    )

    with app.app_context():
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def graphql(client, query, variables={}):
    return client.post(
        "/graphql",
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json"},
    )


def test_get_feed(client):
    feed = Feed(title="test", url="", link="")
    db.session.add(feed)
    db.session.commit()

    query = """
    query GetFeed($feedId: ID!) {
      feed(id: $feedId) {
        id
        title
        url
        link
        entries {
          title
          id
          published
        }
      }
    }
    """
    response = graphql(client, query, {"feedId": feed.id})
    assert response.status_code == 200
    assert response.json["data"]["feed"] == {
        "id": feed.id,
        "title": feed.title,
        "url": feed.url,
        "link": feed.link,
        "entries": [],
    }


def test_get_feeds(client):
    feed = Feed(title="test", url="", link="")
    db.session.add(feed)
    db.session.commit()

    query = """
    {
      feeds {
        id
        title
        url
        link
        entries { title }
      }
    }
    """
    response = graphql(client, query)
    assert response.status_code == 200
    assert response.json["data"]["feeds"] == [
        {
            "id": feed.id,
            "title": feed.title,
            "url": feed.url,
            "link": feed.link,
            "entries": [],
        }
    ]
