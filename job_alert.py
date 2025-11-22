#!/usr/bin/env python3
"""
Daily job-search automation using SerpAPI (Google Search API):
 - Searches fresher software developer jobs
 - Collects titles, URLs, snippets
 - Sends HTML email with results
"""

import os
import time
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

EMAIL_SMTP = os.getenv("EMAIL_SMTP", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TO_EMAIL = os.getenv("TO_EMAIL")

COMPANIES = [c.strip() for c in os.getenv(
    "COMPANIES",
    "google,amazon,microsoft,meta,tesla,flipkart,ola,uber,tcs,infosys,wipro"
).split(",")]

SEARCH_KEYWORDS = [k.strip() for k in os.getenv(
    "SEARCH_KEYWORDS",
    "software developer fresher,software engineer fresher,graduate software engineer"
).split(",")]

MAX_RESULTS = 20


def serpapi_search(query):
    """Perform Google Search using SerpAPI."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": "10",
        "hl": "en"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def collect_results():
    results = []
    queries = []

    for kw in SEARCH_KEYWORDS:
        for c in COMPANIES:
            queries.append(f"{kw} {c} jobs")
        queries.append(f"{kw} fresher jobs 2025")

    seen_urls = set()

    for q in queries:
        try:
            data = serpapi_search(q)
            organic = data.get("organic_results", [])

            for item in organic:
                link = item.get("link")
                title = item.get("title")
                snippet = item.get("snippet", "")

                if not link or link in seen_urls:
                    continue

                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet
                })

                seen_urls.add(link)

                if len(results) >= MAX_RESULTS:
                    return results

            time.sleep(1)

        except Exception as e:
            print("Error searching:", e)
            time.sleep(1)

    return results


def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    server = smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    server.sendmail(EMAIL_USER, [TO_EMAIL], msg.as_string())
    server.quit()


def generate_html(results):
    if not results:
        return "<p>No job results found today.</p>"

    html = "<h2>Daily Fresher Job Alerts</h2><ul>"

    for r in results:
        html += f"""
        <li>
            <a href="{r['url']}"><b>{r['title']}</b></a><br>
            <p>{r['snippet']}</p>
        </li><hr>
        """

    html += "</ul>"
    return html


def main():
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY missing")

    results = collect_results()
    html = generate_html(results)

    send_email("Daily Job Alerts – Software Developer Fresher", html)

    print("Email sent successfully with", len(results), "results.")


if __name__ == "__main__":
    main()
