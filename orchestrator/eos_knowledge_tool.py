import json
import os

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
INDEX_FILE = os.path.join(KNOWLEDGE_BASE_DIR, "ceo_agent_answer_index.jsonl")

def query_eos_knowledge(query: str) -> str:
    """Queries the EOS knowledge base index for principles, definitions, or processes.
    
    Args:
        query: The term or concept to look up (e.g., 'Level 10 Meeting', 'IDS', 'Visionary').
    
    Returns:
        A formatted string containing the relevant EOS recommendations or principles.
    """
    if not os.path.exists(INDEX_FILE):
        return "Error: Knowledge base index not found."

    results = []
    query_lower = query.lower()
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            
            # Simple keyword search on the name or the answer
            name = record.get("name", "").lower()
            answer = record.get("what_does_eos_recommend", "").lower()
            
            if query_lower in name or query_lower in answer:
                res = f"--- {record.get('name')} ---\n"
                res += f"{record.get('what_does_eos_recommend')}\n"
                res += f"Next Steps: {record.get('what_should_happen_next')}\n"
                results.append(res)
                
            # Limit to top 3 results to prevent huge context bloat
            if len(results) >= 3:
                break
                
    if not results:
        return f"No EOS knowledge found for query: '{query}'"
        
    return "\n".join(results)
