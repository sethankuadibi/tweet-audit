from __future__ import annotations

import asyncio

import streamlit as st

from tweet_audit.archive import parse_tweets
from tweet_audit.client import GeminiClient, GeminiError
from tweet_audit.models import Settings
from tweet_audit.service import build_flagged_csv, process_tweets


class MemoryCheckpoint:
    """Per-session checkpoint for the browser workflow; nothing is written to disk."""

    def __init__(self) -> None:
        self.results = {}

    def save(self, result) -> None:
        self.results[result.tweet_id] = result


async def audit_upload(content: str, settings: Settings):
    tweets = parse_tweets(content)
    checkpoint = MemoryCheckpoint()
    async with GeminiClient(
        settings.gemini_api_key,
        settings.gemini_model,
        settings.max_retries,
    ) as client:
        results = await process_tweets(tweets, settings, client, checkpoint)
    return tweets, results


st.set_page_config(
    page_title="Tweet Audit",
    page_icon=":material/fact_check:",
    layout="centered",
)

st.title("Review your old posts", icon=":material/fact_check:")
st.markdown(
    "Upload your X archive, choose what you want to review, and download a private checklist. "
    "Nothing is deleted automatically."
)

with st.container(border=True):
    st.subheader("How it works", icon=":material/route:")
    st.markdown(
        "1. Upload `data/tweets.js` from your X archive.  \n"
        "2. Gemini checks each post against your rules.  \n"
        "3. Download a CSV and review every suggestion yourself."
    )

with st.form("audit_form", border=True):
    st.subheader("Set up your review", icon=":material/tune:")
    archive = st.file_uploader(
        "X archive file",
        type=["js", "json"],
        help="Upload data/tweets.js from the archive downloaded from X.",
    )
    username = st.text_input(
        "X username",
        placeholder="your_username",
        help="Used only to create links in the downloaded CSV.",
    )
    api_key = st.text_input(
        "Gemini API key",
        type="password",
        help="Used for this run and never written to disk by the app.",
    )
    review_instructions = st.text_area(
        "What should be flagged?",
        placeholder=(
            "Flag posts that contain unprofessional language, reveal sensitive information, "
            "or no longer represent my current views."
        ),
        height=120,
    )
    forbidden_words = st.text_input(
        "Words to flag (optional)",
        placeholder="word one, word two",
    )

    with st.expander("Advanced settings", icon=":material/settings:"):
        concurrency = st.slider("Simultaneous checks", 1, 10, 4)
        model = st.selectbox(
            "Gemini model",
            ["gemini-2.5-flash", "gemini-2.5-pro"],
        )

    submitted = st.form_submit_button(
        "Start review",
        type="primary",
        icon=":material/play_arrow:",
        width="stretch",
    )

if submitted:
    missing = []
    if archive is None:
        missing.append("an X archive file")
    if not username.strip():
        missing.append("your X username")
    if not api_key.strip():
        missing.append("a Gemini API key")
    if not review_instructions.strip() and not forbidden_words.strip():
        missing.append("at least one review rule")

    if missing:
        st.error("Please provide " + ", ".join(missing) + ".", icon=":material/error:")
    else:
        criteria = {
            "instructions": review_instructions.strip(),
            "forbidden_words": [
                word.strip() for word in forbidden_words.split(",") if word.strip()
            ],
        }
        settings = Settings(
            username=username.strip().lstrip("@"),
            gemini_api_key=api_key,
            criteria=criteria,
            gemini_model=model,
            concurrency=concurrency,
            batch_size=max(10, concurrency * 2),
            max_retries=4,
        )
        try:
            content = archive.getvalue().decode("utf-8-sig")
            with st.status("Reviewing posts…", expanded=True) as status:
                st.write("Reading your archive")
                tweets, results = asyncio.run(audit_upload(content, settings))
                st.write("Preparing your review file")
                csv_content, flagged_count = build_flagged_csv(results, settings.username)
                status.update(label="Review complete", state="complete", expanded=False)

            with st.container(border=True):
                st.success("Your review is ready.", icon=":material/check_circle:")
                summary = st.columns(2)
                summary[0].metric("Posts reviewed", len(tweets))
                summary[1].metric("Posts flagged", flagged_count)
                st.download_button(
                    "Download review CSV",
                    data=csv_content,
                    file_name="flagged_tweets.csv",
                    mime="text/csv",
                    icon=":material/download:",
                    type="primary",
                    width="stretch",
                )
                st.caption("Review every suggestion before deleting anything on X.")
        except (GeminiError, UnicodeDecodeError, TypeError, ValueError) as exc:
            st.error(
                "The review could not finish. Check your API key and try again. "
                f"Technical detail: {exc}",
                icon=":material/error:",
            )

with st.expander("Privacy and costs", icon=":material/privacy_tip:"):
    st.markdown(
        "Your uploaded archive and API key are not saved by this app. Post text is sent to "
        "Google Gemini for analysis, and Gemini usage may count toward your API quota."
    )
