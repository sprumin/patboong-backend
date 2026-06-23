import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException


RIOT_SERVERS = ("AMERICAS", "ASIA", "EUROPE", "SEA")


class RiotAPIException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "RIOT_API_ERROR"
    default_detail = "Riot API request failed."

    def __init__(self, detail=None, code=None, retryable=True, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(
            {
                "code": code or self.default_code,
                "detail": detail or self.default_detail,
                "retryable": retryable,
            }
        )


class RiotClient:
    def __init__(self, api_key=None, timeout=None):
        self.api_key = api_key or settings.RIOT_API_KEY
        self.timeout = timeout or settings.RIOT_API_TIMEOUT

    def get_account_by_riot_id(self, game_name, tag_line, server):
        path = (
            "/riot/account/v1/accounts/by-riot-id/"
            f"{quote(game_name, safe='')}/{quote(tag_line, safe='')}"
        )
        return self._request(server, path, not_found_code="RIOT_ID_NOT_FOUND")

    def get_account_by_puuid(self, puuid, server):
        path = f"/riot/account/v1/accounts/by-puuid/{quote(puuid, safe='')}"
        return self._request(server, path, not_found_code="RIOT_ACCOUNT_NOT_FOUND")

    def get_match_ids(self, puuid, server, start=0, count=20):
        query = urlencode({"start": start, "count": count})
        path = f"/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids?{query}"
        return self._request(server, path, not_found_code="RIOT_MATCHES_NOT_FOUND")

    def get_match(self, match_id, server):
        path = f"/lol/match/v5/matches/{quote(match_id, safe='')}"
        return self._request(server, path, not_found_code="RIOT_MATCH_NOT_FOUND")

    def _request(self, server, path, not_found_code):
        server = server.upper()
        if server not in RIOT_SERVERS:
            raise RiotAPIException(
                "riot_server must be one of AMERICAS, ASIA, EUROPE, SEA.",
                code="INVALID_RIOT_SERVER",
                retryable=False,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not self.api_key:
            raise RiotAPIException(
                "Riot API key is not configured.",
                code="RIOT_API_NOT_CONFIGURED",
                retryable=True,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        request = Request(
            f"https://{server.lower()}.api.riotgames.com{path}",
            headers={"X-Riot-Token": self.api_key, "Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 400:
                raise RiotAPIException(
                    "Riot rejected the supplied account or match identifier.",
                    code="RIOT_INVALID_REQUEST",
                    retryable=False,
                    status_code=status.HTTP_400_BAD_REQUEST,
                ) from exc
            if exc.code == 404:
                raise RiotAPIException(
                    "The requested Riot account or match was not found.",
                    code=not_found_code,
                    retryable=False,
                    status_code=status.HTTP_404_NOT_FOUND,
                ) from exc
            if exc.code == 429:
                raise RiotAPIException(
                    "Riot API rate limit exceeded. Please retry later.",
                    code="RIOT_RATE_LIMITED",
                    retryable=True,
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                ) from exc
            if exc.code in (401, 403):
                raise RiotAPIException(
                    "Riot API authentication failed. Please retry later.",
                    code="RIOT_API_AUTH_ERROR",
                    retryable=True,
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                ) from exc
            raise RiotAPIException(
                "Riot API returned an error. Please retry later.",
                code="RIOT_UPSTREAM_ERROR",
                retryable=True,
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RiotAPIException(
                "Could not communicate with Riot API. Please retry later.",
                code="RIOT_UPSTREAM_UNAVAILABLE",
                retryable=True,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
