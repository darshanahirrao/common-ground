import asyncio
from datetime import UTC, datetime

from .models import Entity, PlanRequest


def rank_candidates(members, lists: list[list[Entity]], excluded: set[str]):
    """Maximize the weakest reciprocal rank; missing evidence is zero, not dislike."""
    union = {}
    ranks = []
    for entities in lists:
        person = {}
        for entity in entities:
            if entity.entity_id not in person:
                person[entity.entity_id] = len(person) + 1
                union.setdefault(entity.entity_id, entity)
        ranks.append(person)
    candidates = []
    for entity_id, entity in union.items():
        if entity_id in excluded:
            continue
        evidence = []
        for member, person in zip(members, ranks, strict=True):
            rank = person.get(entity_id)
            score = 61 / (60 + rank) if rank else 0
            evidence.append({"person": member.name, "rank": rank, "rank_score": score})
        scores = [item["rank_score"] for item in evidence]
        candidates.append(
            {
                **entity.model_dump(),
                "evidence": evidence,
                "coverage": sum(item["rank"] is not None for item in evidence),
                "weakest_rank_score": min(scores),
                "mean_rank_score": sum(scores) / len(scores),
            }
        )
    return sorted(
        candidates,
        key=lambda c: (
            -c["weakest_rank_score"],
            -c["coverage"],
            -c["mean_rank_score"],
            c["entity_id"],
        ),
    )


async def plan_group(request: PlanRequest, provider):
    excluded = set(request.veto_ids) | {
        anchor.entity_id for person in request.members for anchor in person.anchors
    }
    lists = await asyncio.gather(
        *(provider.recommendations(person.anchors, excluded, page=1) for person in request.members)
    )
    steps = [
        {
            "person": p.name,
            "endpoint": "/v2/insights",
            "page": 1,
            "anchor_ids": [a.entity_id for a in p.anchors],
            "returned": len(entities),
        }
        for p, entities in zip(request.members, lists, strict=True)
    ]
    candidates = rank_candidates(request.members, lists, excluded)
    broadened = False
    if not any(c["coverage"] == len(request.members) for c in candidates):
        # Broaden retrieval, never relax a veto or silently drop a failed participant.
        additions = await asyncio.gather(
            *(
                provider.recommendations(person.anchors, excluded, page=2)
                for person in request.members
            )
        )
        for index, (person, extra) in enumerate(zip(request.members, additions, strict=True)):
            lists[index].extend(extra)
            steps.append(
                {
                    "person": person.name,
                    "endpoint": "/v2/insights",
                    "page": 2,
                    "anchor_ids": [a.entity_id for a in person.anchors],
                    "returned": len(extra),
                }
            )
        candidates = rank_candidates(request.members, lists, excluded)
        broadened = True
    full = [c for c in candidates if c["coverage"] == len(request.members)]
    shown = full if request.require_everyone else candidates
    average = max(candidates, key=lambda c: c["mean_rank_score"], default=None)
    return {
        "source": request.source,
        "source_label": "Live Qloo" if request.source == "qloo" else "Fictional preview",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "ready" if shown else "no_common_ground",
        "people": [p.name for p in request.members],
        "candidates": shown[:8],
        "partial_candidates": [c for c in candidates if c["coverage"] < len(request.members)][:4],
        "average_first_pick": average,
        "excluded_ids": sorted(excluded),
        "broadened": broadened,
        "query_steps": steps,
        "method": "Weakest reciprocal rank first, then coverage, then mean. "
        "61/(60+rank); absent=0. Rank scores are not satisfaction probabilities.",
        "uncertainty": "Absence from a retrieved list is missing evidence, "
        "not a negative preference. "
        "Rankings do not verify streaming availability, suitability or runtime.",
    }
