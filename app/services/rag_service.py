import numpy as np
from openai import OpenAI
from ..config import Config
from ..models.chunk_model import Chunk

# Khởi tạo client OpenAI
client = OpenAI(api_key=Config.OPENAI_API_KEY)

def ingest_meeting_transcript(sid, user_id, full_transcript):
    """
    1. Chia nhỏ transcript thành các đoạn (chunk).
    2. Gọi API Embedding của OpenAI.
    3. Lưu vào bảng Chunks (Map folder_id = sid để biết thuộc meeting nào).
    """
    if not full_transcript:
        return

    # 1. Chunking đơn giản: Tách theo dòng newline
    # Bạn có thể nâng cấp thuật toán tách câu phức tạp hơn nếu cần
    text_chunks = full_transcript.split('\n')
    # Lọc bỏ dòng quá ngắn
    text_chunks = [t.strip() for t in text_chunks if len(t.strip()) > 20]

    if not text_chunks:
        return

    try:
        # 2. Lấy Embedding (Batch request để tối ưu)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text_chunks
        )
        
        embeddings = [item.embedding for item in response.data]

        # 3. Lưu vào DB
        # Lưu ý: Ở đây ta dùng folder_id để lưu sid của cuộc họp.
        # file_id ta set là 'meeting_transcript' để phân biệt với file notebook.
        chunks_to_create = []
        for i, text in enumerate(text_chunks):
            chunk = Chunk(
                user_id=user_id,
                folder_id=sid,        # Gom nhóm theo cuộc họp
                file_id='meeting',    # Đánh dấu nguồn là meeting
                chunk_index=i,
                text=text,
                embedding=embeddings[i]
            )
            chunks_to_create.append(chunk)
        
        # Bulk insert
        Chunk.objects.insert(chunks_to_create)
        print(f"[RAG] Ingested {len(chunks_to_create)} chunks for meeting {sid}")

    except Exception as e:
        print(f"[RAG] Error ingesting meeting: {e}")

def retrieve_relevant_chunks(user_id, query, top_k=3, folder_id=None, file_id=None, max_candidates=200):
    """
    Tìm các đoạn văn bản (chunks) liên quan nhất đến câu hỏi của user.
    Hiện tại search trên toàn bộ chunks của user (gồm cả meeting và notebook).
    """
    # 1. Embed câu hỏi
    try:
        query_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        query_vector = query_response.data[0].embedding
    except Exception as e:
        print(f"[RAG] Error embedding query: {e}")
        return []

    # 2. Lấy tất cả chunks của user (nếu data ít)
    # Nếu data nhiều, bạn nên dùng Vector Database như Pinecone/Qdrant thay vì tính toán tay
    query_set = Chunk.objects(user_id=user_id)
    if folder_id:
        query_set = query_set.filter(folder_id=folder_id)
    if file_id:
        query_set = query_set.filter(file_id=file_id)

    all_chunks = query_set.limit(max_candidates)
    
    scored_chunks = []
    
    for chunk in all_chunks:
        if not chunk.embedding:
            continue
        
        # Tính Cosine Similarity
        vec_a = np.array(query_vector)
        vec_b = np.array(chunk.embedding)
        
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        
        if norm_a == 0 or norm_b == 0: continue
            
        cosine_sim = dot_product / (norm_a * norm_b)
        
        scored_chunks.append({
            "chunk": chunk,
            "score": cosine_sim
        })
    
    # 3. Sắp xếp theo điểm số giảm dần và lấy top K
    sorted_chunks = sorted(scored_chunks, key=lambda x: x['score'], reverse=True)
    return [item['chunk'] for item in sorted_chunks[:top_k]]