# test_gemini_models.py

from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

def list_available_models():
    """List all available models and their supported methods"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    print("🔍 Fetching available models...\n")
    
    try:
        # List all models
        models = client.models.list()
        
        print("📋 AVAILABLE MODELS:\n")
        found_generate = False
        
        for model in models:
            # Check if model supports generateContent
            supports_generate = False
            if hasattr(model, 'supported_actions'):
                supports_generate = 'generateContent' in model.supported_actions
            
            # Only show models that support generateContent
            if supports_generate or 'gemini' in model.name:
                print(f"📌 Model: {model.name}")
                print(f"   Display name: {getattr(model, 'display_name', 'N/A')}")
                print(f"   Description: {getattr(model, 'description', 'N/A')[:100]}...")
                if hasattr(model, 'supported_actions'):
                    print(f"   Supports: {', '.join(model.supported_actions)}")
                print(f"   Supports generateContent: {supports_generate}")
                print("-" * 60)
                
                if supports_generate:
                    found_generate = True
        
        if not found_generate:
            print("\n⚠️ No models found with generateContent support!")
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")

def test_specific_model(model_name: str):
    """Test a specific model to see if it works"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    client = genai.Client(api_key=api_key)
    
    print(f"\n🧪 Testing model: {model_name}")
    print("-" * 40)
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say 'Hello, I am working!' in one short sentence.",
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=50
            )
        )
        
        if response.text:
            print(f"✅ SUCCESS! Response: {response.text}")
            return True
        else:
            print("❌ Model returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GEMINI MODEL TESTER")
    print("=" * 60)
    
    # First, list available models
    list_available_models()
    
    # Then try common model names
    print("\n" + "=" * 60)
    print("TESTING COMMON MODELS")
    print("=" * 60)
    
    common_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-pro",
        "gemini-2.0-flash-exp",
        "gemini-2.0-pro-exp",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro"
    ]
    
    working_models = []
    
    for model in common_models:
        if test_specific_model(model):
            working_models.append(model)
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if working_models:
        print(f"✅ Working models found: {', '.join(working_models)}")
        print("\nUse one of these in your llm_processor_gemini.py")
    else:
        print("❌ No working models found!")
        print("\nPossible issues:")
        print("1. API key might be invalid or expired")
        print("2. Region restrictions (try using a VPN or different region)")
        print("3. Account may not have access to these models")
        print("4. Need to enable billing or request access")