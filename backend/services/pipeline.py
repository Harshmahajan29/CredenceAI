from backend.services.querygenerator import generate_queries
from backend.services.ducksearch import search_duckduckgo

def deduplicate(results):
    seen = set()
    unique = []

    for r in results:
        if r["link"] not in seen:
            seen.add(r["link"])
            unique.append(r)

    return unique

def run_pipeline(input_json):
    explanation = input_json.get("explanation", "")

    # Step 1: Generate queries
    queries = generate_queries(explanation)
    print(" Queries:", queries)

    # Step 2: Search
    all_results = []
    for q in queries:
        results = search_duckduckgo(q)
        all_results.extend(results)

    # Step 3: Deduplicate
    unique_results = deduplicate(all_results)

    print(" Top Results:", unique_results[:5])

    return {
        "queries": queries,
        "results": unique_results[:10]
    }