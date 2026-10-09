import httpx
import pytest

from common_ground.models import Anchor
from common_ground.qloo import BASE_URL, QlooClient, QlooError, QueryBudget

ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
EXCLUDED = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


async def test_documented_get_endpoint_header_and_parameters():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "success": True,
                "results": {
                    "entities": [
                        {"entity_id": ID, "name": "Entirely fictional protocol-test entity"}
                    ]
                },
            },
        )

    client = QlooClient("test-only-not-a-real-key", httpx.MockTransport(handle))
    rows = await client.recommendations(
        [Anchor(entity_id=ID, name="Fixture", source="qloo")], {EXCLUDED}, page=2
    )
    req = calls[0]
    assert str(req.url).startswith(BASE_URL + "/v2/insights?")
    assert req.method == "GET"
    assert req.headers["X-Api-Key"] == "test-only-not-a-real-key"
    assert "test-only-not-a-real-key" not in str(req.url)
    assert req.url.params["filter.type"] == "urn:entity:movie"
    assert req.url.params["signal.interests.entities"] == ID
    assert req.url.params["filter.exclude.entities"] == EXCLUDED
    assert req.url.params["take"] == "50"
    assert req.url.params["page"] == "2"
    assert rows[0].entity_id == ID


async def test_search_has_different_result_nesting():
    def handle(request):
        assert request.url.path == "/search"
        assert request.url.params["query"] == "Fixture artist"
        return httpx.Response(
            200, json={"success": True, "results": [{"entity_id": ID, "name": "Fixture artist"}]}
        )

    rows = await QlooClient("test", httpx.MockTransport(handle)).search("Fixture artist")
    assert rows[0].source == "qloo"


@pytest.mark.parametrize("rows", [[], [{"entity_id": ID, "name": "Fictional film"}]])
async def test_search_accepts_result_schema_without_optional_success_flag(rows):
    client = QlooClient(
        "test", httpx.MockTransport(lambda _: httpx.Response(200, json={"results": rows}))
    )
    results = await client.search("Fixture")
    assert len(results) == len(rows)


@pytest.mark.parametrize("flag", [False, None, "true", 1])
async def test_explicit_invalid_success_flag_is_not_ignored(flag):
    client = QlooClient(
        "test",
        httpx.MockTransport(lambda _: httpx.Response(200, json={"success": flag, "results": []})),
    )
    with pytest.raises(QlooError):
        await client.search("Fixture")


async def test_missing_key_fails_before_any_network_access():
    def handle(request):
        pytest.fail("No network request should be made without a key.")

    with pytest.raises(QlooError, match="pending"):
        await QlooClient("", httpx.MockTransport(handle)).search("Fixture")


@pytest.mark.parametrize("status", [301, 401, 403, 402, 429, 500])
async def test_errors_are_sanitized_and_never_follow_redirects_or_paid_fallback(status):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(
            status,
            headers={"Location": "https://attacker.invalid"},
            text="raw secret test-only-not-a-real-key",
        )

    with pytest.raises(QlooError) as error:
        await QlooClient("test-only-not-a-real-key", httpx.MockTransport(handle)).search("Fixture")
    assert "test-only-not-a-real-key" not in str(error.value)
    assert "raw secret" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "payload", [[], {"success": False}, {"results": {}}, {"success": True, "results": "wrong"}]
)
async def test_bad_schemas_fail_closed(payload):
    client = QlooClient("test", httpx.MockTransport(lambda _: httpx.Response(200, json=payload)))
    with pytest.raises(QlooError):
        await client.search("Fixture")


async def test_invalid_json_fails_closed():
    client = QlooClient("test", httpx.MockTransport(lambda _: httpx.Response(200, text="bad")))
    with pytest.raises(QlooError, match="invalid JSON"):
        await client.search("Fixture")


@pytest.mark.parametrize(
    "row", [{}, {"entity_id": "bad", "name": "Film"}, {"entity_id": ID, "name": ""}]
)
def test_invalid_identity_is_not_silently_skipped(row):
    with pytest.raises(QlooError):
        QlooClient._entities([row])


def test_deduplicate_ids_and_reject_unsafe_image_scheme():
    rows = QlooClient._entities(
        [
            {
                "entity_id": ID,
                "name": "Fictional",
                "properties": {"image": {"url": "javascript:bad"}},
            },
            {"entity_id": ID.upper(), "name": "Duplicate"},
        ]
    )
    assert len(rows) == 1
    assert rows[0].image_url is None


async def test_timeout_is_sanitized():
    def handle(request):
        raise httpx.ReadTimeout("raw secret", request=request)

    with pytest.raises(QlooError, match="could not be reached"):
        await QlooClient("test", httpx.MockTransport(handle)).search("Fixture")


async def test_search_preserves_category_and_year_for_identity_confirmation():
    client = QlooClient(
        "test",
        httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "entity_id": ID,
                            "name": "Fictional protocol-test film",
                            "types": ["urn:entity:movie"],
                            "properties": {"release_year": 2014},
                        }
                    ]
                },
            )
        ),
    )
    result = (await client.search("Fixture"))[0]
    assert result.entity_type == "urn:entity:movie"
    assert result.release_year == 2014


@pytest.mark.parametrize("year", [True, "2014", 1700, 9999, None])
def test_optional_year_does_not_invent_or_coerce_metadata(year):
    result = QlooClient._entities(
        [
            {
                "entity_id": ID,
                "name": "Fictional",
                "types": "wrong",
                "properties": {"release_year": year},
            }
        ]
    )[0]
    assert result.release_year is None
    assert result.entity_type is None


def test_query_budget_bounds_minute_and_hour_without_unbounded_storage():
    now = [0.0]
    budget = QueryBudget(minute_limit=2, hour_limit=3, clock=lambda: now[0])
    budget.reserve()
    budget.reserve()
    with pytest.raises(QlooError, match="budget reached"):
        budget.reserve()
    now[0] = 60.0
    budget.reserve()
    now[0] = 120.0
    with pytest.raises(QlooError, match="budget reached"):
        budget.reserve()
    now[0] = 3600.0
    budget.reserve()
    assert len(budget.recent) == 2


async def test_query_budget_rejects_before_network_access():
    calls = []
    budget = QueryBudget(minute_limit=1)
    client = QlooClient(
        "test",
        httpx.MockTransport(
            lambda request: calls.append(request) or httpx.Response(200, json={"results": []})
        ),
        budget=budget,
    )
    await client.search("Fixture")
    with pytest.raises(QlooError, match="budget reached"):
        await client.search("Fixture")
    assert len(calls) == 1
