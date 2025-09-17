import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

USER_ID = "me17ScoAAAAJ"
URL = f"https://scholar.google.com/citations?hl=en&user={USER_ID}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
}

def get_author_profile_data():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    # --- Author Info ---
    author_info = {
        "name": soup.select_one("#gsc_prf_in").text.strip(),
        "position": soup.select_one("#gsc_prf_inw+ .gsc_prf_il").text.strip(),
        "email": soup.select_one("#gsc_prf_ivh").text.strip(),
        "departments": soup.select_one("#gsc_prf_int").text.strip(),
    }

    # --- Publications (title, authors, venue, year) ---
    articles = []
    rows = soup.select("#gsc_a_b .gsc_a_tr")  # each row = one publication
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
        # Drop empty fields
        articles.append({k: v for k, v in article.items() if v})

    # --- Sort publications by year (newest → oldest) ---
    articles.sort(key=lambda x: int(x.get("year", 0)), reverse=True)

    # --- Citation Table ---
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

    return {
        "_lastFetched": datetime.now().strftime("%Y-%m-%d"),
        "author": author_info,
        "publications": articles,
        "metrics": cited_by,
    }


def main():
    data = get_author_profile_data()

    # Ensure /public exists
    os.makedirs("public", exist_ok=True)
    output_path = os.path.join("public", "scholar.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Scholar JSON updated with {len(data['publications'])} publications.")


if __name__ == "__main__":
    main()
