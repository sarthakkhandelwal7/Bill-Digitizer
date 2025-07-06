from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.user import User
from app.crud.crud_user import CRUDUser

settings = get_settings()

GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
SHEETS_BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"
HEADER_ROW = [
    "Date",
    "Time",
    "Merchant",
    "Product Name",
    "Quantity",
    "Unit Price",
    "Item Total",
    "Subtotal",
    "Tax",
    "Discount",
    "Grand Total",
    "Payment Method",
    "ID",  # Hidden unique identifier column (last column to avoid user curiosity)
]

class GoogleSheetsService:
    """Helper service for interacting with Google Sheets on behalf of a user."""

    async def _refresh_access_token_if_needed(
        self,
        db: AsyncSession,
        user: User,
        user_crud: CRUDUser,
        buffer_seconds: int = 60,
    ) -> str:
        """Return a valid access token, refreshing if it is close to expiry.

        If the stored access token expires within *buffer_seconds*, we refresh it
        using the user's refresh token and persist the new token / expiry on the
        user model.
        """
        if (
            not user.google_access_token
            or not user.google_token_expiry
            or (user.google_token_expiry - datetime.now(timezone.utc)).total_seconds()
            < buffer_seconds
        ):
            if not user.google_refresh_token:
                raise ValueError("User does not have a refresh token stored; cannot refresh.")

            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": user.google_refresh_token,
            }
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(GOOGLE_TOKEN_ENDPOINT, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})

            if resp.status_code != 200:
                raise RuntimeError(f"Failed to refresh token: {resp.text}")

            payload = resp.json()
            user.google_access_token = payload.get("access_token")
            # Google may or may not send expires_in on refresh; default 1h
            expires_in = payload.get("expires_in", 3600)
            user.google_token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            # Persist changes
            await user_crud.update(
                db,
                db_obj=user,
                obj_in={
                    "google_access_token": user.google_access_token,
                    "google_token_expiry": user.google_token_expiry,
                },
            )

        return user.google_access_token

    async def append_rows(
        self,
        db: AsyncSession,
        user: User,
        user_crud: CRUDUser,
        spreadsheet_id: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
        range_: str = "A1",
    ) -> Dict[str, Any]:
        """Append rows to the given spreadsheet.

        Returns Google Sheets API append response.
        """
        access_token = await self._refresh_access_token_if_needed(db, user, user_crud)
        url = f"{SHEETS_BASE_URL}/{spreadsheet_id}/values/{range_}:append"
        params = {"valueInputOption": value_input_option}
        body = {"values": values}

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                url,
                params=params,
                json=body,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to append rows: {resp.text}")

        result = resp.json()
        # Try to parse the starting row number for later tracking
        start_row = None
        try:
            updated_range = result.get("updates", {}).get("updatedRange")
            # e.g. "Sheet1!A8:L10" -> extract 8
            if updated_range and "!" in updated_range and ":" in updated_range:
                start = updated_range.split("!")[1].split(":")[0]  # A8
                row_part = ''.join(filter(str.isdigit, start))
                start_row = int(row_part) if row_part else None
        except Exception:
            start_row = None
        result["start_row_number"] = start_row
        return result

    async def update_rows(
        self,
        access_token: str,
        spreadsheet_id: str,
        row_updates: Dict[int, List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Dict[int, bool]:
        """Overwrite existing rows. Returns dict row_number -> success bool."""
        outcomes: Dict[int, bool] = {}
        async with httpx.AsyncClient(timeout=20) as client:
            for row_num, row_values in row_updates.items():
                range_ = f"A{row_num}:M{row_num}"  # Now includes ID column (A-M instead of A-L)
                url = f"{SHEETS_BASE_URL}/{spreadsheet_id}/values/{range_}"
                params = {"valueInputOption": value_input_option}
                body = {"values": [row_values]}
                resp = await client.put(
                    url,
                    params=params,
                    json=body,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                logging.getLogger(__name__).info(
                    "PUT row %s – status %s – body %s",
                    row_num, resp.status_code, resp.text[:200],
                )
                outcomes[row_num] = resp.status_code in (200, 201)
        return outcomes

    async def find_row_by_id(
        self,
        access_token: str,
        spreadsheet_id: str,
        item_id: str,
    ) -> Optional[int]:
        """Find the row number for a given item ID. Returns None if not found."""
        logging.getLogger(__name__).info("Searching for item ID %s in spreadsheet %s", item_id, spreadsheet_id)
        url = f"{SHEETS_BASE_URL}/{spreadsheet_id}/values/M:M"  # Get all values in column M (ID column - last column)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        
        logging.getLogger(__name__).info("GET column M response: status=%s", resp.status_code)
        if resp.status_code != 200:
            logging.getLogger(__name__).warning("Failed to get column M: %s", resp.text)
            return None
            
        data = resp.json()
        values = data.get("values", [])
        logging.getLogger(__name__).info("Found %s rows in column M", len(values))
        
        # Find the row containing our item_id (skip header row at index 0)
        for row_index, row_data in enumerate(values[1:], start=2):  # Start at row 2 (index 1 + 1)
            logging.getLogger(__name__).info("Row %s data: %s", row_index, row_data)
            if row_data and len(row_data) > 0 and row_data[0] == item_id:
                logging.getLogger(__name__).info("Found item ID %s at row %s", item_id, row_index)
                return row_index
        
        logging.getLogger(__name__).warning("Item ID %s not found in any row", item_id)
        return None

    async def update_rows_by_id(
        self,
        access_token: str,
        spreadsheet_id: str,
        id_updates: Dict[str, List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Dict[str, bool]:
        """Update rows by finding them by ID first. Returns dict item_id -> success bool."""
        logging.getLogger(__name__).info("Starting update_rows_by_id for %s items", len(id_updates))
        outcomes: Dict[str, bool] = {}
        
        for item_id, row_values in id_updates.items():
            logging.getLogger(__name__).info("Processing item ID %s with values: %s", item_id, row_values)
            # Find the current row for this item ID
            row_num = await self.find_row_by_id(access_token, spreadsheet_id, item_id)
            
            if row_num is None:
                logging.getLogger(__name__).warning("Item ID %s not found in spreadsheet", item_id)
                outcomes[item_id] = False
                continue
            
            logging.getLogger(__name__).info("Found item ID %s at row %s, updating...", item_id, row_num)
            # Update the row
            range_ = f"A{row_num}:M{row_num}"  # Include ID column (A-M)
            url = f"{SHEETS_BASE_URL}/{spreadsheet_id}/values/{range_}"
            params = {"valueInputOption": value_input_option}
            body = {"values": [row_values]}
            
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.put(
                    url,
                    params=params,
                    json=body,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
            
            logging.getLogger(__name__).info(
                "PUT item %s at row %s – status %s – body %s",
                item_id, row_num, resp.status_code, resp.text[:200],
            )
            outcomes[item_id] = resp.status_code in (200, 201)
            
        logging.getLogger(__name__).info("update_rows_by_id completed with outcomes: %s", outcomes)
        return outcomes

    async def delete_rows_by_id(
        self,
        access_token: str,
        spreadsheet_id: str,
        item_ids: List[str],
    ) -> Dict[str, bool]:
        """Delete rows by finding them by ID first. Returns dict item_id -> success bool."""
        logging.getLogger(__name__).info("Starting delete_rows_by_id for %s items", len(item_ids))
        outcomes: Dict[str, bool] = {}
        
        # First, find all row numbers for the given item IDs
        rows_to_delete = []
        for item_id in item_ids:
            logging.getLogger(__name__).info("Finding row for item ID %s", item_id)
            row_num = await self.find_row_by_id(access_token, spreadsheet_id, item_id)
            
            if row_num is None:
                logging.getLogger(__name__).warning("Item ID %s not found in spreadsheet", item_id)
                outcomes[item_id] = False
                continue
            
            rows_to_delete.append((item_id, row_num))
            logging.getLogger(__name__).info("Found item ID %s at row %s", item_id, row_num)
        
        # Sort by row number in descending order to avoid index shifting issues
        rows_to_delete.sort(key=lambda x: x[1], reverse=True)
        
        # Get sheet ID for batchUpdate requests
        sheet_id = await self._get_sheet_id(access_token, spreadsheet_id)
        if sheet_id is None:
            logging.getLogger(__name__).error("Could not get sheet ID for spreadsheet %s", spreadsheet_id)
            for item_id in item_ids:
                outcomes[item_id] = False
            return outcomes
        
        # Delete rows using batchUpdate
        delete_requests = []
        for item_id, row_num in rows_to_delete:
            delete_requests.append({
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": row_num - 1,  # Convert to 0-based index
                        "endIndex": row_num,        # Exclusive end
                    }
                }
            })
        
        if delete_requests:
            url = f"{SHEETS_BASE_URL}/{spreadsheet_id}:batchUpdate"
            body = {"requests": delete_requests}
            
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    url,
                    json=body,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
            
            logging.getLogger(__name__).info(
                "DELETE batch request – status %s – body %s",
                resp.status_code, resp.text[:200],
            )
            
            if resp.status_code in (200, 201):
                for item_id, _ in rows_to_delete:
                    outcomes[item_id] = True
            else:
                for item_id, _ in rows_to_delete:
                    outcomes[item_id] = False
        
        logging.getLogger(__name__).info("delete_rows_by_id completed with outcomes: %s", outcomes)
        return outcomes

    async def _get_sheet_id(
        self,
        access_token: str,
        spreadsheet_id: str,
    ) -> Optional[int]:
        """Get the sheet ID for the first sheet in the spreadsheet."""
        url = f"{SHEETS_BASE_URL}/{spreadsheet_id}"
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        
        if resp.status_code != 200:
            logging.getLogger(__name__).warning("Failed to get spreadsheet info: %s", resp.text)
            return None
        
        data = resp.json()
        sheets = data.get("sheets", [])
        if not sheets:
            return None
        
        return sheets[0]["properties"]["sheetId"]

    async def create_spreadsheet(
        self,
        db: AsyncSession,
        user: User,
        user_crud: CRUDUser,
        title: str,
        sheet_title: Optional[str] = None,
    ) -> str:
        """Create a new Google Sheets spreadsheet with protected ID column."""
        access_token = await self._refresh_access_token_if_needed(db, user, user_crud)
        
        # Create the spreadsheet
        body = {
            "properties": {"title": title},
            "sheets": [
                {
                    "properties": {
                        "title": sheet_title or "Sheet1",
                        "gridProperties": {
                            "rowCount": 1000,
                            "columnCount": 13,  # A-M (includes ID column)
                        },
                    }
                }
            ],
        }
        
        spreadsheet_id = None
        sheet_id = None
        
        # Step 1: Create the spreadsheet
        url = f"{SHEETS_BASE_URL}"
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                url,
                json=body,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"Failed to create spreadsheet: {resp.text}")
            
            spreadsheet = resp.json()
            spreadsheet_id = spreadsheet["spreadsheetId"]
            sheet_id = spreadsheet["sheets"][0]["properties"]["sheetId"]
        
        # Step 2: Add header row
        async with httpx.AsyncClient(timeout=20) as client:
            header_url = f"{SHEETS_BASE_URL}/{spreadsheet_id}/values/A1:M1"
            header_body = {"values": [HEADER_ROW]}
            header_resp = await client.put(
                header_url,
                params={"valueInputOption": "USER_ENTERED"},
                json=header_body,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if header_resp.status_code not in (200, 201):
                logging.getLogger(__name__).warning("Failed to set header row: %s", header_resp.text)
        
        # Step 3: Protect the ID column (column M, index 12) from deletion
        async with httpx.AsyncClient(timeout=20) as client:
            protection_requests = [
                {
                    "addProtectedRange": {
                        "protectedRange": {
                            "range": {
                                "sheetId": sheet_id,
                                "startColumnIndex": 12,  # Column M (0-indexed)
                                "endColumnIndex": 13,    # Exclusive end, so just column M
                            },
                            "description": "Protected ID column - do not delete",
                            "warningOnly": False,
                            "requestingUserCanEdit": False,
                        }
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 12,  # Column M (0-indexed)
                            "endIndex": 13,    # Exclusive end, so just column M
                        },
                        "properties": {
                            "hiddenByUser": True
                        },
                        "fields": "hiddenByUser"
                    }
                }
            ]
            
            protection_body = {"requests": protection_requests}
            protection_url = f"{SHEETS_BASE_URL}/{spreadsheet_id}:batchUpdate"
            protection_resp = await client.post(
                protection_url,
                json=protection_body,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if protection_resp.status_code not in (200, 201):
                logging.getLogger(__name__).warning("Failed to protect and hide ID column: %s", protection_resp.text)
            else:
                logging.getLogger(__name__).info("Successfully protected and hidden ID column M")
        
        # Step 4: Update user's spreadsheet ID
        await user_crud.update(
            db,
            db_obj=user,
            obj_in={"sheets_spreadsheet_id": spreadsheet_id},
        )
        
        return spreadsheet_id

    async def get_row_values(
        self,
        access_token: str,
        spreadsheet_id: str,
        row_number: int,
        major_dimension: str = "ROWS",
    ) -> List[Any]:
        """Fetch values for a single row. Returns empty list if not found."""
        range_ = f"A{row_number}:L{row_number}"
        url = f"{SHEETS_BASE_URL}/{spreadsheet_id}/values/{range_}"
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        if resp.status_code != 200:
            return []
        data = resp.json()
        values = data.get("values", [])
        return values[0] if values else [] 