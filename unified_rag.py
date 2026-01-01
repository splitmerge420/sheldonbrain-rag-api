"""
Unified RAG system for all LLMs: Gemini, Grok, GPT, Claude
Provides consistent interface with automatic memory recall and storage.
"""

from google import genai
from anthropic import Anthropic
import openai
import requests
from config import GEMINI_API_KEY, XAI_API_KEY
from rag_wrapper import recall_memory, store_memory
from typing import Optional, Literal
import os

# Initialize clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) if os.getenv("ANTHROPIC_API_KEY") else None
openai.api_key = os.getenv("OPENAI_API_KEY")

LLMProvider = Literal["gemini", "grok", "gpt", "claude"]


def chat_with_rag(
    provider: LLMProvider,
    user_message: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    auto_recall: bool = True,
    auto_store: bool = False,
    conversation_history: list = None,
    temperature: float = 0.7
) -> dict:
    """
    Unified chat interface with RAG for all LLM providers.
    
    Args:
        provider: Which LLM to use ("gemini", "grok", "gpt", "claude")
        user_message: The user's message/query
        model: Optional specific model (defaults to best for each provider)
        system_prompt: Optional system prompt
        auto_recall: Automatically recall relevant memories
        auto_store: Automatically store the response
        conversation_history: Previous messages
        temperature: Response randomness (0-1)
    
    Returns:
        Dictionary with response and metadata
    """
    # Recall relevant memories if enabled
    recalled_context = ""
    if auto_recall:
        recalled_context = recall_memory(user_message, top_k=5)
        memory_count = recalled_context.count('Memory')
        print(f"📚 Recalled {memory_count} relevant memories from Notion")
    
    # Build enhanced message
    if recalled_context and recalled_context != "[No relevant memories found]":
        enhanced_message = f"{recalled_context}\n\n{user_message}"
    else:
        enhanced_message = user_message
    
    # Route to appropriate provider
    try:
        if provider == "gemini":
            result = _chat_gemini(enhanced_message, model, system_prompt, conversation_history, temperature)
        elif provider == "grok":
            result = _chat_grok(enhanced_message, model, system_prompt, conversation_history, temperature)
        elif provider == "gpt":
            result = _chat_gpt(enhanced_message, model, system_prompt, conversation_history, temperature)
        elif provider == "claude":
            result = _chat_claude(enhanced_message, model, system_prompt, conversation_history, temperature)
        else:
            return {"success": False, "error": f"Unknown provider: {provider}"}
        
        # Store response if enabled
        stored_id = None
        if auto_store and result["success"]:
            memory_content = f"Query: {user_message}\n\nResponse ({provider}): {result['response']}"
            stored_id = store_memory(
                content=memory_content,
                sphere="S016",
                source=f"{provider}_session",
                additional_metadata={
                    "provider": provider,
                    "model": result.get("model", "unknown"),
                    "query": user_message[:200]
                }
            )
            print(f"💾 Stored response as memory: {stored_id}")
        
        result["recalled_memories"] = recalled_context if auto_recall else None
        result["stored_memory_id"] = stored_id
        result["provider"] = provider
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": provider
        }


def _chat_gemini(message: str, model: Optional[str], system_prompt: Optional[str], 
                 history: list, temperature: float) -> dict:
    """Chat with Gemini."""
    model = model or "gemini-2.0-flash-exp"
    
    # Build config
    config = {"temperature": temperature}
    if system_prompt:
        config["system_instruction"] = system_prompt
    
    # Generate response
    response = gemini_client.models.generate_content(
        model=model,
        contents=message,
        config=config
    )
    
    return {
        "success": True,
        "response": response.text,
        "model": model,
        "usage": {
            "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
            "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
            "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
        }
    }


def _chat_grok(message: str, model: Optional[str], system_prompt: Optional[str],
               history: list, temperature: float) -> dict:
    """Chat with Grok using direct HTTP API."""
    model = model or "grok-3"
    
    # Build messages for API
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    # Call Grok API directly via HTTP
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": messages,
        "model": model,
        "temperature": temperature
    }
    
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        return {
            "success": True,
            "response": data["choices"][0]["message"]["content"],
            "model": model,
            "usage": data.get("usage", {})
        }
    else:
        raise Exception(f"Grok API error: {response.status_code} - {response.text}")


def _chat_gpt(message: str, model: Optional[str], system_prompt: Optional[str],
              history: list, temperature: float) -> dict:
    """Chat with GPT."""
    model = model or "gpt-4o"
    
    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    
    return {
        "success": True,
        "response": response.choices[0].message.content,
        "model": model,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
    }


def _chat_claude(message: str, model: Optional[str], system_prompt: Optional[str],
                 history: list, temperature: float) -> dict:
    """Chat with Claude."""
    if not anthropic_client:
        raise Exception("Anthropic API key not configured")
    
    model = model or "claude-3-5-sonnet-20241022"
    
    # Build messages
    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    # Call Claude API
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4096
    }
    
    if system_prompt:
        kwargs["system"] = system_prompt
    
    response = anthropic_client.messages.create(**kwargs)
    
    return {
        "success": True,
        "response": response.content[0].text,
        "model": model,
        "usage": {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }
    }


def interactive_session(provider: LLMProvider = "gemini"):
    """
    Start an interactive chat session with RAG memory.
    
    Args:
        provider: Which LLM to use (gemini, grok, gpt, claude)
    """
    print(f"🤖 {provider.upper()} RAG Interactive Session")
    print("=" * 50)
    print("Commands:")
    print("  'exit' - quit")
    print("  'recall <query>' - search memories")
    print("  'switch <provider>' - change LLM (gemini/grok/gpt/claude)")
    print("  'clear' - clear conversation history")
    print("=" * 50)
    
    conversation_history = []
    current_provider = provider
    
    while True:
        user_input = input(f"\n👤 You ({current_provider}): ").strip()
        
        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break
        
        if user_input.lower() == "clear":
            conversation_history = []
            print("🗑️  Conversation history cleared")
            continue
        
        if user_input.lower().startswith("switch "):
            new_provider = user_input[7:].strip().lower()
            if new_provider in ["gemini", "grok", "gpt", "claude"]:
                current_provider = new_provider
                print(f"🔄 Switched to {current_provider}")
            else:
                print(f"❌ Unknown provider: {new_provider}")
            continue
        
        if user_input.lower().startswith("recall "):
            recall_query = user_input[7:]
            memories = recall_memory(recall_query, top_k=5)
            print(f"\n📚 Memories:\n{memories}")
            continue
        
        # Call LLM with RAG
        result = chat_with_rag(
            provider=current_provider,
            user_message=user_input,
            auto_recall=True,
            auto_store=False,
            conversation_history=conversation_history
        )
        
        if result["success"]:
            print(f"\n🤖 {current_provider.upper()}: {result['response']}")
            print(f"   [{result['usage']['total_tokens']} tokens]")
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": result['response']})
        else:
            print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        provider = sys.argv[1].lower()
        if provider not in ["gemini", "grok", "gpt", "claude"]:
            print(f"Unknown provider: {provider}")
            print("Usage: python unified_rag.py [gemini|grok|gpt|claude]")
            sys.exit(1)
        interactive_session(provider)
    else:
        # Default to Gemini
        interactive_session("gemini")
