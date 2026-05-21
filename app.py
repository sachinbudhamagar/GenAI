# Imports
import os
import re
import json
import html
import requests
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import textwrap
from bs4 import BeautifulSoup
import time
import tempfile
from functools import wraps
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -------------------- Setup --------------------
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OpenAI_API_Key")
serper_api_key = os.getenv("SERPER_API_KEY") or os.getenv("Serper_API_Key")

if openai_api_key and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = openai_api_key

llm = None
if openai_api_key:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# -------------------- Utility Functions --------------------
def retry_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_error = None
        for _ in range(3):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                time.sleep(2)
        raise last_error
    return wrapper

def clean_markdown(text: str) -> str:
    return re.sub(r"\*\*(.*?)\*\*", r"\1", text)

def is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", url.strip(), re.IGNORECASE))

def job_search_serper(query: str) -> dict:
    """
    Search for job listings using the Serper API based on the user query and location.
    if {query} does not match 100% provide error! try again
    Returns a dictionary containing job titles, links, and snippets.
    """
    if not serper_api_key:
        st.error("Serper API key is missing. Add SERPER_API_KEY to your .env file.")
        return {"Job Listings": []}

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}
    variations = [query, f"{query} jobs", f"{query} site:linkedin.com"]
    all_jobs = []

    for variation in variations:
        try:
            response = requests.post(url, headers=headers, json={"q": variation}, timeout=10)
            response.raise_for_status()
            results = response.json().get("organic", [])
            jobs = [
                {"Title": r.get("title"), "Link": r.get("link"), "Snippet": r.get("snippet")}
                for r in results if r.get("title") and r.get("link")
            ]
            all_jobs.extend(jobs)
        except requests.RequestException as e:
            st.warning(f"Search failed for '{variation}': {e}")

    unique_jobs = {job["Link"]: job for job in all_jobs}
    return {"Job Listings": list(unique_jobs.values())}

def extract_pdf_text(uploaded_file) -> str:
    try:
        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            st.error("Failed to extract any text from the PDF.")
            return ""
        return text
    except Exception as e:
        st.error(f"Failed to extract text from PDF: {e}")
        return ""

def generate_pdf_from_text(text: str, filename: str = "output.pdf") -> str:
    output_path = os.path.join(tempfile.gettempdir(), filename)
    c = canvas.Canvas(output_path, pagesize=letter)
    y = 750
    for line in clean_markdown(text).split('\n'):
        wrapped_lines = textwrap.wrap(line, width=90)
        for segment in wrapped_lines:
            if y < 50:
                c.showPage()
                y = 750
            c.drawString(50, y, segment)
            y -= 15
    c.save()
    return output_path

def compute_job_fit_scores(resume_text, jobs: list) -> tuple:
    if not resume_text.strip():
        st.error("Resume text is empty, cannot compute job fit scores.")
        return [], jobs

    jobs_to_score = jobs[:30]
    job_snippets = [job.get("Snippet", "") for job in jobs_to_score]
    job_titles = [job.get("Title", "Untitled job") for job in jobs_to_score]
    job_links = [job.get("Link", "#") for job in jobs_to_score]

    filtered_jobs = [(t, s, l) for t, s, l in zip(job_titles, job_snippets, job_links) if s.strip()]
    if not filtered_jobs:
        st.warning("No job snippets available for similarity scoring.")
        return [], jobs

    filtered_titles, filtered_snippets, filtered_links = zip(*filtered_jobs)

    documents = [resume_text] + list(filtered_snippets)
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except Exception as e:
        st.error(f"Error during TF-IDF vectorization: {e}")
        return [], jobs

    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    scored_jobs = [
        {"Score": round(score * 100, 2), "Title": title, "Snippet": snippet, "Link": link}
        for score, title, snippet, link in zip(similarities, filtered_titles, filtered_snippets, filtered_links)
    ]
    sorted_jobs = sorted(scored_jobs, key=lambda x: x["Score"], reverse=True)
    top10 = sorted_jobs[:10]
    other_jobs = sorted_jobs[10:] if len(sorted_jobs) > 10 else []
    return top10, other_jobs

