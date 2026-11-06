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
    layout="wide",
)

with st.container(horizontal=True, vertical_alignment="center"):
    st.badge("Private by design", icon=":material/lock:", color="blue")
    st.badge("Human review required", icon=":material/visibility:", color="gray")

hero_copy, hero_note = st.columns([1.65, 1], gap="large", vertical_alignment="center")
with hero_copy:
    st.title("Know what your timeline says.", icon=":material/fact_check:")
    st.markdown(
        "Turn years of old posts into a focused, private review queue. You choose the rules; "
        "Tweet Audit finds what deserves a second look."
    )
    st.caption("No X login. No automatic deletion. Your final call, every time.")
with hero_note, st.container(border=True):
    st.markdown("**The review contract**")
    st.markdown(
        ":material/upload_file: You provide one archive  \n"
        ":material/rule: You define what no longer fits  \n"
        ":material/download: You leave with a reviewable CSV"
    )

st.space("small")
st.subheader("From archive to evidence", icon=":material/route:")
workflow = st.columns(3, gap="medium")
steps = [
    ("01 · Intake", "Upload `data/tweets.js` from your X archive.", "upload_file"),
    ("02 · Inspect", "Gemini checks each post against your rules.", "manage_search"),
    ("03 · Decide", "Download the shortlist and review it yourself.", "task_alt"),
]
for column, (label, copy, icon) in zip(workflow, steps, strict=True):
    with column.container(border=True, height="stretch"):
        st.markdown(f":material/{icon}: **{label}**")
        st.caption(copy)

with st.form("audit_form", border=True):
    st.subheader("Build your review brief", icon=":material/tune:")
    st.caption("Everything below is used only for this review session.")
    identity, access = st.columns(2, gap="large")
    with identity:
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
    with access:
        api_key = st.text_input(
            "Gemini API key",
            type="password",
            help="Used for this run and never written to disk by the app.",
        )
        st.caption(
            "Create a key in Google AI Studio. The key stays masked and is not added to the CSV."
        )

    review_focus = st.pills(
        "Quick review focus",
        ["Professional tone", "Sensitive information", "Outdated views", "Harassment"],
        selection_mode="multi",
        default=["Professional tone", "Sensitive information"],
        help="Choose common checks, then add your own instructions below.",
    )
    rules, words = st.columns([1.5, 1], gap="large", vertical_alignment="bottom")
    with rules:
        review_instructions = st.text_area(
            "Your review instructions",
            placeholder="Flag posts that no longer represent how I want to show up online.",
            height=120,
        )
    with words:
        forbidden_words = st.text_input(
            "Specific words to flag",
            placeholder="word one, word two",
        )
        st.caption("Separate words or phrases with commas.")

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
    if not review_focus and not review_instructions.strip() and not forbidden_words.strip():
        missing.append("at least one review rule")

    if missing:
        st.error("Please provide " + ", ".join(missing) + ".", icon=":material/error:")
    else:
        criteria = {
            "review_focus": review_focus,
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
                st.success("Your evidence file is ready.", icon=":material/check_circle:")
                summary = st.columns(3)
                summary[0].metric("Posts reviewed", len(tweets))
                summary[1].metric("Posts flagged", flagged_count)
                review_rate = round((flagged_count / len(tweets)) * 100, 1) if tweets else 0
                summary[2].metric("Review rate", f"{review_rate}%")
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

with st.expander("Privacy, cost, and limitations", icon=":material/privacy_tip:"):
    st.markdown(
        "Your uploaded archive and API key are not saved by this app. Post text is sent to "
        "Google Gemini for analysis, and Gemini usage may count toward your API quota."
    )
