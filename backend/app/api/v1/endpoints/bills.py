from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import tempfile
import os
import aiofiles
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.schemas.bill import Bill as BillSchema, BillCreate as BillCreateSchema
from app.services.bill_analyzer import BillAnalyzer
from app.core.config import get_settings, Settings
from app.api import deps
from app.crud.crud_bill import CRUDBill
from app.db.models.user import User
from app.db.session import get_database_session
from app.api.deps import get_google_sheets_service
from app.services.google_sheets_service import GoogleSheetsService
from app.crud.crud_user import CRUDUser

router = APIRouter()

@router.post("/analyze", response_model=BillSchema, status_code=status.HTTP_201_CREATED)
async def analyze_bill_and_create_entry(
    file: UploadFile = File(...),
    downsize: bool = False,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(deps.get_current_active_user),
    bill_repository: CRUDBill = Depends(deps.get_bill_repository)
) -> BillSchema:
    """Uses AI to extract bill data from image and saves to database"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
        async with aiofiles.open(temp_file_path, 'wb') as f:
            await f.write(content)
        
        analyzer = BillAnalyzer(settings)
        bill_create_data, _ = analyzer.analyze_image(temp_file_path, downsize=downsize)
        
        if not bill_create_data or not bill_create_data.merchant_company_name:
            bill_create_data = analyzer.analyze_image_fallback(temp_file_path)

        if not bill_create_data or not bill_create_data.merchant_company_name:
             raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract sufficient bill data from image after fallback."
            )

        bill_create_data.user_id = str(current_user.id)
        
        db_bill = await bill_repository.create_with_items(db=db, bill_in=bill_create_data)
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
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

@router.get("/{bill_id}", response_model=BillSchema)
async def read_bill(
    bill_id: str,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(deps.get_current_active_user),
    bill_repository: CRUDBill = Depends(deps.get_bill_repository)
) -> BillSchema:
    db_bill = await bill_repository.get(db, id=bill_id)
    if db_bill is None or str(db_bill.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    return db_bill

@router.put("/{bill_id}", response_model=BillSchema)
async def update_bill(
    bill_id: str,
    bill_update: BillCreateSchema,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(deps.get_current_active_user),
    bill_repository: CRUDBill = Depends(deps.get_bill_repository),
    gs_service: GoogleSheetsService = Depends(get_google_sheets_service),
    user_crud: CRUDUser = Depends(deps.get_user_repository),
) -> BillSchema:
    db_bill = await bill_repository.get(db, id=bill_id)
    if db_bill is None or str(db_bill.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    updated_bill = await bill_repository.update_with_items(db=db, db_obj=db_bill, obj_in=bill_update)
    if updated_bill.exported_to_sheets:
        access_token = await gs_service._refresh_access_token_if_needed(db, current_user, user_crud)

        row_updates = {}
        new_items = []
        bill_date = updated_bill.date or updated_bill.created_at.date().isoformat()
        bill_time = updated_bill.time or ""
        for item in updated_bill.items:
            row_values = [
                bill_date,
                bill_time,
                updated_bill.merchant_company_name or "",
                item.description or "",
                item.quantity or 1,
                item.unit_price or item.total_price_per_item or 0,
                item.total_price_per_item or (item.quantity or 1) * (item.unit_price or 0),
                updated_bill.subtotal or 0,
                updated_bill.tax or 0,
                updated_bill.discount_savings or 0,
                updated_bill.total_amount or 0,
                updated_bill.payment_method or "",
            ]
            if item.sheet_row_number:
                row_updates[item.sheet_row_number] = row_values
            else:
                new_items.append((item, row_values))

        outcomes = await gs_service.update_rows(access_token, current_user.sheets_spreadsheet_id, row_updates)

        # Append new items
        if new_items:
            append_result = await gs_service.append_rows(
                db,
                current_user,
                user_crud,
                spreadsheet_id=current_user.sheets_spreadsheet_id,
                values=[rv for (_, rv) in new_items],
                range_="A1",
            )
            sr = append_result.get("start_row_number")
            if sr is not None:
                for offset, (item, _) in enumerate(new_items):
                    item.sheet_row_number = sr + offset
        await db.commit()

    return updated_bill 

@router.post("/{bill_id}/export-to-sheets", status_code=status.HTTP_200_OK)
async def export_bill_to_google_sheets(
    bill_id: str,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(deps.get_current_active_user),
    bill_repository: CRUDBill = Depends(deps.get_bill_repository),
    user_crud: CRUDUser = Depends(deps.get_user_repository),
    gs_service: GoogleSheetsService = Depends(get_google_sheets_service),
) -> JSONResponse:
    """Append this bill's line-items to the user's Google Sheet.

    If the user has not yet created a spreadsheet, one will be created automatically.
    """

    db_bill = await bill_repository.get(db, id=bill_id)
    if db_bill is None or str(db_bill.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")

    # Already exported?
    if db_bill.exported_to_sheets:
        return JSONResponse({"success": True, "already_exported": True, "spreadsheet_id": current_user.sheets_spreadsheet_id})

    # Ensure spreadsheet ID exists; create if missing
    spreadsheet_id = current_user.sheets_spreadsheet_id
    if not spreadsheet_id:
        spreadsheet_id = await gs_service.create_spreadsheet(
            db,
            current_user,
            user_crud,
            title="Expenses",
            sheet_title="Expenses",
        )

    # Build rows from bill items
    rows = []
    bill_date = db_bill.date or db_bill.created_at.date().isoformat()
    bill_time = db_bill.time or ""
    for item in db_bill.items:
        rows.append([
            bill_date,
            bill_time,
            db_bill.merchant_company_name or "",
            item.description or "",
            item.quantity or 1,
            item.unit_price or item.total_price_per_item or 0,
            item.total_price_per_item or (item.quantity or 1) * (item.unit_price or 0),
            db_bill.subtotal or 0,
            db_bill.tax or 0,
            db_bill.discount_savings or 0,
            db_bill.total_amount or 0,
            db_bill.payment_method or "",
        ])

    result = await gs_service.append_rows(
        db,
        current_user,
        user_crud,
        spreadsheet_id=spreadsheet_id,
        values=rows,
        range_="A1",
    )

    start_row = result.get("start_row_number")
    if start_row is not None:
        for idx, item in enumerate(db_bill.items):
            item.sheet_row_number = start_row + idx
        await db.commit()

    # Mark bill as exported
    db_bill.exported_to_sheets = True
    db_bill.exported_at = datetime.now(timezone.utc)
    await db.commit()

    return JSONResponse({"success": True, "spreadsheet_id": spreadsheet_id}) 