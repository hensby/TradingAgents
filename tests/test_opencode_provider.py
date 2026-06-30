"""Tests for OpenCode Go provider integration."""

from __future__ import annotations

import pytest

from tradingagents.llm_clients.factory import create_llm_client


@pytest.mark.unit
def test_factory_routes_opencode_to_openai_compatible_client():
    client = create_llm_client(provider="opencode", model="kimi-k2.5")

    assert client.__class__.__name__ == "OpenAIClient"
    assert client.provider == "opencode"
    assert client.model == "kimi-k2.5"


@pytest.mark.unit
def test_opencode_client_uses_chat_completions_not_responses_api(monkeypatch):
    import tradingagents.llm_clients.openai_client as mod

    monkeypatch.setenv("OPENCODE_API_KEY", "sk-opencode-test")

    llm = mod.OpenAIClient(model="provider/model-id", provider="opencode").get_llm()

    assert isinstance(llm, mod.NormalizedChatOpenAI)
    assert llm.model_name == "provider/model-id"
    assert str(llm.openai_api_base) == "https://opencode.ai/zen/go/v1"
    assert llm.use_responses_api is not True


@pytest.mark.unit
def test_opencode_explicit_base_url_overrides_default(monkeypatch):
    import tradingagents.llm_clients.openai_client as mod

    monkeypatch.setenv("OPENCODE_API_KEY", "sk-opencode-test")
    llm = mod.OpenAIClient(
        model="provider/model-id",
        provider="opencode",
        base_url="https://proxy.example.test/v1",
    ).get_llm()

    assert str(llm.openai_api_base) == "https://proxy.example.test/v1"
