from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
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
                range_ = f"A{row_num}:L{row_num}"
                url = f"{SHEETS_BASE_URL}/{spreadsheet_id}/values/{range_}"
                params = {"valueInputOption": value_input_option}
                body = {"values": [row_values]}
                resp = await client.put(
                    url,
                    params=params,
                    json=body,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                outcomes[row_num] = resp.status_code in (200, 201)
        return outcomes

    async def create_spreadsheet(
        self,
        db: AsyncSession,
        user: User,
        user_crud: CRUDUser,
        title: str,
        sheet_title: Optional[str] = None,
    ) -> str:
        """Create a new spreadsheet and return its ID."""
        access_token = await self._refresh_access_token_if_needed(db, user, user_crud)
        url = f"{SHEETS_BASE_URL}"
        body: Dict[str, Any] = {
            "properties": {"title": title},
        }
        if sheet_title:
            body["sheets"] = [{"properties": {"title": sheet_title}}]

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, json=body, headers={"Authorization": f"Bearer {access_token}"})

        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create spreadsheet: {resp.text}")

        data = resp.json()
        spreadsheet_id = data.get("spreadsheetId")
        if not spreadsheet_id:
            raise RuntimeError("Spreadsheet ID missing in response")

        # Append header row
        try:
            await self.append_rows(
                db,
                user,
                user_crud,
                spreadsheet_id=spreadsheet_id,
                values=[HEADER_ROW],
                range_="A1",
                value_input_option="RAW",
            )
        except Exception as e:
            # Not fatal; log but proceed
            import logging
            logging.getLogger(__name__).warning("Failed to append header row: %s", e)

        # Store for user if not set
        if not user.sheets_spreadsheet_id:
            await user_crud.update(
                db,
                db_obj=user,
                obj_in={"sheets_spreadsheet_id": spreadsheet_id},
            )
        return spreadsheet_id 