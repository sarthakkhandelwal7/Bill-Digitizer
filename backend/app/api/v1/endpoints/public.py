from typing import Dict, Any
from fastapi import APIRouter

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


@router.get("/categories")
async def get_available_categories() -> Dict[str, Any]:
    """Get list of available categories and their patterns"""
    
    return {
        "categories": list(CATEGORY_MAPPINGS.keys()) + ["Uncategorized"],
        "category_patterns": CATEGORY_MAPPINGS
    } 