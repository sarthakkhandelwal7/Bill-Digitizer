from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text, String
from datetime import datetime, timedelta
from sqlalchemy.orm import selectinload

from app.db.session import get_database_session
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.models.bill import Bill
from app.schemas.bill import Bill as BillSchema

router = APIRouter()


@router.get("/search")
async def search_bills(
    q: Optional[str] = Query(None, description="Search query for merchant, amount, or other fields"),
    merchant: Optional[str] = Query(None, description="Filter by merchant name"),
    category: Optional[str] = Query(None, description="Filter by payment method/category"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    date_from: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: created_at, total_amount, merchant_company_name"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Advanced bill search and filtering with pagination"""
    
    try:
        # Base query
        query = select(Bill).where(Bill.user_id == str(current_user.id)).options(selectinload(Bill.items))
        
        # Text search across multiple fields
        if q:
            search_pattern = f"%{q}%"
            search_conditions = or_(
                func.coalesce(Bill.merchant_company_name, '').ilike(search_pattern),
                func.coalesce(Bill.address, '').ilike(search_pattern),
                func.coalesce(Bill.transaction_id, '').ilike(search_pattern),
                func.coalesce(Bill.payment_method, '').ilike(search_pattern),
                func.coalesce(Bill.other_info, '').ilike(search_pattern),
                Bill.total_amount.cast(String).ilike(search_pattern)
            )
            query = query.where(search_conditions)
        
        if merchant:
            query = query.where(Bill.merchant_company_name.ilike(f"%{merchant}%"))
        
        if category or payment_method:
            payment_filter = category or payment_method
            query = query.where(Bill.payment_method.ilike(f"%{payment_filter}%"))
        
        if min_amount is not None:
            query = query.where(Bill.total_amount >= min_amount)
        
        if max_amount is not None:
            query = query.where(Bill.total_amount <= max_amount)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.where(Bill.created_at >= from_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                query = query.where(Bill.created_at < to_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
        
        valid_sort_fields = ["created_at", "total_amount", "merchant_company_name", "date"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        sort_column = getattr(Bill, sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()
        
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        bills = result.scalars().all()
        
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "bills": [BillSchema.model_validate(bill) for bill in bills],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "filters_applied": {
                "search_query": q,
                "merchant": merchant,
                "category": category,
                "min_amount": min_amount,
                "max_amount": max_amount,
                "date_from": date_from,
                "date_to": date_to,
                "payment_method": payment_method,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching bills: {str(e)}")


@router.get("/filters/options")
async def get_filter_options(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get available filter options for dropdowns"""
    
    try:
        merchants_result = await db.execute(
            select(Bill.merchant_company_name)
            .where(
                and_(
                    Bill.user_id == str(current_user.id),
                    Bill.merchant_company_name.isnot(None)
                )
            )
            .distinct()
            .order_by(Bill.merchant_company_name)
        )
        merchants = [row[0] for row in merchants_result.fetchall() if row[0]]
        
        payment_methods_result = await db.execute(
            select(Bill.payment_method)
            .where(
                and_(
                    Bill.user_id == str(current_user.id),
                    Bill.payment_method.isnot(None)
                )
            )
            .distinct()
            .order_by(Bill.payment_method)
        )
        payment_methods = [row[0] for row in payment_methods_result.fetchall() if row[0]]
        
        amount_range_result = await db.execute(
            select(
                func.min(Bill.total_amount).label('min_amount'),
                func.max(Bill.total_amount).label('max_amount')
            ).where(
                and_(
                    Bill.user_id == str(current_user.id),
                    Bill.total_amount.isnot(None)
                )
            )
        )
        amount_range = amount_range_result.first()
        
        date_range_result = await db.execute(
            select(
                func.min(Bill.created_at).label('earliest_date'),
                func.max(Bill.created_at).label('latest_date')
            ).where(Bill.user_id == str(current_user.id))
        )
        date_range = date_range_result.first()
        
        return {
            "merchants": merchants,
            "payment_methods": payment_methods,
            "amount_range": {
                "min": float(amount_range.min_amount) if amount_range.min_amount else 0,
                "max": float(amount_range.max_amount) if amount_range.max_amount else 0
            },
            "date_range": {
                "earliest": date_range.earliest_date.isoformat() if date_range.earliest_date else None,
                "latest": date_range.latest_date.isoformat() if date_range.latest_date else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting filter options: {str(e)}")


@router.get("/quick-filters")
async def get_quick_filters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get pre-defined quick filter options"""
    
    try:
        now = datetime.now()
        
        week_start = now - timedelta(days=now.weekday())
        week_query = select(func.count(Bill.id), func.sum(Bill.total_amount)).where(
            and_(
                Bill.user_id == str(current_user.id),
                Bill.created_at >= week_start
            )
        )
        week_result = await db.execute(week_query)
        week_data = week_result.first()
        
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_query = select(func.count(Bill.id), func.sum(Bill.total_amount)).where(
            and_(
                Bill.user_id == str(current_user.id),
                Bill.created_at >= month_start
            )
        )
        month_result = await db.execute(month_query)
        month_data = month_result.first()
        
        thirty_days_ago = now - timedelta(days=30)
        thirty_query = select(func.count(Bill.id), func.sum(Bill.total_amount)).where(
            and_(
                Bill.user_id == str(current_user.id),
                Bill.created_at >= thirty_days_ago
            )
        )
        thirty_result = await db.execute(thirty_query)
        thirty_data = thirty_result.first()
        
        # Get approximate high value threshold (simple approach)
        high_value_query = select(Bill.total_amount).where(
            and_(
                Bill.user_id == str(current_user.id),
                Bill.total_amount.isnot(None)
            )
        ).order_by(Bill.total_amount.desc()).limit(10)
        high_value_result = await db.execute(high_value_query)
        high_values = high_value_result.scalars().all()
        high_value_threshold = min(high_values) if high_values else 100
        
        return {
            "quick_filters": [
                {
                    "name": "This Week",
                    "key": "this_week",
                    "date_from": week_start.strftime("%Y-%m-%d"),
                    "bill_count": week_data[0] or 0,
                    "total_amount": float(week_data[1]) if week_data[1] else 0
                },
                {
                    "name": "This Month", 
                    "key": "this_month",
                    "date_from": month_start.strftime("%Y-%m-%d"),
                    "bill_count": month_data[0] or 0,
                    "total_amount": float(month_data[1]) if month_data[1] else 0
                },
                {
                    "name": "Last 30 Days",
                    "key": "last_30_days", 
                    "date_from": thirty_days_ago.strftime("%Y-%m-%d"),
                    "bill_count": thirty_data[0] or 0,
                    "total_amount": float(thirty_data[1]) if thirty_data[1] else 0
                },
                {
                    "name": "High Value (Top 10%)",
                    "key": "high_value",
                    "min_amount": float(high_value_threshold),
                    "description": f"Transactions above ${high_value_threshold:.2f}"
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting quick filters: {str(e)}") 