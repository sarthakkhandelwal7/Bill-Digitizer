from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.models.bill import Bill as BillModel, LineItem as LineItemModel
from app.schemas.bill import BillCreate as BillCreateSchema, LineItemCreate as LineItemCreateSchema

class CRUDBill:
    def get(self, db: Session, id: int) -> Optional[BillModel]:
        return db.query(BillModel).filter(BillModel.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[BillModel]:
        return db.query(BillModel).offset(skip).limit(limit).all()

    def create_with_items(
        self, db: Session, *, bill_in: BillCreateSchema
    ) -> BillModel:
        """
        Create a new Bill and its associated LineItems.
        """
        print(f"DEBUG: Creating bill with {len(bill_in.items_services_purchased or [])} line items")
        
        # Create Bill object from schema, excluding line items for now
        bill_data = bill_in.model_dump(exclude={"items_services_purchased"})
        db_bill = BillModel(**bill_data)
        
        db.add(db_bill)
        db.flush() # Ensure bill_id is available for line items

        # Create LineItem objects
        if bill_in.items_services_purchased:
            print(f"DEBUG: Processing {len(bill_in.items_services_purchased)} line items")
            for i, item_schema in enumerate(bill_in.items_services_purchased):
                item_data = item_schema.model_dump()
                print(f"DEBUG: Line item {i+1}: {item_data}")
                db_item = LineItemModel(**item_data, bill_id=db_bill.id)
                db.add(db_item) # Explicitly add each line item to the session
        else:
            print("DEBUG: No line items to process")
        
        db.commit()
        db.refresh(db_bill) # Refresh to get updated state, including generated IDs and relationships
        print(f"DEBUG: Bill created with ID {db_bill.id}, items count: {len(db_bill.items)}")
        return db_bill

    def update_with_items(
        self, db: Session, *, db_obj: BillModel, obj_in: BillCreateSchema
    ) -> BillModel:
        """
        Update an existing Bill and its associated LineItems.
        """
        # Get all data from the schema
        all_data = obj_in.model_dump()
        
        # Update Bill fields (excluding line items)
        bill_data = {k: v for k, v in all_data.items() if k not in ["items_services_purchased", "items"]}
        for field, value in bill_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Delete existing line items
        db.query(LineItemModel).filter(LineItemModel.bill_id == db_obj.id).delete()
        
        # Get items data - check both possible field names
        items_data = []
        if "items_services_purchased" in all_data and all_data["items_services_purchased"]:
            items_data = all_data["items_services_purchased"]
        elif "items" in all_data and all_data["items"]:
            items_data = all_data["items"]
            
        if items_data:
            for item_data in items_data:
                # Handle both dict and schema objects
                if hasattr(item_data, 'model_dump'):
                    item_dict = item_data.model_dump()
                elif isinstance(item_data, dict):
                    item_dict = item_data.copy()
                else:
                    item_dict = item_data.__dict__.copy()
                
                # Remove any existing id and bill_id fields
                item_dict.pop('id', None)
                item_dict.pop('bill_id', None)
                
                db_item = LineItemModel(**item_dict, bill_id=db_obj.id)
                db.add(db_item)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # Placeholder for delete - to be implemented later
    # def remove(self, db: Session, *, id: int) -> BillModel:
    #     return super().remove(db, id=id)

bill = CRUDBill() 