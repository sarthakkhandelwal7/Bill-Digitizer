from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import tempfile
import os
import aiofiles
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import logging
import uuid

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
    import logging
    logging.getLogger(__name__).info("Received bill update data: %s", bill_update.model_dump())
    db_bill = await bill_repository.get(db, id=bill_id)
    if db_bill is None or str(db_bill.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    # Capture current values of each row before mutation for diffing later
    def _build_row_values(bill_obj, item_obj):
        """Helper – build Google-Sheets row array from bill + item objects."""
        bill_date_local = bill_obj.date or bill_obj.created_at.date().isoformat()
        bill_time_local = bill_obj.time or ""
        return [
            bill_date_local,
            bill_time_local,
            bill_obj.merchant_company_name or "",
            item_obj.description or "",
            item_obj.quantity or 1,
            item_obj.unit_price or item_obj.total_price_per_item or 0,
            item_obj.total_price_per_item or (item_obj.quantity or 1) * (item_obj.unit_price or 0),
            bill_obj.subtotal or 0,
            bill_obj.tax or 0,
            bill_obj.discount_savings or 0,
            bill_obj.total_amount or 0,
            bill_obj.payment_method or "",
        ]

    old_item_snap: Dict[str, List] = {}
    if db_bill.exported_to_sheets:
        logging.getLogger(__name__).info("Bill %s is exported_to_sheets, capturing old snapshot", bill_id)
        for it in db_bill.items:
            if it.sheet_item_id:
                old_values = _build_row_values(db_bill, it)
                old_values.append(it.sheet_item_id)  # Add ID to the end
                old_item_snap[it.sheet_item_id] = old_values
                logging.getLogger(__name__).info("Captured old item %s: %s", it.sheet_item_id, old_values)
        logging.getLogger(__name__).info("Old snapshot complete: %s items captured", len(old_item_snap))

    # Perform DB update (this commits internally)
    logging.getLogger(__name__).info("About to update bill. Items before update:")
    for it in db_bill.items:
        logging.getLogger(__name__).info("  Item %s: description='%s' sheet_item_id=%s", it.id, it.description, it.sheet_item_id)
    
    await bill_repository.update_with_items(db=db, db_obj=db_bill, obj_in=bill_update)
    
    # Update bill fields from input
    bill_data = bill_update.model_dump(exclude={'items_services_purchased', 'user_id'})
    for field, value in bill_data.items():
        if value is not None:
            setattr(db_bill, field, value)
    
    logging.getLogger(__name__).info("After update. Items from input payload:")
    for item_data in bill_update.items_services_purchased:
        logging.getLogger(__name__).info("  Item payload: description='%s' sheet_item_id=%s", item_data.description, item_data.sheet_item_id)

    # After update, decide what needs to be sent to Sheets
    if db_bill.exported_to_sheets:
        logging.getLogger(__name__).info("Bill %s is still exported_to_sheets, checking for changes", bill_id)
        access_token = await gs_service._refresh_access_token_if_needed(db, current_user, user_crud)

        diff_item_updates: Dict[str, List] = {}
        missing_items: List[str] = []
        
        # Get all new item IDs for comparison
        new_item_ids = set()
        for item_data in bill_update.items_services_purchased:
            if item_data.sheet_item_id:
                new_item_ids.add(item_data.sheet_item_id)

        # Find deleted items (items that were in old snapshot but not in new payload)
        old_item_ids = set(old_item_snap.keys())
        deleted_item_ids = old_item_ids - new_item_ids
        
        if deleted_item_ids:
            logging.getLogger(__name__).info("Detected %s deleted items: %s", len(deleted_item_ids), deleted_item_ids)
            try:
                delete_results = await gs_service.delete_rows_by_id(
                    access_token,
                    current_user.sheets_spreadsheet_id,
                    list(deleted_item_ids)
                )
                logging.getLogger(__name__).info("Google Sheets deletion results: %s", delete_results)
                
                # Check if any deletions failed
                failed_deletions = [item_id for item_id, success in delete_results.items() if not success]
                if failed_deletions:
                    logging.getLogger(__name__).warning("Failed to delete items from Google Sheets: %s", failed_deletions)
            except Exception as e:
                logging.getLogger(__name__).error("Error deleting items from Google Sheets: %s", str(e))
                # Continue with updates even if deletion fails

        # Use the input payload items instead of querying DB
        for item_data in bill_update.items_services_purchased:
            if not item_data.sheet_item_id:
                missing_items.append(f"item_{item_data.description or 'unknown'}")
                continue

            # Build new values from the updated bill + item payload
            new_values = [
                db_bill.date or db_bill.created_at.date().isoformat(),
                db_bill.time or "",
                db_bill.merchant_company_name or "",
                item_data.description or "",
                item_data.quantity or 1,
                item_data.unit_price or item_data.total_price_per_item or 0,
                item_data.total_price_per_item or (item_data.quantity or 1) * (item_data.unit_price or 0),
                db_bill.subtotal or 0,
                db_bill.tax or 0,
                db_bill.discount_savings or 0,
                db_bill.total_amount or 0,
                db_bill.payment_method or "",
                item_data.sheet_item_id,  # Add ID to the end
            ]
            old_values = old_item_snap.get(item_data.sheet_item_id)
            logging.getLogger(__name__).info(
                "Item %s comparison: old=%s new=%s equal=%s", 
                item_data.sheet_item_id, old_values, new_values, old_values == new_values
            )
            # If item didn't exist before or values changed, include in diff
            if old_values is None or new_values != old_values:
                logging.getLogger(__name__).info("Item %s CHANGE DETECTED", item_data.sheet_item_id)
                diff_item_updates[item_data.sheet_item_id] = new_values

        logging.getLogger(__name__).info("Diff complete: %s items to update", len(diff_item_updates))
        if diff_item_updates:
            logging.getLogger(__name__).info("Calling Google Sheets update for items: %s", list(diff_item_updates.keys()))
            try:
                result = await gs_service.update_rows_by_id(access_token, current_user.sheets_spreadsheet_id, diff_item_updates)
                logging.getLogger(__name__).info("Google Sheets update result: %s", result)
            except Exception as e:
                logging.getLogger(__name__).error("Google Sheets update failed: %s", str(e))
                raise
        else:
            logging.getLogger(__name__).info("No items to update in Google Sheets")

        if missing_items:
            logging.getLogger(__name__).info(
                "Line items not synced to Sheets due to missing item IDs: %s", missing_items
            )

        await db.commit()

    return db_bill 

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
        # Generate unique ID for this item if it doesn't have one
        if not item.sheet_item_id:
            item.sheet_item_id = str(uuid.uuid4())
        
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
            item.sheet_item_id,  # Add unique ID to the end
        ])

    result = await gs_service.append_rows(
        db,
        current_user,
        user_crud,
        spreadsheet_id=spreadsheet_id,
        values=rows,
        range_="A1",
    )

    # The item IDs are already set above, just commit them
    await db.commit()

    # Mark bill as exported
    db_bill.exported_to_sheets = True
    db_bill.exported_at = datetime.now(timezone.utc)
    await db.commit()

    return JSONResponse({"success": True, "spreadsheet_id": spreadsheet_id})

