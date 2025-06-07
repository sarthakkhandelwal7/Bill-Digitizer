import google.generativeai as genai
from langchain_core.output_parsers import PydanticOutputParser
from PIL import Image
import json
import io
import re
from typing import Tuple, Optional

from app.schemas.bill import BillCreate
from app.core.config import Settings

def downsize_to_800(input_path: str, downsize: bool = False) -> bytes:
    """Downsize image to max 800px for efficient processing"""
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    
    if not downsize:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()
    
    if max(w, h) <= 800:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()
    
    if w >= h:
        new_w, new_h = 800, int(800 * (h / w))
    else:
        new_h, new_w = 800, int(800 * (w / h))
    
    resized = img.resize((new_w, new_h), resample=Image.LANCZOS)
    buffer = io.BytesIO()
    resized.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()

def extract_json_from_response(text: str) -> str:
    """Extract JSON from model response, handling various formats"""
    if not text or text.strip() == "":
        return "{}"
    
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    print(f"Warning: No JSON found in response. Raw text: {text[:200]}...")
    return "{}"

class BillAnalyzer:
    """Analyzes bill/receipt images using Google Gemini AI to extract structured data"""
    
    def __init__(self, settings: Settings):
        """Initialize analyzer with Gemini model and output parser"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.MODEL_NAME)
        self.parser = PydanticOutputParser(pydantic_object=BillCreate)
        
        self.prompt_template = """You are a bill/receipt analysis expert. Analyze this image and extract information into a JSON format.

IMPORTANT: You must respond with ONLY a valid JSON object. Do not include any explanatory text, markdown formatting, or code blocks.

Extract the following information and format it as a JSON object with these exact field names:
- "document_type": Type like "Receipt", "Invoice", "Bill"
- "merchant_company_name": Business name
- "address": Full address if visible
- "phone_number": Phone number if visible  
- "date": Date in YYYY-MM-DD format
- "time": Time in HH:MM AM/PM format
- "transaction_id": Transaction/receipt/invoice number
- "items_services_purchased": Array of items, each with "description", "quantity", "unit_price", "total_price_per_item"
- "subtotal": Subtotal amount as number
- "tax": Tax amount as number
- "discount_savings": Discount amount as number
- "total_amount": Final total as number
- "payment_method": Payment method used
- "card_last_four": Last 4 digits of card
- "approval_code": Approval code if present
- "currency": Currency code like "USD"
- "other_info": Any other relevant information

Use null for missing fields. Ensure all numbers are actual numbers, not strings.

Example response format:
{
  "document_type": "Receipt",
  "merchant_company_name": "ABC Store",
  "total_amount": 25.99,
  "items_services_purchased": [
    {
      "description": "Coffee",
      "quantity": 1,
      "unit_price": 4.99,
      "total_price_per_item": 4.99
    }
  ]
}

Now analyze the image and respond with ONLY the JSON object:"""
    
    def analyze_image(self, image_path: str, downsize=False) -> Tuple[BillCreate, Optional[genai.types.GenerateContentResponse]]:
        """Analyze bill image and return structured data"""
        try:
            print("Processing image...")
            raw_bytes = downsize_to_800(image_path, downsize=downsize)
            processed_image = Image.open(io.BytesIO(raw_bytes))
            
            print(f"Image processed successfully")
            print("Sending request to Gemini...")
            response = self.model.generate_content([self.prompt_template, processed_image])
            print("Received response from Gemini...")
            
            response_text = response.text if hasattr(response, 'text') and response.text else ""
            print(f"Raw response (first 200 chars): {response_text[:200]}...")
            
            json_text = extract_json_from_response(response_text)
            print(f"Extracted JSON (first 200 chars): {json_text[:200]}...")
            
            try:
                json_data = json.loads(json_text)
                print("JSON parsed successfully")
                print(f"DEBUG: items_services_purchased in response: {json_data.get('items_services_purchased', 'NOT_FOUND')}")
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}. Using empty dict.")
                json_data = {}
            
            result = BillCreate(**json_data)
            print("Successfully created BillCreate object")
            print(f"DEBUG: BillCreate items count: {len(result.items_services_purchased or [])}")
            if result.items_services_purchased:
                print(f"DEBUG: First item: {result.items_services_purchased[0]}")
            
            return result, response
            
        except Exception as e:
            print(f"Error during image analysis: {e}")
            import traceback
            traceback.print_exc()
            return BillCreate(), None

    def analyze_image_fallback(self, image_path: str) -> BillCreate:
        """Fallback analysis with simpler prompting when primary method fails"""
        try:
            print("Trying fallback analysis method...")
            raw_bytes = downsize_to_800(image_path)
            processed_image = Image.open(io.BytesIO(raw_bytes))
            
            simple_prompt = """Look at this receipt/bill image. Extract basic information and respond in this exact JSON format:

{
  "merchant_company_name": "store name here",
  "total_amount": 0.00,
  "date": "YYYY-MM-DD",
  "document_type": "Receipt",
  "items_services_purchased": [] 
}

Replace the values with what you see in the image. Use null if you can't find something. Ensure items_services_purchased is an array, even if empty."""
            
            response = self.model.generate_content([simple_prompt, processed_image])
            response_text = response.text if hasattr(response, 'text') and response.text else "{}"
            
            print(f"Fallback response: {response_text}")
            
            json_text = extract_json_from_response(response_text)
            try:
                json_data = json.loads(json_text)
            except json.JSONDecodeError:
                 json_data = {}
            
            if 'items_services_purchased' not in json_data:
                json_data['items_services_purchased'] = []

            return BillCreate(**json_data)
            
        except Exception as e:
            print(f"Fallback method also failed: {e}")
            return BillCreate() 