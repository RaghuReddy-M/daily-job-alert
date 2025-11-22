#!/usr/bin/env python3
"""
Daily job-search automation:
 - Uses Bing Web Search API to find fresher software developer jobs
 - Fetches page metadata
 - Sends results as HTML email
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

# Load env (works for local testing)
load_dotenv()

# Config from environment (GitHub Secrets will supply values)
BING_API_KEY = os.getenv("BING_API_KEY")
BING_ENDPOINT = os.getenv("BING_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")

EMAIL_SMTP = os.getenv("EMAIL_SMTP", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TO_EMAIL = os.getenv("TO_EMAIL")

COMPANIES = [c.strip() for c in os.getenv(
    "COMPANIES", 
    "google,amazon,microsoft,flipkart,ola,uber,meta,tesla,tcs,infosys,wipro"
).split(",") if c.strip()]

SEARCH_KEYWORDS = [k.strip() for k in os.getenv(
    "SEARCH_KEYWORDS", 
    "software developer fresher,software engineer fresher,graduate software engineer"
).split(",")]

MAX_RESULTS = int(os.getenv("MAX_RESULTS", "30"))

SEEN_STORE = "seen.json"  # Only works locally, not in GitHub Actions unless stored remotely


# -------------------------- Core Functions -------------------------- #

def search_bing(query, count=10):
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": query, "count": count, "mkt": "en-IN"}
    resp = requests.get(BING_ENDPOINT, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def extract_page_metadata(url):
    """Extract page title + first paragraph snippet."""
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "job-bot"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html5lib")

        title = soup.title.string.strip() if soup.title else ""
        p = soup.find("p")
        snippet = p.get_text().strip()[:300] if p else ""

        return {"title": title, "snippet": snippet}
    except:
        return {"title": "", "snippet": ""}


def build_queries():
    queries = []
    for kw in SEARCH_KEYWORDS:
        for c in COMPANIES:
            queries.append(f'{kw} "{c}"')
            queries.append(f'{kw} site:{c}.com careers')
        queries.append(kw + " fresher jobs tech companies startup")
    return list(dict.fromkeys(queries))


def collect_results():
    found = {}
    queries = build_queries()

    for q in queries:
        try:
            data = search_bing(q)
            items = data.get("webPages", {}).get("value", [])

            for item in items:
                url = item.get("url")
                if not url or url in found:
                    continue

                meta = extract_page_metadata(url)

                found[url] = {
                    "title": meta["title"] or item.get("name", "No Title"),
                    "url": url,
                    "snippet": meta["snippet"] or item.get("snippet", ""),
                    "source": item.get("displayUrl", "")
                }

                if len(found) >= MAX_RESULTS:
                    return list(found.values())

            time.sleep(1)

        except Exception as e:
            print("Error:", e)
            time.sleep(1)

    return list(found.values())


def generate_html(results):
    if not results:
        return "<p>No new results today.</p>"

    html = "<h2>Daily Job Search — Fresher Developer Roles</h2><ul>"

    for r in results:
        html += f"""
        <li>
            <a href="{r['url']}"><b>{r['title']}</b></a><br>
            <small>{r['source']}</small><br>
            <p>{r['snippet']}</p>
        </li><hr>
        """

    html += "</ul>"
    return html


def send_email(subject, body_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(body_html, "html"))

    server = smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    server.sendmail(EMAIL_USER, [TO_EMAIL], msg.as_string())
    server.quit()


def main():
    if not BING_API_KEY:
        raise Exception("Missing BING_API_KEY")

    results = collect_results()
    html = generate_html(results)
    send_email("Daily Job Alerts — Fresher Developer Roles", html)

    print("Email sent with", len(results), "results.")


if __name__ == "__main__":
    main()
