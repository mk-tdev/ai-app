"""
Quick Start Example: Multi-Hop Reasoning

Run this script to see multi-hop reasoning in action!
"""
import requests
import json


def print_separator(title=""):
    """Print a nice separator."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'-'*60}\n")


def example1_simple_comparison():
    """Example 1: Simple comparison query."""
    print_separator("Example 1: Simple Comparison")
    
    query = "What are the differences between embeddings and tokens in AI?"
    print(f"Question: {query}\n")
    
    response = requests.post(
        "http://localhost:8000/api/chat/reasoning",
        json={"message": query, "max_hops": 3}
    )
    
    result = response.json()
    
    print(f"Strategy Used: {result.get('strategy_used')}")
    print(f"Multi-Hop Needed: {result.get('needs_multi_hop')}")
    
    if result.get('reasoning_chain'):
        print("\n📋 Reasoning Process:")
        for step in result['reasoning_chain']:
            print(f"\n  Step {step['step_number']}: {step['question']}")
            print(f"  → {step['answer'][:150]}...")
            print(f"  📊 Confidence: {step['confidence']:.1%}")
    
    print(f"\n💡 Final Answer:\n{result['message']}\n")


def example2_entity_relationship():
    """Example 2: Entity relationship query."""
    print_separator("Example 2: Entity Relationship")
    
    query = "How does ChromaDB use embeddings to enable semantic search?"
    print(f"Question: {query}\n")
    
    response = requests.post(
        "http://localhost:8000/api/chat/reasoning",
        json={"message": query, "max_hops": 3}
    )
    
    result = response.json()
    
    if result.get('reasoning_chain'):
        print("🔍 Breaking down the question:")
        for i, step in enumerate(result['reasoning_chain'], 1):
            print(f"\n{i}. {step['question']}")
    
    print(f"\n💡 Final Answer:\n{result['message']}\n")


def example3_multi_entity():
    """Example 3: Complex multi-entity query."""
    print_separator("Example 3: Complex Multi-Entity Query")
    
    query = "Compare LlamaCPP, Ollama, and HuggingFace for running local LLMs, and explain which is best for GPU-accelerated inference"
    print(f"Question: {query}\n")
    
    response = requests.post(
        "http://localhost:8000/api/chat/reasoning",
        json={"message": query, "max_hops": 4}
    )
    
    result = response.json()
    
    if result.get('reasoning_chain'):
        print(f"🧠 Reasoning Chain ({len(result['reasoning_chain'])} steps):\n")
        for step in result['reasoning_chain']:
            print(f"Step {step['step_number']}: {step['question']}")
            print(f"  Sources used: {len(step['sources'])} documents")
            print()
    
    print(f"💡 Synthesized Answer:\n{result['message']}\n")


def example4_simple_query_for_comparison():
    """Example 4: Simple query to show when multi-hop is NOT used."""
    print_separator("Example 4: Simple Query (No Multi-Hop)")
    
    query = "What is RAG?"
    print(f"Question: {query}\n")
    
    response = requests.post(
        "http://localhost:8000/api/chat",
        json={
            "message": query,
            "use_rag": True,
            "use_reasoning": True,  # Even with reasoning enabled...
        }
    )
    
    result = response.json()
    
    print(f"✅ For simple queries, the system intelligently uses direct retrieval")
    print(f"   (No multi-hop needed)\n")
    print(f"💡 Answer:\n{result['message']}\n")


def main():
    """Run all examples."""
    print("\n" + "🌟 "*25)
    print("   MULTI-HOP REASONING EXAMPLES")
    print("🌟 "*25)
    
    try:
        # Check if server is running
        health = requests.get("http://localhost:8000/health")
        if health.status_code != 200:
            print("\n❌ Server is not healthy. Please check the backend.")
            return
        
        print("\n✅ Server is running!")
        
        # Run examples
        example1_simple_comparison()
        example2_entity_relationship()
        example3_multi_entity()
        example4_simple_query_for_comparison()
        
        print_separator()
        print("✅ All examples completed!")
        print("\nTry your own queries:")
        print("  python test_multihop.py")
        print()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server.")
        print("\nPlease make sure the backend is running:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
        print()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
