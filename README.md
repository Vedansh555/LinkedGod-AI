# LinkedGod AI

A Streamlit app that turns a trending headline or your own idea into a LinkedIn caption and a matching carousel PDF, using Groq's Llama 3.3 70B.

You pick a topic (pulled from an RSS feed, or typed in yourself) and a tone, and it generates a hook-first caption plus a 3-7 slide carousel, rendered as a dark-themed PDF you can upload straight to LinkedIn as a document post.

## Features

- Two ways to start a post: pull a headline from a curated RSS feed (Product Management, AI Agents, Consulting, Startup Life), or write your own idea
- Five tones (Professional, Controversial, Scary/Urgent, Motivational, Contrarian), each with its own prompt structure and sampling temperature
- Captions follow a fixed structure: a hook under 12 words, a short story with a real stat, a contrarian angle, a discussion question, and 8 hashtags split across mega/mid-tier/niche
- Carousel PDF with a custom dark design ("Obsidian" theme) that auto-sizes body text per slide so it fills the frame, with *word* highlighting for emphasis
- Slide count is adjustable, 3 to 7
- Character count shown against LinkedIn's ~210-character mobile truncation point
- Last 10 generations kept in session history
- Retries with backoff on transient API errors instead of failing outright

## How it works

1. A topic comes in, either as an RSS entry or a typed idea
2. `content_generator.py` builds a tone-specific prompt and sends it to Groq
3. The response is split into a caption and a list of slides
4. `pdf_engine.py` renders the slides into a PDF
5. The app shows the caption, hashtags, and slide previews, with a PDF download

## Project structure

```
LinkedGod-AI/
  app.py                 Streamlit UI
  config.py               RSS feeds, tone presets, model settings
  content_generator.py    Prompt building, Groq calls, response parsing
  pdf_engine.py            Carousel PDF renderer
  requirements.txt
  .env.example
```

## Tech stack

- Streamlit for the UI
- Groq (llama-3.3-70b-versatile) for generation
- ReportLab for PDF rendering
- feedparser for RSS
- python-dotenv for local API key handling

## Setup

```bash
git clone https://github.com/Vedansh555/LinkedGod-AI.git
cd LinkedGod-AI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Get a Groq API key from console.groq.com, then either:

- copy `.env.example` to `.env` and fill in `GROQ_API_KEY` (local dev), or
- add it under Streamlit Cloud's App > Settings > Secrets as `GROQ_API_KEY = "your_key_here"`

Run it:

```bash
streamlit run app.py
```

## Example

Input: "AI is changing how startups build products."

Output: a ~300-word caption with a short hook, a three-part story with a stat, a contrarian take, a question, and 8 hashtags, plus a 5-slide 1080x1350 PDF carousel.

## Notes

Slide count and RSS feeds are configured in `config.py` if you want to change what's available. History is in-memory only and resets when the app restarts. The PDF renderer only supports the one Obsidian theme right now.

## License

MIT.