@retry_request
def fetch_job_description_from_url(url: str) -> str:
    if not is_valid_url(url):
        return "Failed to fetch job description from URL: please enter a valid http or https URL."

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AI Job Agent/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        selectors = [
            "div.job-description", "div.description", "section.job-desc",
            "div#job-description", "div.jd-content", "article",
            "div[class*=job]", "div[class*=description]"
        ]
        for selector in selectors:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                return el.get_text(separator="\n", strip=True)
        return "\n".join(soup.stripped_strings)
    except Exception as e:
        return f"Failed to fetch job description from URL: {e}"

def generate_resume_and_coverletter(resume_text: str, job_description: str) -> dict:
    if llm is None:
        st.error("OpenAI API key is missing. Add OPENAI_API_KEY to your .env file.")
        return {
            "optimized_resume": "",
            "cover_letter": "",
            "analysis": {"JD Match": "N/A", "MissingKeywords": []},
        }

    prompt = f"""
You are a career assistant.

1. Rewrite the given resume to best match the provided job description.
2. Write a professional cover letter tailored to this job description using the resume details.
3. Provide a profile summary.
4. Calculate the match % between resume and job description based on keyword alignment.
5. List missing important keywords.

Respond using this exact format:

<RESUME>
[Custom resume here]
</RESUME>

<COVERLETTER>
[Custom cover letter here]
</COVERLETTER>

<JSON>
{{
  "JD Match": "X%",
  "MissingKeywords": ["keyword1", "keyword2"]
}}
</JSON>

Resume: {resume_text}

Job Description: {job_description}
"""
    messages = [SystemMessage(content="Career assistant"), HumanMessage(content=prompt)]
    result = llm.invoke(messages)

    resume_part = "No resume content found."
    cover_part = "No cover letter content found."
    json_part = {}

    resume_match = re.search(r"<RESUME>(.*?)</RESUME>", result.content, re.DOTALL)
    if resume_match:
        resume_part = resume_match.group(1).strip()

    cover_match = re.search(r"<COVERLETTER>(.*?)</COVERLETTER>", result.content, re.DOTALL)
    if cover_match:
        cover_part = cover_match.group(1).strip()

    json_match = re.search(r"<JSON>(.*?)</JSON>", result.content, re.DOTALL)
    if json_match:
        try:
            json_part = json.loads(json_match.group(1))
            # Hallucination mitigation: check if JD Match is a valid percentage
            jd_match_str = json_part.get("JD Match", "")
            if not jd_match_str or not re.match(r"^\d{1,3}%$", jd_match_str.strip()):
                st.warning("AI response seems unreliable. Please try again or revise your input.")
                json_part = {"JD Match": "N/A", "MissingKeywords": []}
        except json.JSONDecodeError:
            st.error("Failed to parse JSON from AI response.")
            json_part = {"JD Match": "N/A", "MissingKeywords": []}
    else:
        st.warning("AI response missing analysis JSON data.")
        json_part = {"JD Match": "N/A", "MissingKeywords": []}

    return {"optimized_resume": resume_part, "cover_letter": cover_part, "analysis": json_part}

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="AI Job Agent", layout="centered")
st.markdown("<h1 style='text-align: center;'>AI Job Agent</h1>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["Job Search", "Resume & Cover Letter Optimizer"])

# Tab 1: Job Search
with tab1:
    resume_file = st.file_uploader("", type=["pdf"], key="search_resume", label_visibility="visible")
    query = st.text_input("Search jobs", placeholder="e.g. AI engineer in Nepal")

    search_button_col1, search_button_col2, search_button_col3 = st.columns([1, 2, 1])
    with search_button_col2:
        search_clicked = st.button("Search Jobs", use_container_width=True)

    if search_clicked:
        if query.strip() and resume_file:
            with st.spinner("Extracting resume and searching jobs..."):
                resume_text = extract_pdf_text(resume_file)
                if not resume_text:
                    st.warning("Could not extract text from resume.")
                else:
                    job_data = job_search_serper(query)
                    job_list = job_data.get("Job Listings", [])

                    if job_list:
                        top_jobs, other_jobs = compute_job_fit_scores(resume_text, job_list)

                        st.subheader("Top 10 Matching Jobs")
                        for idx, job in enumerate(top_jobs, start=1):
                            title = html.escape(job.get("Title", "Untitled job"))
                            link = html.escape(job.get("Link", "#"), quote=True)
                            snippet = html.escape(job.get("Snippet", ""))
                            st.markdown(f"""
                                <div style='border:1px solid #ddd; padding:8px; border-radius:6px; margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,0.05);'>
                                    <h4>{idx}. <a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">{title}</a></h4>
                                    <p><strong>Match:</strong> {job['Score']}%</p>
                                    <p style='color:#555;'>{snippet}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        if other_jobs:
                            st.subheader("Other Opportunities You May Consider")
                            for idx, job in enumerate(other_jobs, start=1):
                                title = html.escape(job.get("Title", "Untitled job"))
                                link = html.escape(job.get("Link", "#"), quote=True)
                                snippet = html.escape(job.get("Snippet", ""))
                                st.markdown(f"""
                                    <div style='border:1px solid #eee; padding:8px; border-radius:6px; margin-bottom:10px;'>
                                        <h5>{idx}. <a href="{link}" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">{title}</a></h5>
                                        <p style='color:#555;'>{snippet}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.error("No jobs found.")
        else:
            st.warning("Please enter a search query and upload your resume.")

# Tab 2: Resume & Cover Letter Optimizer
with tab2:
    resume_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="optimizer_resume")
    job_url = st.text_input("Paste the Job Posting URL")
    if st.button("Generate Optimized Resume & Cover Letter"):
        if resume_file and job_url.strip():
            if not openai_api_key:
                st.error("OpenAI API key is missing. Add OPENAI_API_KEY to your .env file.")
                st.stop()
            with st.spinner("Fetching job description..."):
                job_description = fetch_job_description_from_url(job_url)
            if job_description.startswith("Failed to fetch"):
                st.error(job_description)
            else:
                resume_text = extract_pdf_text(resume_file)
                if not resume_text:
                    st.warning("Could not extract text from resume.")
                else:
                    with st.spinner("Generating documents..."):
                        response = generate_resume_and_coverletter(resume_text, job_description)
                    analysis = response.get("analysis", {})
                    st.markdown(f"**Match:** {analysis.get('JD Match', 'N/A')}")
                    st.markdown(f"**Missing Keywords:** {', '.join(analysis.get('MissingKeywords', [])) or 'None'}")
                    with st.expander("View Optimized Resume"):
                        st.text_area("Optimized Resume", response.get("optimized_resume", ""), height=400)
                    with st.expander("View Cover Letter"):
                        st.text_area("Cover Letter", response.get("cover_letter", ""), height=400)
                    resume_pdf_path = generate_pdf_from_text(response.get("optimized_resume", ""), filename="optimized_resume.pdf")
                    cover_pdf_path = generate_pdf_from_text(response.get("cover_letter", ""), filename="cover_letter.pdf")
                    col1, col2 = st.columns(2)
                    with col1:
                        with open(resume_pdf_path, "rb") as f:
                            st.download_button("Download Optimized Resume (PDF)", data=f, file_name="optimized_resume.pdf", mime="application/pdf")
                    with col2:
                        with open(cover_pdf_path, "rb") as f:
                            st.download_button("Download Cover Letter (PDF)", data=f, file_name="cover_letter.pdf", mime="application/pdf")
        else:
            st.warning("Please upload your resume and paste a valid job posting URL.")
