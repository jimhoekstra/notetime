import requests
import numpy as np
from pydantic import BaseModel, Field


EMBEDDINGS_URL = "http://localhost:9931/v1/embeddings"


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class Embedding(BaseModel):
    embedding: list[float] = Field(repr=False)
    index: int

    def as_numpy_array(self) -> np.ndarray:
        return np.array(self.embedding)


class EmbeddingsUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingsResponse(BaseModel):
    model: str
    usage: EmbeddingsUsage
    data: list[Embedding]


def call_embeddings_endpoint_sync(
    documents: list[str]
) -> EmbeddingsResponse:
    response = requests.post(
        url=EMBEDDINGS_URL,
        json={
            "model": "ggml-org/embeddinggemma-2-GGUF:BF16",
            "input": documents,
        },
        headers={"Content-Type": "application/json"},
    )

    response.raise_for_status()
    response_json = response.json()

    parsed_response = EmbeddingsResponse.model_validate(response_json)
    return parsed_response


class RetrievalResult(BaseModel):
    rank: int
    score: float
    document: str
    index: int


def retrieve(query: str, documents: list[str], top_n: int) -> list[RetrievalResult]:
    query_embedding = call_embeddings_endpoint_sync(documents=[query])
    assert len(query_embedding.data) == 1

    document_embeddings = call_embeddings_endpoint_sync(documents=documents)

    results: list[RetrievalResult] = []

    for document_embedding in document_embeddings.data:
        similarity = cosine_similarity(
            query_embedding.data[0].as_numpy_array(), 
            document_embedding.as_numpy_array(),
        )

        results.append(
            RetrievalResult(
                rank=-1,
                score=similarity,
                document=documents[document_embedding.index],
                index=document_embedding.index,
            )
        )

    sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
    for idx in range(len(results)):
        sorted_results[idx].rank = idx + 1

    return sorted_results[:top_n]
 