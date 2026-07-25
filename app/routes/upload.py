from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.storage_service import storage_service
from app.utilities.file_validation import file_validator
from app.models.upload import UploadResponse

router = APIRouter(tags=["upload"])

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Validate file size & type
    try:
        file_validator.validate(file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Save the file
    try:
        saved_info = await storage_service.save_file(file)
        return UploadResponse(
            filename=saved_info["filename"],
            file_size=saved_info["size"],
            saved_path=saved_info["path"],
            status="success",
            message="File uploaded and validated successfully."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file: {str(e)}"
        )
