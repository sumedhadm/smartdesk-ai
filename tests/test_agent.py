from agent import SmartDeskAgent


def make_agent(monkeypatch, store=None):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    return SmartDeskAgent(store if store is not None else [])


def test_unknown_tool_rejected(monkeypatch):
    agent = make_agent(monkeypatch)
    r = agent._execute_tool("delete_everything", {})
    assert r["status"] == "error"


def test_create_task_via_registry(monkeypatch):
    store = []
    agent = make_agent(monkeypatch, store)
    r = agent._execute_tool("create_task", {"task_description": "Write README"})
    assert r["status"] == "ok" and len(store) == 1


def test_bad_args_handled(monkeypatch):
    agent = make_agent(monkeypatch)
    r = agent._execute_tool("create_task", {})
    assert r["status"] == "error"


def test_empty_message(monkeypatch):
    agent = make_agent(monkeypatch)
    assert "Please type" in agent.chat("   ")["reply"]