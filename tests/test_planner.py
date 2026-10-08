import pytest

from common_ground.models import Entity, PlanRequest
from common_ground.planner import plan_group, rank_candidates
from common_ground.preview import ANCHORS, PreviewProvider
from common_ground.qloo import QlooError


def preview_request(**changes):
    values = {
        "source": "synthetic",
        "members": [
            {"name": name, "anchors": [anchor.model_dump()]}
            for name, anchor in zip(["Asha", "Leo", "Mina"], ANCHORS, strict=True)
        ],
    }
    return PlanRequest(**(values | changes))


async def test_fair_pick_differs_from_average_pick():
    result = await plan_group(preview_request(), PreviewProvider())
    assert result["source_label"] == "Fictional preview"
    assert result["candidates"][0]["entity_id"] == "preview-ferry"
    assert result["average_first_pick"]["entity_id"] == "preview-platform"
    assert result["candidates"][0]["coverage"] == 3
    assert "probabilities" in result["method"]


async def test_hard_veto_is_never_relaxed():
    result = await plan_group(preview_request(veto_ids=["preview-ferry"]), PreviewProvider())
    assert "preview-ferry" in result["excluded_ids"]
    assert all(c["entity_id"] != "preview-ferry" for c in result["candidates"])
    assert result["candidates"][0]["entity_id"] == "preview-atlas"


class DisjointProvider:
    def __init__(self):
        self.calls = []

    async def recommendations(self, anchors, excluded, page=1):
        self.calls.append(page)
        return [Entity(entity_id=anchors[0].entity_id + "-only", name="Disjoint fictional film")]


async def test_no_evidence_for_everyone_never_fabricates_consensus():
    provider = DisjointProvider()
    result = await plan_group(preview_request(), provider)
    assert result["status"] == "no_common_ground"
    assert result["candidates"] == []
    assert len(result["partial_candidates"]) == 3
    assert result["broadened"]
    assert sorted(provider.calls) == [1, 1, 1, 2, 2, 2]


async def test_partial_evidence_requires_explicit_opt_in():
    result = await plan_group(preview_request(require_everyone=False), DisjointProvider())
    assert result["status"] == "ready"
    assert all(c["coverage"] == 1 for c in result["candidates"])
    assert sum(r["rank"] is None for r in result["candidates"][0]["evidence"]) == 2


async def test_any_participant_failure_fails_the_whole_plan():
    class FailedProvider:
        async def recommendations(self, anchors, excluded, page=1):
            if anchors[0].entity_id == "preview-action":
                raise QlooError("One participant query failed.")
            return []

    with pytest.raises(QlooError, match="participant"):
        await plan_group(preview_request(), FailedProvider())


def test_duplicate_entities_do_not_inflate_rank_or_coverage():
    e = Entity(entity_id="film", name="Film")
    request = preview_request()
    result = rank_candidates(request.members, [[e, e], [e], [e]], set())
    assert len(result) == 1
    assert all(row["rank"] == 1 for row in result[0]["evidence"])


@pytest.mark.parametrize("names", [["A", "A", "C"], [" A ", "a", "C"], [" ", "B", "C"]])
def test_names_must_be_unique_and_not_blank(names):
    members = preview_request().model_dump()["members"]
    for person, name in zip(members, names, strict=True):
        person["name"] = name
    with pytest.raises(ValueError):
        preview_request(members=members)


def test_no_mixing_live_and_preview_anchors():
    with pytest.raises(ValueError, match="cannot be mixed"):
        preview_request(source="qloo")


def test_limit_group_size():
    with pytest.raises(ValueError):
        preview_request(members=preview_request().model_dump()["members"][:1])


def test_duplicate_normalized_uuids_rejected():
    anchor = {
        "entity_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "name": "Fixture",
        "source": "qloo",
    }
    with pytest.raises(ValueError, match="distinct"):
        PlanRequest(
            source="qloo",
            members=[
                {
                    "name": "A",
                    "anchors": [anchor, anchor | {"entity_id": anchor["entity_id"].upper()}],
                },
                {"name": "B", "anchors": [anchor]},
            ],
        )


async def test_unknown_preview_anchor_does_not_invent_results():
    request = preview_request()
    request.members[0].anchors[0].entity_id = "unknown"
    with pytest.raises(ValueError, match="fictional preview anchors"):
        await plan_group(request, PreviewProvider())
