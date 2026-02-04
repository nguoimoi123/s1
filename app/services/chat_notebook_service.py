import math
from openai import OpenAI
import os
from dotenv import load_dotenv
from ..models.chunk_model import Chunk
from ..services.usage_service import check_and_increment_qa

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def cosine_similarity(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2)

def get_embedding(text):
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return res.data[0].embedding
class ChatNotebookController:
    @staticmethod
    def chat_bot_notebook(user_id, folder_id, question, file_ids=None, top_k=5):
        if not all([user_id, folder_id, question]):
            return {"error": "Missing required fields"}, 400

        allowed, error = check_and_increment_qa(user_id)
        if not allowed:
            return {"error": error or "Q&A limit reached"}, 403
        
        # Embedding câu hỏi
        question_embedding = get_embedding(question)

        # Lấy chunk trong folder
        query = Chunk.objects(
            user_id=user_id,
            folder_id=folder_id
        )

        if isinstance(file_ids, list) and len(file_ids) > 0:
            query = query.filter(file_id__in=file_ids)

        chunks = query
        
        # Tính similarity
        scored_chunks = []
        for chunk in chunks:
            score = cosine_similarity(question_embedding, chunk.embedding)
            scored_chunks.append((score, chunk.text))
        
        # Top K chunk
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        top_chunks = scored_chunks[:top_k]

        # Ghép context
        context = "\n\n".join([text for _, text in top_chunks])

        # chat với openai
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là 1 chuyên gia giải thích phân tích nội dung dự trên notebook người dùng."
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {question}"
                }
            ],
            max_tokens=200,
            temperature=0.2
        )
        answer = completion.choices[0].message.content
        return {
            "answer": answer,
        }, 200
