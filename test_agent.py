from agents.graph import run_agent
import json

query  = "What is described in my documents about RAG systems?"
result = run_agent(query, language='all')

print('═' * 60)
print(f'QUERY:        {result["query"]}')
print(f'SUB-QUESTIONS: {result["sub_questions"]}')
print(f'RETRIES:      {result["retry_count"]}')
print(f'GROUNDED:     {result["grounded"]}')
print(f'CRITIQUE:     {result["critique"]}')
print()
print('ANSWER:')
print(result['answer'])
print()
print(f'TOP CHUNKS ({len(result["retrieved_chunks"])} total):')
for i, chunk in enumerate(result['retrieved_chunks'][:3], 1):
    source = chunk['source'].split('/')[-1]
    print(f'  [{i}] rerank={chunk["rerank_score"]:.3f} | {source}')
    print(f'      {chunk["child_text"][:100]}...')