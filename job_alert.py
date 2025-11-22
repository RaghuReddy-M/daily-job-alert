import os
import smtplib
from email.mime.text import MIMEText
from serpapi import GoogleSearch

# Load environment variables
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TO_EMAIL = os.getenv("TO_EMAIL")

COMPANIES = [c.strip() for c in os.getenv("COMPANIES", "").split(",")]
SEARCH_KEYWORDS = [k.strip() for k in os.getenv("SEARCH_KEYWORDS", "").split(",")]

MAX_RESULTS = 50


# -----------------------------
# Search SerpAPI Google Jobs (India Only)
# -----------------------------
def serpapi_search(company, keyword):
    """Perform Google Jobs Search using SerpAPI (India only)."""
    
    query = f"{company} {keyword} fresher jobs in India"
    
    search = GoogleSearch({
        "engine": "google_jobs",
        "q": query,
        "hl": "en",
        "gl": "in",
        "location": "India",
        "api_key": SERPAPI_KEY
    })

    results = search.get_dict()
    return results.get("jobs_results", [])


# -----------------------------
# Collect jobs
# -----------------------------
def collect_results():
    all_jobs = []
    seen_urls = set()

    for kw in SEARCH_KEYWORDS:
        for c in COMPANIES:
            try:
                jobs = serpapi_search(c, kw)

                for job in jobs:
                    title = job.get("title", "No title")
                    company = job.get("company_name", "Unknown")
                    location = job.get("location", "Unknown")
                    url = job.get("apply_link", None)

                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_jobs.append({
                            "title": title,
                            "company": company,
                            "location": location,
                            "url": url
                        })

            except Exception as e:
                print(f"Error fetching results for {c} + {kw}: {e}")

    return all_jobs[:MAX_RESULTS]


# -----------------------------
# Send email
# -----------------------------
def send_email(subject, html):
    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)  # Gmail App Password
        server.sendmail(EMAIL_USER, TO_EMAIL, msg.as_string())
        server.quit()
        print("Email sent successfully!")

    except Exception as e:
        print(f"Error sending email: {e}")


# -----------------------------
# Build email HTML
# -----------------------------
def build_email(results):
    if not results:
        return "<h2>No new fresher jobs found today.</h2>"

    html = "<h2>Daily Job Alerts - India Fresher Developer Roles</h2><br>"

    for r in results:
        html += f"""
        <b>{r['title']}</b><br>
        Company: {r['company']}<br>
        Location: {r['location']}<br>
        <a href="{r['url']}">Apply Here</a>
        <br><br>
        """

    return html


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("Collecting India-based developer fresher jobs...")
    results = collect_results()
    print(f"Found {len(results)} results.")

    html = build_email(results)
    send_email("Daily Job Alerts - India Software Developer Fresher", html)

