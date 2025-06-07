from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import tempfile
import os
import aiofiles
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.bill import Bill as BillSchema, BillCreate as BillCreateSchema
from app.services.bill_analyzer import BillAnalyzer
from app.core.config import get_settings, Settings
from app.api import deps
from app.crud.crud_bill import CRUDBill
from app.db.models.user import User
from app.db.session import get_async_db

router = APIRouter()

@router.post("/analyze", response_model=BillSchema, status_code=status.HTTP_201_CREATED)
async def analyze_bill_and_create_entry(
    file: UploadFile = File(...),
    downsize: bool = False,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(deps.get_current_active_user),
    bill_crud: CRUDBill = Depends(deps.get_bill_crud)
) -> BillSchema:
    """Uses AI to extract bill data from image and saves to database"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    temp_file_path = None
    try:
        # Create temporary file with async file operations
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            
        # Write file content asynchronously
        async with aiofiles.open(temp_file_path, 'wb') as f:
            await f.write(content)
        
        analyzer = BillAnalyzer(settings)
        bill_create_data, _ = await analyzer.analyze_image(temp_file_path, downsize=downsize)
        
        if not bill_create_data or not bill_create_data.merchant_company_name:
            bill_create_data = await analyzer.analyze_image_fallback(temp_file_path)

        if not bill_create_data or not bill_create_data.merchant_company_name:
             raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract sufficient bill data from image after fallback."
            )

        bill_create_data.user_id = str(current_user.id)
        
        # Now fully async - no more mixed async/sync pattern
        db_bill = await bill_crud.create_with_items(db=db, bill_in=bill_create_data)
        return db_bill
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unhandled error in /analyze endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing the image: {str(e)}"
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

@router.get("", response_model=List[BillSchema])
async def read_bills(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(deps.get_current_active_user),
    bill_crud: CRUDBill = Depends(deps.get_bill_crud)
) -> List[BillSchema]:
    bills = await bill_crud.get_multi_by_owner(db, owner_id=str(current_user.id), skip=skip, limit=limit)
    return bills

@router.get("/{bill_id}", response_model=BillSchema)
async def read_bill(
    bill_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(deps.get_current_active_user),
    bill_crud: CRUDBill = Depends(deps.get_bill_crud)
) -> BillSchema:
    db_bill = await bill_crud.get(db, id=bill_id)
    if db_bill is None or str(db_bill.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    return db_bill

@router.put("/{bill_id}", response_model=BillSchema)
async def update_bill(
    bill_id: str,
    bill_update: BillCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(deps.get_current_active_user),
    bill_crud: CRUDBill = Depends(deps.get_bill_crud)
) -> BillSchema:
    db_bill = await bill_crud.get(db, id=bill_id)
    if db_bill is None or str(db_bill.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    updated_bill = await bill_crud.update_with_items(db=db, db_obj=db_bill, obj_in=bill_update)
    return updated_bill 