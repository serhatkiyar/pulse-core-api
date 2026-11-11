from unittest.mock import MagicMock, patch


async def test_ask_ai_unauthorized(client):
    response = await client.post(
        "ai/ask",
        json={"question": "İlhami sel neden derslerde yavaş gidiyor?", "limit": 5},
    )

    assert response.status_code == 401


async def test_ask_ai_authorized(authorized_client):
    response = await authorized_client.post(
        "ai/ask",
        json={"question": "İlhami sel neden derslerde yavaş gidiyor?", "limit": 5},
    )

    assert response.status_code == 200


from app.schemas import RAGResponse


@patch("app.services.rag_service.client.aio.models.generate_content")
async def test_ask_ai_caching(mock_generate, authorized_client, test_posts):

    create_post_res = await authorized_client.post(
        "/posts/",
        json={
            "title": "İlhami sel derslerde yavaş ilerliyor",
            "content": "İlhami sel öğrenciler projelerini yapabilsin diye derslerin yavaş işlendiğini söylüyor.",
            "published": True,
        },
    )

    assert create_post_res.status_code == 201
    created_post = create_post_res.json()

    fake_rag_response = RAGResponse(
        thought_process=["düşünme zinciri"],
        answer="İlhami sel projenizi bitirebilin diye derslerde yavaş gidiyor.",
        enough_context=True,
        source_post_ids=[created_post["id"]],
    )

    fake_response = MagicMock()
    fake_response.text = fake_rag_response.model_dump_json()

    mock_generate.return_value = fake_response

    question = "İlhami sel neden derslerde yavaş gidiyor?"

    response1 = await authorized_client.post(
        "ai/ask", json={"question": question, "limit": 5}
    )

    assert response1.status_code == 200
    assert (
        response1.json()["answer"]
        == "İlhami sel projenizi bitirebilin diye derslerde yavaş gidiyor."
    )
    assert mock_generate.call_count == 1

    response2 = await authorized_client.post(
        "ai/ask",
        json={"question": "İlhami sel neden derslerde yavaş gidiyor?", "limit": 5},
    )

    assert response2.status_code == 200
    assert (
        response2.json()["answer"]
        == "İlhami sel projenizi bitirebilin diye derslerde yavaş gidiyor."
    )
    assert mock_generate.call_count == 1
