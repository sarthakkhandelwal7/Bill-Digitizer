from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from pydantic import BaseModel

from app.db.session import get_database_session
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.models.bill import Bill

router = APIRouter()

# Predefined category mappings based on merchant patterns
CATEGORY_MAPPINGS = {
    "Food & Dining": [
        "restaurant", "cafe", "pizza", "burger", "coffee", "starbucks", "mcdonald", 
        "subway", "kfc", "domino", "food", "dining", "kitchen", "grill", "bistro",
        "bar", "pub", "brewery", "diner", "bakery", "donut"
    ],
    "Groceries": [
        "walmart", "target", "costco", "kroger", "safeway", "publix", "market", 
        "grocery", "supermarket", "food lion", "giant", "harris teeter", "aldi",
        "whole foods", "trader joe", "stop shop"
    ],
    "Gas & Transportation": [
        "gas", "fuel", "shell", "exxon", "chevron", "bp", "mobil", "speedway",
        "uber", "lyft", "taxi", "metro", "transit", "parking", "toll"
    ],
    "Shopping": [
        "amazon", "ebay", "store", "shop", "retail", "mall", "outlet", "boutique",
        "clothing", "fashion", "electronics", "best buy", "apple store"
    ],
    "Entertainment": [
        "movie", "cinema", "theater", "netflix", "spotify", "game", "entertainment",
        "amusement", "park", "zoo", "museum", "concert", "ticket"
    ],
    "Healthcare": [
        "pharmacy", "cvs", "walgreens", "rite aid", "hospital", "clinic", "doctor",
        "medical", "health", "dental", "vision", "urgent care"
    ],
    "Utilities": [
        "electric", "power", "water", "gas company", "internet", "phone", "cable",
        "utility", "verizon", "att", "comcast", "xfinity"
    ],
    "Home & Garden": [
        "home depot", "lowes", "hardware", "garden", "nursery", "furniture",
        "bed bath", "ikea", "home improvement"
    ]
}


class CategoryAssignment(BaseModel):
    bill_id: str
    category: str
    confidence: Optional[float] = None


class BulkCategoryAssignment(BaseModel):
    assignments: List[CategoryAssignment]


