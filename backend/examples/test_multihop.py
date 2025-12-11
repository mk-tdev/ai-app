"""
Test Script for Multi-Hop Reasoning

This script demonstrates how to test the multi-hop reasoning functionality
with various types of complex queries.
"""
import requests
import json
from typing import Optional


class MultiHopTester:
    """Test multi-hop reasoning capabilities."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id: Optional[str] = None
    
    def test_simple_query(self):
        """Test with a simple query (should not use multi-hop)."""
        print("\n" + "="*60)
        print("TEST 1: Simple Query (No Multi-Hop Expected)")
        print("="*60)
        
        query = "What is RAG?"
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "message": query,
                "use_rag": True,
                "use_reasoning": True,
                "max_hops": 3,
            }
        )
        
        result = response.json()
        print(f"\nQuery: {query}")
        print(f"Answer: {result['message']}")
        print(f"Sources: {result.get('sources', [])}")
    
    def test_multi_hop_query(self):
        """Test with a query that requires multi-hop reasoning."""
        print("\n" + "="*60)
        print("TEST 2: Multi-Hop Query")
        print("="*60)
        
        query = "Compare the deployment process for Docker and Kubernetes and explain which is better for small teams"
        
        response = requests.post(
            f"{self.base_url}/api/chat/reasoning",
            json={
                "message": query,
                "max_hops": 3,
            }
        )
        
        result = response.json()
        print(f"\nQuery: {query}")
        print(f"\nStrategy Used: {result.get('strategy_used')}")
        print(f"Needs Multi-Hop: {result.get('needs_multi_hop')}")
        
        if result.get('reasoning_chain'):
            print("\nReasoning Chain:")
            for step in result['reasoning_chain']:
                print(f"\n  Step {step['step_number']}:")
                print(f"    Question: {step['question']}")
                print(f"    Answer: {step['answer'][:100]}...")
                print(f"    Confidence: {step['confidence']:.2f}")
                print(f"    Sources: {len(step['sources'])} documents")
        
        print(f"\nFinal Answer: {result['message'][:200]}...")
    
    def test_entity_relationship(self):
        """Test query requiring connecting entities."""
        print("\n" + "="*60)
        print("TEST 3: Entity Relationship Query")
        print("="*60)
        
        query = "What is the relationship between embeddings and vector databases in RAG?"
        
        response = requests.post(
            f"{self.base_url}/api/chat/reasoning",
            json={
                "message": query,
                "max_hops": 3,
            }
        )
        
        result = response.json()
        print(f"\nQuery: {query}")
        print(f"Strategy: {result.get('strategy_used')}")
        
        if result.get('reasoning_chain'):
            print(f"\nMulti-Hop Steps: {len(result['reasoning_chain'])}")
            for step in result['reasoning_chain']:
                print(f"  - {step['question']}")
        
        print(f"\nAnswer: {result['message']}")
    
    def test_complex_comparative(self):
        """Test complex comparative query."""
        print("\n" + "="*60)
        print("TEST 4: Complex Comparative Query")
        print("="*60)
        
        query = "What are the differences between LlamaCPP and Ollama, and which one is better for running local models?"
        
        response = requests.post(
            f"{self.base_url}/api/chat/reasoning",
            json={
                "message": query,
                "max_hops": 4,
            }
        )
        
        result = response.json()
        print(f"\nQuery: {query}")
        
        if result.get('reasoning_chain'):
            print(f"\nReasoning Steps ({len(result['reasoning_chain'])}):")
            for i, step in enumerate(result['reasoning_chain'], 1):
                print(f"\n{i}. {step['question']}")
                print(f"   → {step['answer'][:80]}...")
        
        print(f"\nFinal Answer:\n{result['message']}")
    
    def test_troubleshooting(self):
        """Test troubleshooting query."""
        print("\n" + "="*60)
        print("TEST 5: Troubleshooting Query")
        print("="*60)
        
        query = "Why is my ChromaDB not loading documents correctly and how do I fix it?"
        
        response = requests.post(
            f"{self.base_url}/api/chat/reasoning",
            json={
                "message": query,
                "max_hops": 3,
            }
        )
        
        result = response.json()
        print(f"\nQuery: {query}")
        print(f"Answer: {result['message']}")
    
    def run_all_tests(self):
        """Run all test cases."""
        print("\n" + "🚀 "*20)
        print("MULTI-HOP REASONING TEST SUITE")
        print("🚀 "*20)
        
        try:
            self.test_simple_query()
            self.test_multi_hop_query()
            self.test_entity_relationship()
            self.test_complex_comparative()
            self.test_troubleshooting()
            
            print("\n" + "✅ "*20)
            print("ALL TESTS COMPLETED")
            print("✅ "*20 + "\n")
            
        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Could not connect to server.")
            print("Make sure the backend is running on http://localhost:8000")
        except Exception as e:
            print(f"\n❌ Error: {e}")


def test_with_custom_query(query: str, max_hops: int = 3):
    """Test a custom query."""
    print(f"\nTesting custom query: {query}")
    
    response = requests.post(
        "http://localhost:8000/api/chat/reasoning",
        json={
            "message": query,
            "max_hops": max_hops,
        }
    )
    
    result = response.json()
    
    print(f"\nStrategy: {result.get('strategy_used')}")
    print(f"Multi-Hop: {result.get('needs_multi_hop')}")
    
    if result.get('reasoning_chain'):
        print(f"\nReasoning Chain ({len(result['reasoning_chain'])} steps):")
        for step in result['reasoning_chain']:
            print(f"\n  Step {step['step_number']}: {step['question']}")
            print(f"  Answer: {step['answer']}")
            print(f"  Confidence: {step['confidence']:.2%}")
    
    print(f"\n📝 Final Answer:\n{result['message']}")
    
    return result


if __name__ == "__main__":
    # Run the full test suite
    tester = MultiHopTester()
    tester.run_all_tests()
    
    # Uncomment to test a custom query
    # test_with_custom_query(
    #     "Who created the embedding model used in this application and what is it optimized for?",
    #     max_hops=3
    # )
