from ..models.chunk_model import Chunk
from ..models.file_model import File
from ..models.folder_model import Folder
from ..services.plan_service import get_plan_limits, get_user_plan
class FolderController:
    @staticmethod
    def create_folder(user_id, name, description=None):
        if not user_id or not name:
            return {"error": "User ID and folder name are required"}, 400

        plan = get_user_plan(user_id)
        limits = get_plan_limits(plan)
        folder_limit = limits.get("folder_limit")
        if folder_limit is not None:
            current_count = Folder.objects(user_id=user_id).count()
            if current_count >= folder_limit:
                return {
                    "error": "Folder limit reached for current plan",
                    "plan": plan,
                    "limit": folder_limit,
                }, 403

        folder = Folder(
            user_id=user_id,
            name=name,
            description=description,
            
        )
        folder.save()
        return {"id": str(folder.id), "name": folder.name}, 201
    
    @staticmethod
    def get_folders_by_user(user_id):
        folders = Folder.objects(user_id=user_id)
        folder_list = [{"id": str(folder.id), "name": folder.name, "description": folder.description, "created_at": folder.created_at.isoformat()} for folder in folders]
        return folder_list, 200
    
    @staticmethod
    def delete_folder(folder_id):
        try:
            folder = Folder.objects(id=folder_id).first()
            if not folder:
                return {"error": "Folder not found"}, 404
            
            # Xóa files và chunks trước
            File.objects(folder_id=folder_id).delete()
            Chunk.objects(folder_id=folder_id).delete()
            
            # Xóa folder
            folder.delete()
            return {"message": "Folder deleted successfully"}, 200
        except Exception as e:
            return {"error": str(e)}, 500