@router.post("/categorize/auto")
async def auto_categorize_bills(
    bill_ids: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Automatically categorize bills based on merchant names and patterns"""
    
    try:
        # Build query
        query = select(Bill).where(Bill.user_id == str(current_user.id))
        
        if bill_ids:
            query = query.where(Bill.id.in_(bill_ids))
        
        result = await db.execute(query)
        bills = result.scalars().all()
        
        categorized_count = 0
        categorizations = []
        
        for bill in bills:
            category, confidence = _categorize_bill(bill)
            
            if category and category != "Uncategorized":
                current_info = bill.other_info or ""
                if "Category:" not in current_info:
                    bill.other_info = f"Category: {category}; {current_info}".strip("; ")
                    categorized_count += 1
                
                categorizations.append({
                    "bill_id": str(bill.id),
                    "merchant": bill.merchant_company_name,
                    "category": category,
                    "confidence": confidence,
                    "amount": float(bill.total_amount) if bill.total_amount else 0
                })
        
        
        await db.commit()
        
        # Group by category for summary
        category_summary = {}
        for cat in categorizations:
            category = cat["category"]
            if category not in category_summary:
                category_summary[category] = {"count": 0, "total_amount": 0}
            category_summary[category]["count"] += 1
            category_summary[category]["total_amount"] += cat["amount"]
        
        return {
            "total_bills_processed": len(bills),
            "categorized_count": categorized_count,
            "categorizations": categorizations,
            "category_summary": category_summary
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error auto-categorizing bills: {str(e)}")


@router.post("/categorize/manual")
async def manually_categorize_bills(
    assignments: BulkCategoryAssignment,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Manually assign categories to bills"""
    
    try:
        updated_count = 0
        results = []
        
        for assignment in assignments.assignments:
            # Verify bill belongs to user
            bill_query = select(Bill).where(
                and_(
                    Bill.id == assignment.bill_id,
                    Bill.user_id == str(current_user.id)
                )
            )
            bill_result = await db.execute(bill_query)
            bill = bill_result.scalar_one_or_none()
            
            if not bill:
                results.append({
                    "bill_id": assignment.bill_id,
                    "success": False,
                    "error": "Bill not found"
                })
                continue
            
            current_info = bill.other_info or ""
            
            if "Category:" in current_info:
                parts = current_info.split(";")
                parts = [part.strip() for part in parts if not part.strip().startswith("Category:")]
                current_info = "; ".join(parts)
            
            bill.other_info = f"Category: {assignment.category}; {current_info}".strip("; ")
            updated_count += 1
            
            results.append({
                "bill_id": assignment.bill_id,
                "success": True,
                "category": assignment.category,
                "merchant": bill.merchant_company_name
            })
        
        await db.commit()
        
        return {
            "updated_count": updated_count,
            "results": results
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error manually categorizing bills: {str(e)}")


@router.get("/categories")
async def get_available_categories() -> Dict[str, Any]:
    """Get list of available categories and their patterns"""
    
    return {
        "categories": list(CATEGORY_MAPPINGS.keys()) + ["Uncategorized"],
        "category_patterns": CATEGORY_MAPPINGS
    }


@router.get("/categories/analysis")
async def get_category_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Analyze spending by categories"""
    
    try:
        bills_query = select(Bill).where(
            and_(
                Bill.user_id == str(current_user.id),
                Bill.other_info.isnot(None)
            )
        )
        result = await db.execute(bills_query)
        bills = result.scalars().all()
        
        category_stats = {}
        uncategorized_count = 0
        uncategorized_amount = 0
        
        for bill in bills:
            category = _extract_category_from_bill(bill)
            amount = float(bill.total_amount) if bill.total_amount else 0
            
            if category == "Uncategorized" or not category:
                uncategorized_count += 1
                uncategorized_amount += amount
            else:
                if category not in category_stats:
                    category_stats[category] = {
                        "count": 0,
                        "total_amount": 0,
                        "average_amount": 0,
                        "merchants": set()
                    }
                
                category_stats[category]["count"] += 1
                category_stats[category]["total_amount"] += amount
                if bill.merchant_company_name:
                    category_stats[category]["merchants"].add(bill.merchant_company_name)
        
        # Calculate averages and convert sets to lists
        for category in category_stats:
            stats = category_stats[category]
            stats["average_amount"] = stats["total_amount"] / stats["count"] if stats["count"] > 0 else 0
            stats["merchants"] = list(stats["merchants"])
            stats["merchant_count"] = len(stats["merchants"])
        
        # Add uncategorized if any
        if uncategorized_count > 0:
            category_stats["Uncategorized"] = {
                "count": uncategorized_count,
                "total_amount": uncategorized_amount,
                "average_amount": uncategorized_amount / uncategorized_count,
                "merchants": [],
                "merchant_count": 0
            }
        
        # Calculate totals
        total_amount = sum(stats["total_amount"] for stats in category_stats.values())
        total_bills = sum(stats["count"] for stats in category_stats.values())
        
        # Calculate percentages
        for category in category_stats:
            stats = category_stats[category]
            stats["percentage_of_spending"] = (stats["total_amount"] / total_amount * 100) if total_amount > 0 else 0
            stats["percentage_of_bills"] = (stats["count"] / total_bills * 100) if total_bills > 0 else 0
        
        return {
            "category_breakdown": category_stats,
            "summary": {
                "total_categories": len(category_stats),
                "total_bills": total_bills,
                "total_amount": total_amount,
                "categorized_percentage": ((total_bills - uncategorized_count) / total_bills * 100) if total_bills > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing categories: {str(e)}")


@router.get("/categories/suggestions")
async def get_categorization_suggestions(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get suggestions for uncategorized bills"""
    
    try:
        # Get uncategorized bills
        bills_query = select(Bill).where(
            and_(
                Bill.user_id == str(current_user.id),
                or_(
                    Bill.other_info.is_(None),
                    ~Bill.other_info.ilike("%Category:%")
                )
            )
        ).order_by(Bill.created_at.desc()).limit(limit)
        
        result = await db.execute(bills_query)
        bills = result.scalars().all()
        
        suggestions = []
        for bill in bills:
            category, confidence = _categorize_bill(bill)
            
            suggestions.append({
                "bill_id": str(bill.id),
                "merchant": bill.merchant_company_name,
                "amount": float(bill.total_amount) if bill.total_amount else 0,
                "date": bill.created_at.isoformat() if bill.created_at else None,
                "suggested_category": category,
                "confidence": confidence,
                "reasoning": _get_categorization_reasoning(bill, category)
            })
        
        return {
            "suggestions": suggestions,
            "total_uncategorized": len(bills)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categorization suggestions: {str(e)}")


def _categorize_bill(bill: Bill) -> tuple[str, float]:
    """Categorize a bill based on merchant name and other info"""
    if not bill.merchant_company_name:
        return "Uncategorized", 0.0
    
    merchant_lower = bill.merchant_company_name.lower()
    
    # Check each category for matches
    for category, keywords in CATEGORY_MAPPINGS.items():
        for keyword in keywords:
            if keyword in merchant_lower:
                # Calculate confidence based on keyword match quality
                confidence = min(0.9, len(keyword) / len(merchant_lower) + 0.3)
                return category, confidence
    
    return "Uncategorized", 0.0


def _extract_category_from_bill(bill: Bill) -> str:
    """Extract category from bill's other_info field"""
    if not bill.other_info:
        return "Uncategorized"
    
    if "Category:" in bill.other_info:
        # Extract category from other_info
        parts = bill.other_info.split(";")
        for part in parts:
            if part.strip().startswith("Category:"):
                return part.replace("Category:", "").strip()
    
    return "Uncategorized"


def _get_categorization_reasoning(bill: Bill, category: str) -> str:
    """Get reasoning for why a bill was categorized"""
    if category == "Uncategorized":
        return "No matching patterns found"
    
    if not bill.merchant_company_name:
        return "No merchant information available"
    
    merchant_lower = bill.merchant_company_name.lower()
    
    # Find which keyword matched
    for keyword in CATEGORY_MAPPINGS.get(category, []):
        if keyword in merchant_lower:
            return f"Matched keyword '{keyword}' in merchant name"
    
    return "Pattern matching" 