import os
import time
from collections import deque
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from .models import Anchor, Entity

BASE_URL = "https://hackathon.api.qloo.com"


class QlooError(Exception):
    """Sanitized service failure: never include raw bodies, request headers or keys."""


class QueryBudget:
    def __init__(self, minute_limit=60, hour_limit=500, clock=time.monotonic):
        self.minute_limit = minute_limit
        self.hour_limit = hour_limit
        self.clock = clock
        self.recent = deque()

    def reserve(self):
        now = self.clock()
        while self.recent and self.recent[0] <= now - 3600:
            self.recent.popleft()
        minute_count = sum(timestamp > now - 60 for timestamp in self.recent)
        if minute_count >= self.minute_limit or len(self.recent) >= self.hour_limit:
            raise QlooError("Free-demo Qloo query budget reached. Wait before retrying.")
        self.recent.append(now)


_live_budget = QueryBudget()


class QlooClient:
    def __init__(self, key: str | None = None, transport=None, budget=None):
        self._key = key if key is not None else os.environ.get("QLOO_API_KEY")
        self._transport = transport
        self._budget = budget or (QueryBudget() if transport is not None else _live_budget)

    @property
    def configured(self):
        return bool(self._key and self._key.strip())

    async def _get(self, path: str, params: dict):
        if not self.configured:
            raise QlooError("Qloo key pending. Live queries are unavailable; preview is fictional.")
        self._budget.reserve()
        try:
            async with httpx.AsyncClient(
                timeout=20,
                transport=self._transport,
                trust_env=False,
                follow_redirects=False,
                headers={"X-Api-Key": self._key},
            ) as client:
                response = await client.get(BASE_URL + path, params=params)
        except httpx.HTTPError:
            raise QlooError("Qloo could not be reached. Retry the live query later.") from None
        if response.status_code == 429:
            raise QlooError("Qloo rate limit reached. Wait before retrying.")
        if response.status_code in (401, 403):
            raise QlooError("Qloo access was rejected. Verify the hackathon key and permissions.")
        if response.status_code == 402:
            raise QlooError("Free Qloo access is unavailable. No paid fallback was attempted.")
        if response.status_code != 200:
            raise QlooError("Qloo returned an unexpected status. No recommendations were invented.")
        try:
            payload = response.json()
        except ValueError:
            raise QlooError("Qloo returned invalid JSON. Retry later.") from None
        if not isinstance(payload, dict) or (
            "success" in payload and payload["success"] is not True
        ):
            raise QlooError("Qloo did not confirm a successful query.")
        return payload

    @staticmethod
    def _entities(rows):
        if not isinstance(rows, list):
            raise QlooError("Qloo response schema changed. Live results need validation.")
        result = []
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                raise QlooError("Qloo response contains an invalid entity.")
            try:
                entity_id = str(UUID(row["entity_id"]))
                name = row["name"]
                if not isinstance(name, str) or not name.strip():
                    raise ValueError
            except (KeyError, ValueError, TypeError, AttributeError):
                raise QlooError("Qloo entity identity is missing or invalid.") from None
            if entity_id in seen:
                continue
            seen.add(entity_id)
            props = row.get("properties") or {}
            art = props.get("image") if isinstance(props, dict) else None
            url = art.get("url") if isinstance(art, dict) else None
            if not isinstance(url, str) or urlsplit(url).scheme != "https":
                url = None
            types = row.get("types")
            entity_type = (
                next(
                    (
                        value
                        for value in types
                        if isinstance(value, str)
                        and value.startswith("urn:entity:")
                        and len(value) <= 80
                    ),
                    None,
                )
                if isinstance(types, list)
                else None
            )
            year = props.get("release_year") if isinstance(props, dict) else None
            if type(year) is not int or not 1800 <= year <= 2200:
                year = None
            result.append(
                Entity(
                    entity_id=entity_id,
                    name=name[:180],
                    image_url=url,
                    entity_type=entity_type,
                    release_year=year,
                )
            )
        return result

    async def search(self, query: str):
        query = query.strip()
        if not 2 <= len(query) <= 100:
            raise ValueError("Search with 2 to 100 characters.")
        payload = await self._get("/search", {"query": query, "take": 8})
        return [
            Anchor(
                entity_id=e.entity_id,
                name=e.name,
                source="qloo",
                entity_type=e.entity_type,
                release_year=e.release_year,
            )
            for e in self._entities(payload.get("results"))
        ]

    async def recommendations(self, anchors: list[Anchor], excluded: set[str], page=1):
        params = {
            "filter.type": "urn:entity:movie",
            "signal.interests.entities": ",".join(a.entity_id for a in anchors),
            "sort_by": "affinity",
            "take": 50,
            "page": page,
        }
        if excluded:
            params["filter.exclude.entities"] = ",".join(sorted(excluded))
        payload = await self._get("/v2/insights", params)
        results = payload.get("results")
        if not isinstance(results, dict):
            raise QlooError("Qloo response schema changed. Live results need validation.")
        return self._entities(results.get("entities"))
