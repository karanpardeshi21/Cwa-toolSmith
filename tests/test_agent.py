
import agent


def test_agent_reuses_existing_tool(monkeypatch):
    """Agent should reuse a retrieved tool instead of generating another."""

    existing_tool = {
        "name": "adds_two_numbers_tool",
        "version": 4,
        "description": "Adds two numbers and returns their sum.",
        "similarity_score": 0.62,
    }

    def fake_retrieve_tools(task, top_k=3):
        return [existing_tool]

    def fail_if_generated(task):
        raise AssertionError("Agent should not generate a duplicate tool")

    monkeypatch.setattr(agent, "retrieve_tools", fake_retrieve_tools)
    monkeypatch.setattr(agent, "generate_tool", fail_if_generated)

    result = agent.process_task("Build a calculator that sums two numeric values")

    assert result["status"] == "existing_tools_found"
    assert result["tools"][0]["name"] == "adds_two_numbers_tool"
