"""Opt-in real stdio verification. Prints only pass/fail counts, never Qloo datasets."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters


def tool_data(result):
    if result.is_error:
        raise RuntimeError("Live MCP tool failed; no response data was printed.")
    if result.structured_content is not None:
        return result.structured_content
    texts = [block.text for block in result.content if block.type == "text"]
    if len(texts) != 1:
        raise RuntimeError("Unexpected MCP response format.")
    return json.loads(texts[0])


async def verify(key):
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "common_ground.mcp_server"],
        env=dict(os.environ, QLOO_API_KEY=key),
        cwd=Path(__file__).resolve().parents[1],
    )
    async with Client(server, cache=None, read_timeout_seconds=90) as host:
        tools = await host.list_tools()
        assert {tool.name for tool in tools.tools} == {
            "search_cultural_anchors",
            "plan_movie_night",
        }
        members = []
        # Fictional participants and explicit film identities, not inferred user preferences.
        for person, title, year in [("Asha", "Interstellar", 2014), ("Leo", "Inception", 2010)]:
            data = tool_data(await host.call_tool("search_cultural_anchors", {"query": title}))
            anchor = next(
                a
                for a in data["results"]
                if (
                    a["name"] == title
                    and a["entity_type"] == "urn:entity:movie"
                    and a["release_year"] == year
                )
            )
            members.append({"name": person, "anchors": [anchor]})
        plan = tool_data(
            await host.call_tool(
                "plan_movie_night",
                {
                    "members": members,
                    "require_everyone": True,
                },
            )
        )
        assert plan["source"] == "qloo" and plan["status"] == "ready"
        assert plan["candidates"] and all(c["coverage"] == 2 for c in plan["candidates"])
        assert all(c["entity_id"] not in plan["excluded_ids"] for c in plan["candidates"])
        veto = plan["candidates"][0]["entity_id"]
        replacement = tool_data(
            await host.call_tool(
                "plan_movie_night",
                {
                    "members": members,
                    "veto_ids": [veto],
                    "require_everyone": True,
                },
            )
        )
        assert replacement["status"] == "ready" and replacement["people"] == plan["people"]
        assert all(c["entity_id"] != veto for c in replacement["candidates"])
        print(
            json.dumps(
                {
                    "transport": "stdio",
                    "source": "qloo",
                    "search_tools": 2,
                    "planning_tools": 2,
                    "represented_people": 2,
                    "candidate_count": len(plan["candidates"]),
                    "veto_replan": "passed",
                }
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args()
    key = (
        json.loads(args.key_file.read_text())["apiKey"]
        if args.key_file
        else os.environ.get("QLOO_API_KEY")
    )
    if not key:
        parser.error("Set QLOO_API_KEY privately or supply a private --key-file.")
    asyncio.run(verify(key))
