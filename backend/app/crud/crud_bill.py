from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid

from app.crud.base import CRUDBase
from app.db.models.bill import Bill as BillModel, LineItem as LineItemModel
from app.schemas.bill import BillCreate as BillCreateSchema, BillUpdate as BillUpdateSchema, LineItemCreate as LineItemCreateSchema

class CRUDBill(CRUDBase[BillModel, BillCreateSchema, BillUpdateSchema]):
    async def get(self, db: AsyncSession, id: str) -> Optional[BillModel]:
        """Handles UUID string conversion and validation"""
        try:
            bill_uuid = uuid.UUID(id) if isinstance(id, str) else id
            result = await db.execute(
                select(BillModel)
                .options(selectinload(BillModel.items), selectinload(BillModel.owner))
                .filter(BillModel.id == bill_uuid)
            )
            return result.scalar_one_or_none()
        except (ValueError, TypeError):
            return None

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[BillModel]:
        result = await db.execute(
            select(BillModel)
            .options(selectinload(BillModel.items), selectinload(BillModel.owner))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_multi_by_owner(
        self, db: AsyncSession, *, owner_id: str, skip: int = 0, limit: int = 100
    ) -> List[BillModel]:
        try:
            owner_uuid = uuid.UUID(owner_id) if isinstance(owner_id, str) else owner_id
            result = await db.execute(
                select(BillModel)
                .options(selectinload(BillModel.items), selectinload(BillModel.owner))
                .filter(BillModel.user_id == owner_uuid)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except (ValueError, TypeError):
            return []

    async def create_with_items(self, db: AsyncSession, *, bill_in: BillCreateSchema) -> BillModel:
        """Creates bill with line items in single transaction"""
        user_uuid = None
        if bill_in.user_id:
            try:
                user_uuid = uuid.UUID(bill_in.user_id) if isinstance(bill_in.user_id, str) else bill_in.user_id
            except (ValueError, TypeError):
                pass
        
        bill_data = bill_in.model_dump(exclude={'items_services_purchased', 'user_id'})
        db_bill = BillModel(**bill_data, user_id=user_uuid)
        db.add(db_bill)
        await db.flush()
        
        # Save the bill ID before committing to avoid lazy loading issues
        bill_id = db_bill.id
        
        if bill_in.items_services_purchased:
            for item_data in bill_in.items_services_purchased:
                item_dict = item_data.model_dump()
                db_item = LineItemModel(**item_dict, bill_id=bill_id)
                db.add(db_item)
        
        await db.commit()
        
        # Eagerly load the items relationship to prevent lazy loading issues
        result = await db.execute(
            select(BillModel)
            .options(selectinload(BillModel.items), selectinload(BillModel.owner))
            .filter(BillModel.id == bill_id)
        )
        return result.scalar_one()

    async def update_with_items(self, db: AsyncSession, *, db_obj: BillModel, obj_in: BillCreateSchema) -> BillModel:
        """Updates bill and replaces all line items"""
        # Save the bill ID before operations to avoid lazy loading issues
        bill_id = db_obj.id
        
        bill_data = obj_in.model_dump(exclude={'items_services_purchased', 'user_id'})
        for field, value in bill_data.items():
            if value is not None:
                setattr(db_obj, field, value)
        
        await db.execute(delete(LineItemModel).filter(LineItemModel.bill_id == bill_id))
        
        if obj_in.items_services_purchased:
            for item_data in obj_in.items_services_purchased:
                item_dict = item_data.model_dump()
                db_item = LineItemModel(**item_dict, bill_id=bill_id)
                db.add(db_item)
        
        await db.commit()
        
        # Eagerly load the items relationship to prevent lazy loading issues
        result = await db.execute(
            select(BillModel)
            .options(selectinload(BillModel.items), selectinload(BillModel.owner))
            .filter(BillModel.id == bill_id)
        )
        return result.scalar_one()

    async def remove(self, db: AsyncSession, *, id: str) -> Optional[BillModel]:
        try:
            bill_uuid = uuid.UUID(id) if isinstance(id, str) else id
            result = await db.execute(select(BillModel).filter(BillModel.id == bill_uuid))
            obj = result.scalar_one_or_none()
            if obj:
                await db.delete(obj)
                await db.commit()
            return obj
        except (ValueError, TypeError):
            return None

    async def get_bills_by_date_range(
        self, db: AsyncSession, *, owner_id: str, start_date, end_date, skip: int = 0, limit: int = 100
    ) -> List[BillModel]:
        try:
            owner_uuid = uuid.UUID(owner_id) if isinstance(owner_id, str) else owner_id
            result = await db.execute(
                select(BillModel)
                .options(selectinload(BillModel.items), selectinload(BillModel.owner))
                .filter(
                    BillModel.user_id == owner_uuid,
                    BillModel.created_at >= start_date,
                    BillModel.created_at <= end_date
                )
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except (ValueError, TypeError):
            return []

    async def get_bills_by_merchant(
        self, db: AsyncSession, *, owner_id: str, merchant_name: str, skip: int = 0, limit: int = 100
    ) -> List[BillModel]:
        try:
            owner_uuid = uuid.UUID(owner_id) if isinstance(owner_id, str) else owner_id
            result = await db.execute(
                select(BillModel)
                .options(selectinload(BillModel.items), selectinload(BillModel.owner))
                .filter(
                    BillModel.user_id == owner_uuid,
                    BillModel.merchant_company_name.ilike(f"%{merchant_name}%")
                )
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except (ValueError, TypeError):
            return []

 