@router.delete("/{bill_id}", status_code=status.HTTP_200_OK)
async def delete_bill(
    bill_id: str,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(deps.get_current_active_user),
    bill_repository: CRUDBill = Depends(deps.get_bill_repository),
    user_crud: CRUDUser = Depends(deps.get_user_repository),
    gs_service: GoogleSheetsService = Depends(get_google_sheets_service),
) -> JSONResponse:
    """Delete a bill and remove its items from Google Sheets if exported."""
    import logging
    
    # Get the bill with its line items
    db_bill = await bill_repository.get(db, id=bill_id)
    if db_bill is None or str(db_bill.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    # If the bill was exported to sheets, remove the rows from Google Sheets
    if db_bill.exported_to_sheets and current_user.sheets_spreadsheet_id:
        logging.getLogger(__name__).info("Bill %s was exported to sheets, removing from Google Sheets", bill_id)
        
        # Collect all sheet item IDs
        sheet_item_ids = []
        for item in db_bill.items:
            if item.sheet_item_id:
                sheet_item_ids.append(item.sheet_item_id)
        
        if sheet_item_ids:
            logging.getLogger(__name__).info("Removing %s items from Google Sheets: %s", len(sheet_item_ids), sheet_item_ids)
            try:
                access_token = await gs_service._refresh_access_token_if_needed(db, current_user, user_crud)
                delete_results = await gs_service.delete_rows_by_id(
                    access_token,
                    current_user.sheets_spreadsheet_id,
                    sheet_item_ids
                )
                logging.getLogger(__name__).info("Google Sheets deletion results: %s", delete_results)
                
                # Check if any deletions failed
                failed_deletions = [item_id for item_id, success in delete_results.items() if not success]
                if failed_deletions:
                    logging.getLogger(__name__).warning("Failed to delete items from Google Sheets: %s", failed_deletions)
                    # Note: We continue with database deletion even if Google Sheets deletion fails
                    # This prevents orphaned data in the database
            except Exception as e:
                logging.getLogger(__name__).error("Error deleting items from Google Sheets: %s", str(e))
                # Continue with database deletion even if Google Sheets deletion fails
    
    # Delete the bill from the database
    deleted_bill = await bill_repository.remove(db, id=bill_id)
    if deleted_bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    logging.getLogger(__name__).info("Successfully deleted bill %s", bill_id)
    return JSONResponse({"success": True, "message": "Bill deleted successfully"}) 