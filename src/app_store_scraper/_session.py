from urllib.parse import urljoin
from typing import Any

import requests

from .__about__ import __version__


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
        self._session = requests.Session()

    def _get_app_page(self, app_id: str | int, country: str) -> str:
        url = urljoin(self._web_base_url, f"/{country}/app/_/id{app_id}")
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _get_api_resource(
        self,
        url: str,
        *,
        access_token: str,
        params: dict[str, str] | None = None,
    ) -> Any:
        response = self._session.get(
            urljoin(self._api_base_url, url),
            params=params,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Origin": self._web_base_url,
                "User-Agent": f"app-store-scraper/{__version__}",
            },
        )
        response.raise_for_status()
        return response.json()
