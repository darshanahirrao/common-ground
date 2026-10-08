from .models import Anchor, Entity

ANCHORS = [
    Anchor(entity_id="preview-quiet", name="The Lantern House", source="synthetic"),
    Anchor(entity_id="preview-action", name="Orbital Run", source="synthetic"),
    Anchor(entity_id="preview-offbeat", name="Paper Streets", source="synthetic"),
]
FEATURED = {
    "preview-ferry": Entity(entity_id="preview-ferry", name="Night Ferry", preview_art=0),
    "preview-platform": Entity(entity_id="preview-platform", name="Red Platform", preview_art=1),
    "preview-atlas": Entity(entity_id="preview-atlas", name="Moon Atlas", preview_art=2),
}
POSITIONS = {
    "preview-quiet": {"preview-ferry": 15, "preview-platform": 50, "preview-atlas": 18},
    "preview-action": {"preview-ferry": 15, "preview-platform": 1, "preview-atlas": 22},
    "preview-offbeat": {"preview-ferry": 15, "preview-platform": 1, "preview-atlas": 2},
}


class PreviewProvider:
    async def search(self, query):
        return [a for a in ANCHORS if query.casefold() in a.name.casefold()]

    async def recommendations(self, anchors, excluded, page=1):
        if page > 1:
            return []
        lists = []
        for anchor in anchors:
            if anchor.entity_id not in POSITIONS:
                raise ValueError("Choose one of the fictional preview anchors.")
            entities = [
                Entity(entity_id=f"{anchor.entity_id}-{n}", name=f"Fictional film {n}")
                for n in range(1, 51)
            ]
            for entity_id, rank in POSITIONS[anchor.entity_id].items():
                entities[rank - 1] = FEATURED[entity_id]
            lists.append(entities)
        all_entities = {e.entity_id: e for entities in lists for e in entities}
        scores = {
            entity_id: sum(
                61 / (60 + rank)
                for entities in lists
                for rank, entity in enumerate(entities, 1)
                if entity.entity_id == entity_id
            )
            for entity_id in all_entities
        }
        return [
            all_entities[entity_id]
            for entity_id in sorted(scores, key=lambda entity_id: (-scores[entity_id], entity_id))
            if entity_id not in excluded
        ][:50]
