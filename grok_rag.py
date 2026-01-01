"""
Grok API integration with RAG memory.
This enables Grok to access full Notion workspace context.
"""

from xai_sdk import Client
from config import XAI_API_KEY
from rag_wrapper import recall_memory, store_memory, enrich_prompt_with_memory
from typing import Optional

# Initialize Grok client
grok_client = Client(api_key=XAI_API_KEY)


def grok_with_rag(
    user_message: str,
    model: str = "grok-beta",
    system_prompt: Optional[str] = None,
    auto_recall: bool = True,
    auto_store: bool = False,
    conversation_history: list = None
) -> dict:
    """
    Call Grok API with RAG memory enhancement.
    
    Args:
        user_message: The user's message/query
        model: Grok model to use (grok-beta, grok-2-1212, etc.)
        system_prompt: Optional system prompt
        auto_recall: Automatically recall relevant memories before responding
        auto_store: Automatically store the response as new memory
        conversation_history: Previous messages in the conversation
    
    Returns:
        Dictionary with response and metadata
    """
    # Build messages array
    messages = []
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Recall relevant memories if enabled
    recalled_context = ""
    if auto_recall:
        recalled_context = recall_memory(user_message, top_k=5)
        print(f"📚 Recalled {recalled_context.count('Memory')} relevant memories")
    
    # Build enhanced user message
    if recalled_context and recalled_context != "[No relevant memories found]":
        enhanced_message = f"{recalled_context}\n\n{user_message}"
    else:
        enhanced_message = user_message
    
    messages.append({
        "role": "user",
        "content": enhanced_message
    })
    
    # Call Grok API using the correct SDK method
    try:
        response = grok_client.chat.create(
            model=model,
            messages=messages
        )
        
        assistant_message = response.choices[0].message.content
        
        # Store response as new memory if enabled
        stored_id = None
        if auto_store:
            memory_content = f"Query: {user_message}\n\nResponse: {assistant_message}"
            stored_id = store_memory(
                content=memory_content,
                sphere="S016",  # Computer Science/AI
                source="grok_session",
                additional_metadata={
                    "model": model,
                    "query": user_message[:200]
                }
            )
            print(f"💾 Stored response as memory: {stored_id}")
        
        return {
            "success": True,
            "response": assistant_message,
            "recalled_memories": recalled_context if auto_recall else None,
            "stored_memory_id": stored_id,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": None
        }


def grok_query_with_context(query: str, sphere_filter: Optional[str] = None) -> str:
    """
    Simple helper: Query Grok with automatic RAG context injection.
    
    Args:
        query: The question to ask Grok
        sphere_filter: Optional sphere to filter memories by
    
    Returns:
        Grok's response string
    """
    # Recall memories with optional sphere filter
    context = recall_memory(query, top_k=5, sphere_filter=sphere_filter)
    
    # Build enhanced prompt
    enhanced_query = f"{context}\n\n{query}"
    
    # Call Grok
    response = grok_client.chat.create(
        model="grok-beta",
        messages=[{"role": "user", "content": enhanced_query}]
    )
    
    return response.choices[0].message.content


def interactive_grok_session():
    """
    Start an interactive Grok session with RAG memory.
    """
    print("🤖 Grok RAG Interactive Session")
    print("=" * 50)
    print("Type 'exit' to quit, 'recall <query>' to search memories")
    print("=" * 50)
    
    conversation_history = []
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break
        
        if user_input.lower().startswith("recall "):
            # Manual memory recall
            recall_query = user_input[7:]
            memories = recall_memory(recall_query, top_k=5)
            print(f"\n📚 Memories:\n{memories}")
            continue
        
        # Call Grok with RAG
        result = grok_with_rag(
            user_message=user_input,
            auto_recall=True,
            auto_store=False,
            conversation_history=conversation_history
        )
        
        if result["success"]:
            print(f"\n🤖 Grok: {result['response']}")
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": result['response']})
        else:
            print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}\n")
        response = grok_query_with_context(query)
        print(f"Response: {response}")
    else:
        interactive_grok_session()
