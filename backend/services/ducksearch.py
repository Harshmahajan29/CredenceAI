import requests
from bs4 import BeautifulSoup

def search_duckduckgo(query):
    url = "https://html.duckduckgo.com/html/"
    
    try:
        response = requests.post(url, data={"q": query})
        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        for result in soup.find_all("div", class_="result"):
            title_tag = result.find("a", class_="result__a")
            snippet_tag = result.find("a", class_="result__snippet")

            if title_tag:
                title = title_tag.text
                link = title_tag.get("href")
                snippet = snippet_tag.text if snippet_tag else ""

                results.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })

        return results

    except Exception as e:
        print("DuckDuckGo error:", e)
        return []