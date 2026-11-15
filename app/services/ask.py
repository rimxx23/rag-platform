from app.repositories.chunk import ChunkRepository
from app.schemas.ask import AnswerSchema, SourceSchema
from app.services.embedder import embed_texts
from app.services.llm import NO_ANSWER, extract_citations, generate_answer

NO_ANSWER_RESPONSE = AnswerSchema(answer=NO_ANSWER, sources=[])


async def answer_question(repository: ChunkRepository, collection_id: str, question: str) -> AnswerSchema:
    embedding = embed_texts([question])[0]
    chunks = await repository.search(collection_id, embedding)
    if not chunks:
        return NO_ANSWER_RESPONSE

    answer = await generate_answer(question, [chunk.content for chunk in chunks])
    if answer.startswith(NO_ANSWER):
        return NO_ANSWER_RESPONSE

    sources = [
        SourceSchema(
            number=number,
            document_id=chunks[number - 1].document_id,
            filename=chunks[number - 1].document.filename,
            page=chunks[number - 1].page,
            content=chunks[number - 1].content,
        )
        for number in extract_citations(answer, len(chunks))
    ]
    return AnswerSchema(answer=answer, sources=sources)
