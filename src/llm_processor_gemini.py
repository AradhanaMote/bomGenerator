# src/llm_processor_gemini.py

import os
import json
import re
import time
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class GeminiLLMProcessor:
    """Handles BOM generation using Google's Gen AI SDK"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with working model
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Initialize client
        self.client = genai.Client(api_key=self.api_key)
        
        # Use a reliable model
        self.model_name = "models/gemini-2.5-flash"
        self.current_description = ""
        print(f"✅ Using model: {self.model_name}")
        
    def generate_bom(self, product_description: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate BOM with automatic retry on quota errors
        
        Args:
            product_description: User's description of the product
            max_retries: Number of times to retry on rate limit errors
            
        Returns:
            Structured BOM as dictionary
        """
        
        self.current_description = product_description
        prompt = self._create_bom_prompt(product_description)
        
        for attempt in range(max_retries):
            try:
                print(f"⏳ Sending request to Gemini (attempt {attempt + 1}/{max_retries})...")
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=4096,
                    )
                )
                
                if response.text:
                    print("✓ Received response from Gemini")
                    return self._parse_llm_response(response.text)
                else:
                    print("⚠️ Empty response from Gemini")
                    if attempt < max_retries - 1:
                        print("Retrying...")
                        time.sleep(2)
                        continue
                    return self._get_fallback_bom(product_description)
                    
            except Exception as e:
                error_str = str(e)
                
                # Handle rate limiting (429 errors)
                if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
                    # Extract retry delay if present
                    delay_match = re.search(r'retryDelay.*?(\d+)s', error_str)
                    delay = int(delay_match.group(1)) if delay_match else 20
                    
                    if attempt < max_retries - 1:
                        print(f"⚠️ Rate limit hit. Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        print("❌ Max retries exceeded for rate limit")
                
                # Handle other errors
                else:
                    print(f"❌ Error calling Gemini: {e}")
                    if attempt < max_retries - 1:
                        print("Retrying...")
                        time.sleep(2)
                        continue
                    break
        
        return self._get_fallback_bom(product_description)
    
    def _create_bom_prompt(self, description: str) -> str:
        """Create a clear, structured prompt for Gemini"""
        
        return f"""You are a Bill of Materials (BOM) expert. Generate a detailed BOM for: "{description}"

IMPORTANT: Return ONLY a valid JSON object. No markdown, no explanations, no other text.

The JSON must have this exact structure:
{{
    "product_name": "Descriptive name based on the input",
    "description": "{description}",
    "components": [
        {{
            "id": "comp-001",
            "name": "Component name",
            "category": "electrical or mechanical or structural or hardware or assembly",
            "quantity": 1,
            "unit": "piece",
            "subcomponents": [
                {{
                    "name": "Subcomponent name",
                    "quantity": 1,
                    "unit": "piece",
                    "verify_needed": false
                }}
            ],
            "verify_needed": false,
            "notes": "Additional details"
        }}
    ]
}}

REQUIREMENTS:
1. Include 8-12 main components
2. Each main component should have 2-5 subcomponents
3. Use realistic quantities
4. Categories must be one of: electrical, mechanical, structural, hardware, assembly
5. Set verify_needed=true only if uncertain
6. NO trailing commas in arrays/objects
7. NO comments in the JSON
8. Return ONLY the JSON object

Example for electric scooter:
{{
    "product_name": "Electric Scooter - Urban Commuter",
    "description": "Small electric scooter with lithium battery, disc brakes, LED display",
    "components": [
        {{
            "id": "comp-001",
            "name": "Lithium Battery Pack",
            "category": "electrical",
            "quantity": 1,
            "unit": "piece",
            "subcomponents": [
                {{"name": "18650 Lithium Cells", "quantity": 20, "unit": "pieces", "verify_needed": false}},
                {{"name": "Battery Management System", "quantity": 1, "unit": "piece", "verify_needed": false}},
                {{"name": "Battery Housing", "quantity": 1, "unit": "piece", "verify_needed": false}}
            ],
            "verify_needed": false,
            "notes": "36V 10Ah configuration"
        }}
    ]
}}

Now generate the BOM for: "{description}"
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response with robust error handling"""
        
        try:
            # Clean the response
            cleaned = response.strip()
            print(f"✓ Received response ({len(cleaned)} characters)")
            
            # Remove markdown code blocks
            if "```json" in cleaned:
                start = cleaned.find("```json") + 7
                end = cleaned.find("```", start)
                if end > start:
                    cleaned = cleaned[start:end].strip()
            elif "```" in cleaned:
                start = cleaned.find("```") + 3
                end = cleaned.find("```", start)
                if end > start:
                    cleaned = cleaned[start:end].strip()
            
            # Find the JSON object (between first { and last })
            json_start = cleaned.find('{')
            json_end = cleaned.rfind('}') + 1
            
            if json_start < 0 or json_end <= json_start:
                print("❌ No valid JSON object found")
                print(f"First 200 chars: {cleaned[:200]}")
                return self._get_fallback_bom("No JSON found")
            
            json_str = cleaned[json_start:json_end]
            
            # Fix common JSON issues
            # Remove trailing commas before } and ]
            json_str = re.sub(',\s*}', '}', json_str)
            json_str = re.sub(',\s*]', ']', json_str)
            
            # Remove comments (// style)
            json_str = re.sub('//.*?\n', '\n', json_str)
            
            # Parse JSON
            try:
                bom_data = json.loads(json_str)
                print(f"✓ Successfully parsed JSON")
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse failed: {e}")
                print("Attempting to extract components array...")
                
                # Try to extract just the components array
                components_match = re.search(r'"components"\s*:\s*(\[.*\])', json_str, re.DOTALL)
                if components_match:
                    try:
                        components_str = components_match.group(1)
                        # Fix trailing commas in components array
                        components_str = re.sub(',\s*}', '}', components_str)
                        components_str = re.sub(',\s*]', ']', components_str)
                        components = json.loads(components_str)
                        
                        bom_data = {
                            "product_name": "Electric Scooter",
                            "description": self.current_description,
                            "components": components
                        }
                        print(f"✓ Extracted {len(components)} components")
                    except json.JSONDecodeError as e2:
                        print(f"❌ Could not parse components: {e2}")
                        return self._get_fallback_bom("Component parse failed")
                else:
                    print("❌ No components array found")
                    return self._get_fallback_bom("No components")
            
            # Add metadata
            bom_data["generated_at"] = datetime.now().isoformat()
            
            # Ensure components is a list
            if "components" not in bom_data or not isinstance(bom_data["components"], list):
                bom_data["components"] = []
            
            # Validate and fix each component
            validated_components = []
            for i, comp in enumerate(bom_data["components"], 1):
                if not isinstance(comp, dict):
                    continue
                
                # Ensure required fields
                validated_comp = {
                    "id": comp.get("id", f"comp-{i:03d}"),
                    "name": comp.get("name", f"Component {i}"),
                    "category": comp.get("category", "general"),
                    "quantity": int(comp.get("quantity", 1)),
                    "unit": comp.get("unit", "piece"),
                    "subcomponents": [],
                    "verify_needed": bool(comp.get("verify_needed", False)),
                    "notes": comp.get("notes", "")
                }
                
                # Handle subcomponents
                if "subcomponents" in comp and isinstance(comp["subcomponents"], list):
                    for j, sub in enumerate(comp["subcomponents"]):
                        if isinstance(sub, dict):
                            validated_sub = {
                                "name": sub.get("name", f"Subcomponent {j+1}"),
                                "quantity": int(sub.get("quantity", 1)),
                                "unit": sub.get("unit", "piece"),
                                "verify_needed": bool(sub.get("verify_needed", False))
                            }
                            validated_comp["subcomponents"].append(validated_sub)
                
                validated_components.append(validated_comp)
            
            bom_data["components"] = validated_components
            bom_data["total_components"] = len(validated_components)
            
            # Count total subcomponents
            total_subs = sum(len(c["subcomponents"]) for c in validated_components)
            print(f"✓ Processed {len(validated_components)} components with {total_subs} subcomponents")
            
            return bom_data
            
        except Exception as e:
            print(f"❌ Unexpected error in parsing: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_bom(f"Parse error")
    
    def _get_fallback_bom(self, description: str) -> Dict[str, Any]:
        """Provide a detailed fallback BOM when generation fails"""
        
        print("📋 Using detailed fallback BOM template")
        
        # Create a reasonable default BOM for electric scooter
        if "scooter" in description.lower():
            return {
                "product_name": "Electric Scooter (Template)",
                "description": description,
                "components": [
                    {
                        "id": "comp-001",
                        "name": "Lithium Battery Pack",
                        "category": "electrical",
                        "quantity": 1,
                        "unit": "piece",
                        "subcomponents": [
                            {"name": "18650 Cells", "quantity": 20, "unit": "pieces", "verify_needed": True},
                            {"name": "BMS", "quantity": 1, "unit": "piece", "verify_needed": True},
                            {"name": "Battery Case", "quantity": 1, "unit": "piece", "verify_needed": True}
                        ],
                        "verify_needed": True,
                        "notes": "36V 10Ah - verify specifications"
                    },
                    {
                        "id": "comp-002",
                        "name": "Hub Motor",
                        "category": "electrical",
                        "quantity": 1,
                        "unit": "piece",
                        "subcomponents": [
                            {"name": "350W Motor", "quantity": 1, "unit": "piece", "verify_needed": True},
                            {"name": "Controller", "quantity": 1, "unit": "piece", "verify_needed": True},
                            {"name": "Wiring Harness", "quantity": 1, "unit": "piece", "verify_needed": True}
                        ],
                        "verify_needed": True,
                        "notes": "Verify power rating"
                    },
                    {
                        "id": "comp-003",
                        "name": "Disc Brake System",
                        "category": "mechanical",
                        "quantity": 2,
                        "unit": "sets",
                        "subcomponents": [
                            {"name": "Brake Caliper", "quantity": 2, "unit": "pieces", "verify_needed": True},
                            {"name": "Brake Rotor", "quantity": 2, "unit": "pieces", "verify_needed": True},
                            {"name": "Brake Pads", "quantity": 4, "unit": "pieces", "verify_needed": True},
                            {"name": "Brake Cables", "quantity": 2, "unit": "pieces", "verify_needed": True}
                        ],
                        "verify_needed": True,
                        "notes": "Front and rear - verify rotor size"
                    },
                    {
                        "id": "comp-004",
                        "name": "LED Display",
                        "category": "electrical",
                        "quantity": 1,
                        "unit": "piece",
                        "subcomponents": [
                            {"name": "LCD Screen", "quantity": 1, "unit": "piece", "verify_needed": True},
                            {"name": "Control Board", "quantity": 1, "unit": "piece", "verify_needed": True},
                            {"name": "Display Housing", "quantity": 1, "unit": "piece", "verify_needed": True}
                        ],
                        "verify_needed": True,
                        "notes": "Speed and battery display"
                    },
                    {
                        "id": "comp-005",
                        "name": "Frame Assembly",
                        "category": "structural",
                        "quantity": 1,
                        "unit": "piece",
                        "subcomponents": [
                            {"name": "Aluminum Deck", "quantity": 1, "unit": "piece", "verify_needed": True},
                            {"name": "Steering Column", "quantity": 1, "unit": "piece", "verify_needed": True},
                            {"name": "Handlebar", "quantity": 1, "unit": "piece", "verify_needed": True},
                            {"name": "Folding Mechanism", "quantity": 1, "unit": "piece", "verify_needed": True}
                        ],
                        "verify_needed": True,
                        "notes": "Verify material and dimensions"
                    }
                ],
                "total_components": 5,
                "generated_at": datetime.now().isoformat(),
                "fallback": True
            }
        
        # Generic fallback for other products
        return {
            "product_name": "Product (Manual Entry)",
            "description": description[:200],
            "components": [
                {
                    "id": "comp-001",
                    "name": "Main Assembly",
                    "category": "assembly",
                    "quantity": 1,
                    "unit": "piece",
                    "subcomponents": [],
                    "verify_needed": True,
                    "notes": "Manual verification required"
                }
            ],
            "total_components": 1,
            "generated_at": datetime.now().isoformat(),
            "fallback": True
        }