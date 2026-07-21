from backend.app.services.llm.providers import RetrievalOnlyProvider, SYSTEM_PROMPT


def test_system_prompt_enforces_answer_contract():
    assert "Never invent Marvel facts" in SYSTEM_PROMPT
    assert "Separate MCU canon" in SYSTEM_PROMPT
    assert "confidence note" in SYSTEM_PROMPT


def test_retrieval_only_answer_includes_contract_sections():
    provider = RetrievalOnlyProvider()
    context = """[Kang the Conqueror] (characters, hybrid, score=0.91)
Reason: Matched semantic vector search, keyword search, or both.
Character Name: Kang the Conqueror
Aliases: Kang, Nathaniel Richards Variant
Type: Character
Biography: Kang the Conqueror is a powerful multiversal variant associated with advanced temporal technology.
Powers: Advanced temporal technology, Strategic conquest
Affiliations: Kang variants
Chronological Year: 2025
"""

    response = provider.generate("Who is Kang?", context)

    assert "**Direct Answer**" in response.content
    assert "**Continuity**" in response.content
    assert "**Sources Used**" in response.content
    assert "**Confidence**" in response.content
    assert "Kang the Conqueror" in response.content
    assert "Kang the Conqueror (characters, hybrid, score=0.91)" in response.content

