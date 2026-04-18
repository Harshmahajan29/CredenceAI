import re

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text.lower())

def extract_keywords(text):
    stopwords = {
        "the","is","in","on","and","have","has","been",
        "this","that","with","from","are","was","were"
    }

    words = clean_text(text).split()
    return [w for w in words if len(w) > 3 and w not in stopwords]

def generate_queries(explanation):
    keywords = extract_keywords(explanation)

    queries = []

    # Base query
    queries.append(explanation)

    # Keyword-based queries
    for word in keywords[:5]:
        queries.append(f"{word} news")
        queries.append(f"{word} fact check")

    # Context-based queries
    if "reported" in explanation.lower():
        queries.append("latest news reports verification")

    if "global" in explanation.lower():
        queries.append("international news coverage")

    # Remove duplicates + limit
    return list(set(queries))[:8]