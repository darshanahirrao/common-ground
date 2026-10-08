from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Anchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    source: Literal["qloo", "synthetic"]


class Member(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=40)
    anchors: list[Anchor] = Field(min_length=1, max_length=3)


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["qloo", "synthetic"]
    members: list[Member] = Field(min_length=2, max_length=6)
    veto_ids: list[str] = Field(default_factory=list, max_length=100)
    require_everyone: bool = True

    @model_validator(mode="after")
    def validate_members(self):
        names = [member.name.strip().casefold() for member in self.members]
        if any(not name for name in names) or len(set(names)) != len(names):
            raise ValueError("Give each person a distinct, non-empty name.")
        for member in self.members:
            member.name = member.name.strip()
            for anchor in member.anchors:
                if anchor.source != self.source:
                    raise ValueError("Preview and Qloo anchors cannot be mixed.")
                if self.source == "qloo":
                    anchor.entity_id = str(UUID(anchor.entity_id))
            ids = [anchor.entity_id for anchor in member.anchors]
            if len(set(ids)) != len(ids):
                raise ValueError("A person's anchors must be distinct.")
        if self.source == "qloo":
            self.veto_ids = [str(UUID(entity_id)) for entity_id in self.veto_ids]
        return self


class Entity(BaseModel):
    entity_id: str
    name: str
    image_url: str | None = None
    preview_art: int | None = None
