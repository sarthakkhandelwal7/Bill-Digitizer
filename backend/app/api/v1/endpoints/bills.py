from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import tempfile
import os
from typing import List

from app.schemas.bill import Bill as BillSchema, BillCreate as BillCreateSchema # Renamed for clarity
from app.services.bill_analyzer import BillAnalyzer
from app.core.config import get_settings, Settings
# Import DB session and CRUD operations
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.crud import crud_bill # Using the __init__.py import

router = APIRouter()

@router.post("/analyze", response_model=BillSchema, status_code=status.HTTP_201_CREATED)
async def analyze_bill_and_create_entry(
    file: UploadFile = File(...),
    downsize: bool = False,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db) # DB session injected
) -> BillSchema:
    """
    Analyze a bill/receipt image, extract structured data, and create a new bill entry in the database.
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        analyzer = BillAnalyzer(settings)
        bill_create_data, _ = analyzer.analyze_image(temp_file_path, downsize=downsize)
        
        if not bill_create_data or not bill_create_data.merchant_company_name:
            bill_create_data = analyzer.analyze_image_fallback(temp_file_path)

        if not bill_create_data or not bill_create_data.merchant_company_name: # Check again after fallback
             raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract sufficient bill data from image after fallback."
            )

        # Create bill entry in the database using CRUD operation
        db_bill = crud_bill.bill.create_with_items(db=db, bill_in=bill_create_data)
        return db_bill # FastAPI will convert this DB model to BillSchema
        
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
            os.unlink(temp_file_path)

@router.get("", response_model=List[BillSchema])
async def read_bills(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[BillSchema]:
    """Retrieve a list of bills from the database."""
    bills = crud_bill.bill.get_multi(db, skip=skip, limit=limit)
    return bills

@router.get("/{bill_id}", response_model=BillSchema)
async def read_bill(
    bill_id: int,
    db: Session = Depends(get_db)
) -> BillSchema:
    """Retrieve a specific bill by its ID from the database."""
    db_bill = crud_bill.bill.get(db, id=bill_id)
    if db_bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    return db_bill

@router.put("/{bill_id}", response_model=BillSchema)
async def update_bill(
    bill_id: int,
    bill_update: BillCreateSchema,  # Reusing BillCreateSchema for updates
    db: Session = Depends(get_db)
) -> BillSchema:
    """Update a specific bill by its ID."""
    db_bill = crud_bill.bill.get(db, id=bill_id)
    if db_bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    # Update the bill with new data
    updated_bill = crud_bill.bill.update_with_items(db=db, db_obj=db_bill, obj_in=bill_update)
    return updated_bill 