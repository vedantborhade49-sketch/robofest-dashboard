import os
from app.llm.config import LLMConfig
from app.llm.cloud_provider import CloudLLMProvider

def run_smoke_test():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        print("Please set your ANTHROPIC_API_KEY environment variable before running this test.")
        return

    config = LLMConfig(
        model_name="claude-3-haiku-20240307",
        temperature=0.0,
        max_tokens=500,
        api_key=api_key
    )
    provider = CloudLLMProvider(config)
    
    system_prompt = "You are an AI assistant parsing an emergency incident."
    user_prompt = "Generate a brief incident report about a drone detecting a lost hiker wearing a red jacket."
    
    print("Testing Anthropic Claude Structured Outputs API...")
    try:
        response = provider.generate(system_prompt, user_prompt)
        print("\nSuccess! Here is the parsed structured object:")
        print(f"Summary: {response.summary}")
        print(f"Observations: {response.observations}")
        print(f"Severity: {response.severity}")
        print(f"Confidence: {response.confidence}")
    except Exception as e:
        print(f"\nSmoke test failed: {e}")

if __name__ == "__main__":
    run_smoke_test()
