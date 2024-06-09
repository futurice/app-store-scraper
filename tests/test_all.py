import json
import urllib.parse

import pytest
from faker import Faker
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from app_store_scraper import AppReview, AppStoreEntry, AppStoreSession

APP_ID = "123456789"
COUNTRY = "de"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"


def mock_app_store_page(httpserver: HTTPServer):
    app_config = {"MEDIA_API": {"token": API_TOKEN}}
    app_config_encoded = urllib.parse.quote(json.dumps(app_config))
    httpserver.expect_request(f"/{COUNTRY}/app/_/id{APP_ID}").respond_with_data(
        f"""
        <!doctype html>
        <html>
          <head>
            <!-- … -->
            <meta name="web-experience-app/config/environment" content="{app_config_encoded}">
            <!-- … -->
          </head>
          <body>
            <!-- … -->
          </body>
        </html>
        """,
    )


def mock_app_reviews(
    httpserver: HTTPServer,
    reviews: list[AppReview],
    *,
    page_size: int,
):
    path = f"/v1/catalog/{COUNTRY}/apps/{APP_ID}/reviews"

    def request_handler(request: Request) -> Response:
        offset = int(request.args.get("offset", 0))
        next_offset = offset + page_size
        page = reviews[offset:next_offset]

        if len(page) > 0:
            next_path = f"{path}?offset={next_offset}"
        else:
            next_path = None

        return Response(
            status=200,
            content_type="application/json",
            response=json.dumps(
                {
                    "next": next_path,
                    "data": [
                        {
                            "id": review.id,
                            "attributes": {
                                "date": review.date.isoformat(),
                                "userName": review.user_name,
                                "title": review.title,
                                "review": review.review,
                                "rating": review.rating,
                                "isEdited": review.is_edited,
                            },
                        }
                        for review in page
                    ],
                }
            ),
        )

    httpserver.expect_request(path).respond_with_handler(request_handler)


def fake_app_review(faker: Faker):
    return AppReview(
        id=faker.unique.random_int(min=0, max=2**32),
        date=faker.past_datetime(),
        user_name=faker.user_name(),
        title=" ".join(faker.words(3)),
        review=" ".join(faker.sentences(2)),
        rating=faker.random_int(min=1, max=5),
        is_edited=faker.boolean(),
        developer_response=None,
    )


@pytest.fixture
def session(httpserver: HTTPServer) -> AppStoreSession:
    session = AppStoreSession()
    session._web_base_url = httpserver.url_for("")
    session._api_base_url = httpserver.url_for("")
    return session


def test_basic(
    httpserver: HTTPServer,
    faker: Faker,
    session: AppStoreSession,
):
    reviews = [fake_app_review(faker) for _ in range(10)]

    mock_app_store_page(httpserver)
    mock_app_reviews(httpserver, reviews, page_size=3)

    app = AppStoreEntry(APP_ID, COUNTRY, session=session)
    retrieved_reviews = list(app.reviews())

    assert retrieved_reviews == reviews


def test_reviews_limit(
    httpserver: HTTPServer,
    faker: Faker,
    session: AppStoreSession,
):
    reviews = [fake_app_review(faker) for _ in range(10)]
    limit = 5

    mock_app_store_page(httpserver)
    mock_app_reviews(httpserver, reviews, page_size=3)

    app = AppStoreEntry(APP_ID, COUNTRY, session=session)
    retrieved_reviews = list(app.reviews(limit=limit))

    assert retrieved_reviews == reviews[:limit]
