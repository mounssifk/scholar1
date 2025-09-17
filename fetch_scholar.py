import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone

USER_ID = "me17ScoAAAAJ"
URL = f"https://scholar.google.com/citations?hl=en&user={USER_ID}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/104.0.0.0 Safari/537.36"
}

def get_author_profile_data():
    response = requests.get(URL, headers=HEADERS)
    
    # Save fetched page for debugging (ignored in git)
    os.makedirs("debug", exist_ok=True)
    with open("debug/debug_page.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, "html.parser")

    # Check if the profile exists
    name_el = soup.select_one("#gsc_prf_in")
    if not name_el:
        raise Exception("Google Scholar blocked the request or page structure changed")

    # --- Author Info ---
    author_info = {
        "name": name_el.text.strip(),
        "position": soup.select_one("#gsc_prf_inw+ .gsc_prf_il").text.strip() if soup.select_one("#gsc_prf_inw+ .gsc_prf_il") else "",
        "email": soup.select_one("#gsc_prf_ivh").text.strip() if soup.select_one("#gsc_prf_ivh") else "",
        "departments": soup.select_one("#gsc_prf_int").text.strip() if soup.select_one("#gsc_prf_int") else "",
    }

    # --- Publications ---
    articles = []
    rows = soup.select("#gsc_a_b .gsc_a_tr")
    for row in rows:
        title_el = row.select_one(".gsc_a_at")
        authors_el = row.select_one(".gsc_a_at+ .gs_gray")
        venue_el = row.select_one(".gs_gray+ .gs_gray")
        year_el = row.select_one(".gsc_a_y span")

        article = {
            "title": title_el.text.strip() if title_el else "",
            "link": "https://scholar.google.com" + title_el["href"] if title_el else "",
            "authors": authors_el.text.strip() if authors_el else "",
            "publication": venue_el.text.strip() if venue_el else "",
            "year": year_el.text.strip() if year_el else "",
        }
        articles.append({k: v for k, v in article.items() if v})

    articles.sort(key=lambda x: int(x.get("year", 0)), reverse=True)

    # --- Citation Table ---
    cited_by = {}
    try:
        cited_by = {
            "citations": {
                "all": soup.select_one("tr:nth-child(1) .gsc_rsb_sc1+ .gsc_rsb_std").text,
                "since_2017": soup.select_one("tr:nth-child(1) .gsc_rsb_std+ .gsc_rsb_std").text,
            },
            "h_index": {
                "all": soup.select_one("tr:nth-child(2) .gsc_rsb_sc1+ .gsc_rsb_std").text,
                "since_2017": soup.select_one("tr:nth-child(2) .gsc_rsb_std+ .gsc_rsb_std").text,
            },
            "i_index": {
                "all": soup.select_one("tr~ tr+ tr .gsc_rsb_sc1+ .gsc_rsb_std").text,
                "since_2017": soup.select_one("tr~ tr+ tr .gsc_rsb_std+ .gsc_rsb_std").text,
            },
        }
    except AttributeError:
        cited_by = {}  # leave empty if blocked

    now = datetime.now(timezone.utc)
    epoch_seconds = int(now.timestamp())

    return {
        "_lastFetched": now.strftime("%Y-%m-%d"),
        "_lastFetchedEpoch": epoch_seconds,
        "author": author_info,
        "publications": articles,
        "metrics": cited_by,
    }


def main():
    try:
        data = get_author_profile_data()
    except Exception as e:
        print(f"⚠️ Could not fetch Google Scholar profile: {e}")
        return  # Exit gracefully

    os.makedirs("public", exist_ok=True)
    output_path = os.path.join("public", "scholar.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Scholar JSON updated with {len(data['publications'])} publications.")
    print(f"⏱ Last fetched epoch: {data['_lastFetchedEpoch']}")


if __name__ == "__main__":
    main()
