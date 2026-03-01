# src/llm_processor.py

import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class LLMProcessor:
    """Handles LLM interactions for BOM generation"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        Initialize the LLM processor with OpenAI client
        
        Args:
            model: The OpenAI model to use (default: gpt-3.5-turbo)
            api_key: OpenAI API key (if not provided, reads from OPENAI_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize the new OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
    def generate_bom(self, product_description: str) -> Dict[str, Any]:
        """
        Generate BOM from product description using LLM
        
        Args:
            product_description: User's description of the product
            
        Returns:
            Structured BOM as dictionary
        """
        
        # Craft the prompt carefully to minimize hallucinations
        prompt = self._create_bom_prompt(product_description)
        
        try:
            # New API syntax for chat completions
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are a BOM generation expert. Extract components accurately and avoid hallucinations. "
                            "Always respond with valid JSON only, no additional text."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=2000,
                response_format={"type": "json_object"}  # Request JSON format if model supports it
            )
            
            # Extract the content from the response (new way)
            bom_text = response.choices[0].message.content
            return self._parse_llm_response(bom_text)
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            print("Falling back to default BOM structure...")
            return self._get_fallback_bom(product_description)
    
    def generate_bom_streaming(self, product_description: str):
        """
        Generate BOM with streaming response (optional feature)
        
        Args:
            product_description: User's description of the product
            
        Yields:
            Chunks of the response as they arrive
        """
        prompt = self._create_bom_prompt(product_description)
        
        try:
            # Streaming version
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a BOM generation expert. Extract components accurately and avoid hallucinations."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"Error in streaming: {e}")
            yield json.dumps(self._get_fallback_bom(product_description))
    
    def _create_bom_prompt(self, description: str) -> str:
        """Create a detailed prompt for the LLM"""
        
        return f"""
        Generate a detailed Bill of Materials (BOM) for the following product:
        
        Product Description: "{description}"
        
        Follow these guidelines STRICTLY:
        1. Identify ONLY components that are physically part of the product
        2. Include major assemblies and their sub-components
        3. Estimate reasonable quantities for a single unit
        4. If uncertain about a component, mark it as "verify_needed": true
        5. Do NOT invent components that don't make sense for this product
        6. Use realistic quantities (e.g., don't put 100 motors in a single scooter)
        
        Return the BOM as a structured JSON with this exact format:
        {{
            "product_name": "string (descriptive name based on the input)",
            "description": "string (copy of input description)",
            "components": [
                {{
                    "id": "unique-id (format: comp-001, comp-002, etc)",
                    "name": "component name (clear and specific)",
                    "category": "mechanical/electrical/structural/assembly/hardware/accessory",
                    "quantity": number (integer, realistic quantity),
                    "unit": "pieces/meters/kg/set (appropriate unit)",
                    "subcomponents": [
                        {{
                            "name": "subcomponent name",
                            "quantity": number,
                            "unit": "pieces",
                            "verify_needed": boolean
                        }}
                    ],
                    "verify_needed": boolean (true if uncertain),
                    "notes": "string (additional details or specifications)"
                }}
            ],
            "total_components": number (count of main components),
            "generated_at": "timestamp (use current ISO format)"
        }}
        
        Return ONLY the JSON object, no other text, no markdown formatting.
        """
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        try:
            # Clean the response - remove any markdown formatting or extra text
            cleaned_response = response.strip()
            
            # Try to find JSON if it's embedded in markdown code blocks
            if "```json" in cleaned_response:
                # Extract content between ```json and ```
                start = cleaned_response.find("```json") + 7
                end = cleaned_response.find("```", start)
                if end > start:
                    cleaned_response = cleaned_response[start:end].strip()
            elif "```" in cleaned_response:
                # Extract content between ``` and ```
                start = cleaned_response.find("```") + 3
                end = cleaned_response.find("```", start)
                if end > start:
                    cleaned_response = cleaned_response[start:end].strip()
            
            # Try to find JSON object (between first { and last })
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = cleaned_response[json_start:json_end]
                bom_data = json.loads(json_str)
                
                # Add generated timestamp if not present
                if "generated_at" not in bom_data:
                    bom_data["generated_at"] = datetime.now().isoformat()
                
                # Validate structure
                if self._validate_bom_structure(bom_data):
                    return bom_data
                else:
                    print("BOM validation failed, using fallback...")
                    
            else:
                print("No valid JSON found in response")
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {response[:200]}...")  # Print first 200 chars for debugging
            
        return self._get_fallback_bom("Parsing failed")
    
    def _validate_bom_structure(self, bom: Dict) -> bool:
        """Validate that BOM has required fields and correct types"""
        try:
            # Check required fields
            required = ["product_name", "components"]
            if not all(field in bom for field in required):
                print(f"Missing required fields. Found: {list(bom.keys())}")
                return False
            
            # Check components is a list
            if not isinstance(bom["components"], list):
                print("Components is not a list")
                return False
            
            # Validate each component has required fields
            for i, comp in enumerate(bom["components"]):
                comp_required = ["name", "quantity", "category"]
                if not all(field in comp for field in comp_required):
                    print(f"Component {i} missing required fields: {comp}")
                    return False
                
                # Ensure quantity is positive
                if comp.get("quantity", 0) <= 0:
                    comp["quantity"] = 1  # Fix invalid quantity
                
            return True
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    def _get_fallback_bom(self, description: str) -> Dict[str, Any]:
        """Provide a fallback BOM when LLM fails"""
        return {
            "product_name": "Product (Manual Review Required)",
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
                    "notes": "Manual verification required - AI generation failed"
                },
                {
                    "id": "comp-002",
                    "name": "Component Set",
                    "category": "hardware",
                    "quantity": 1,
                    "unit": "set",
                    "subcomponents": [],
                    "verify_needed": True,
                    "notes": "Please manually define components"
                }
            ],
            "total_components": 2,
            "generated_at": datetime.now().isoformat(),
            "fallback": True,
            "error": "AI generation failed, using template"
        }
    
    def test_connection(self) -> bool:
        """Test the OpenAI API connection"""
        try:
            # Simple test call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Say 'Connection successful' in one word"}
                ],
                max_tokens=10
            )
            print(f"API Connection test successful: {response.choices[0].message.content}")
            return True
        except Exception as e:
            print(f"API Connection test failed: {e}")
            return False


# Optional: Add a main function to test the processor independently
if __name__ == "__main__":
    # Test the LLM processor
    print("Testing LLM Processor...")
    
    # Initialize processor
    processor = LLMProcessor()
    
    # Test connection
    if processor.test_connection():
        # Test BOM generation
        test_description = "Design a small electric scooter with lithium battery, disc brakes, LED display"
        print(f"\nGenerating BOM for: {test_description}")
        
        bom = processor.generate_bom(test_description)
        print("\nGenerated BOM:")
        print(json.dumps(bom, indent=2))
    else:
        print("Please check your API key and try again.")