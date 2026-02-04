from ..models.chunk_model import Chunk

class ChunkController:
    @staticmethod
    def create_chunk(user_id, folder_id, file_id, chunk_index, text, embedding):
        if not all([user_id, folder_id, file_id, chunk_index is not None, text, embedding]):
            return {"error": "All chunk details are required"}, 400
        chunk = Chunk(
            user_id=user_id,
            folder_id=folder_id,
            file_id=file_id,
            chunk_index=chunk_index,
            text=text,
            embedding=embedding
        )
        chunk.save()
        return {"id": str(chunk.id), "chunk_index": chunk.chunk_index}, 201
    @staticmethod
    def get_chunks_by_folder(folder_id):
        chunks = Chunk.objects(folder_id=folder_id)
        chunk_list = [{"id": str(chunk.id), "chunk_index": chunk.chunk_index, "text": chunk.text, "embedding": chunk.embedding, "created_at": chunk.created_at.isoformat()} for chunk in chunks]
        return chunk_list, 200