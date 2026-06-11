# Recruiter Assistant

A batch CV screening and ranking tool that analyzes multiple candidates against a job description, built with Claude API.

## What it does
Upload a folder of CVs, paste a job description, and get a ranked shortlist with competency scores, strengths, gaps, and hire/maybe/pass recommendations for each candidate.

## Sample output
- Ranked shortlist table across all candidates
- Competency scores: technical, experience, education, soft skills
- Top strength and top gap per candidate
- Hire / maybe / pass recommendation

## Tech stack
- Python
- Anthropic Claude API (claude-haiku-4-5)
- python-docx (Word CV extraction)
- PyMuPDF (PDF CV extraction)
- Google Colab
- Google Drive (CV folder
