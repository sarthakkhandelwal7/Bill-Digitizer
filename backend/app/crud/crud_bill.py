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

    # Placeholder for update - to be implemented later
    # def update(self, db: Session, *, db_obj: BillModel, obj_in: Union[BillUpdateSchema, Dict[str, Any]]) -> BillModel:
    #     ...
    #     return super().update(db, db_obj=db_obj, obj_in=obj_in)

    # Placeholder for delete - to be implemented later
    # def remove(self, db: Session, *, id: int) -> BillModel:
    #     return super().remove(db, id=id)

bill = CRUDBill() 