from urllib.parse import urljoin
from typing import Any

import urllib3

from .__about__ import __version__
from ._errors import AppNotFound, AppStoreError


class AppStoreSession:
    """
    An App Store session is a pool of HTTP connections to the App Store.
    When scraping multiple App Store entries, using a shared session
    improves performance and resource usage as the same set of HTTP
    connections is reused across requests.
    """

    _web_base_url = "https://apps.apple.com"
    _api_base_url = "https://amp-api-edge.apps.apple.com"

    def __init__(self):
        self._http = urllib3.PoolManager(
            headers={
                "Origin": self._web_base_url,
                "User-Agent": f"app-store-scraper/{__version__}",
            }
        )

    def _get_app_page(self, app_id: str | int, country: str) -> str:
        url = urljoin(self._web_base_url, f"/{country}/app/_/id{app_id}")
        response = self._http.request("GET", url)

        if response.status == 404:
            raise AppNotFound(app_id, country)
        elif response.status >= 400:
            raise AppStoreError(
                f"Fetching App Store page failed with status {response.status}"
            )

        return response.data.decode()

    def _get_api_resource(
        self,
        url: str,
        *,
        access_token: str,
        params: dict[str, str] | None = None,
    ) -> Any:
        response = self._http.request(
            "GET",
            urljoin(self._api_base_url, url),
            fields=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status >= 400:
            raise AppStoreError(
                f"App Store API request failed with status {response.status}"
            )

        return response.json()
