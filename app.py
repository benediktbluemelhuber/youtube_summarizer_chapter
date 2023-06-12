import argparse
import os
import tempfile
import time
from functools import wraps
from shutil import rmtree
import yaml
import openai
import streamlit as st
import streamlit_authenticator as stauth
from audio_to_text import transcribe_audio
from text_summary import (align_chapters, get_automatic_chapters,
                          summarize_chapters)
from youtube_extraction import get_youtube_chapters, youtube_to_audio
from utils import get_config, upload_blob_to_gcs
from send_mail import send_mail, send_mail_password_change


def timing_decorator(message):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with st.spinner(message):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                st.write(f"{message} complete - {end_time - start_time:.2f}s")
                return result

        return wrapper

    return decorator


@timing_decorator("Downloading Youtube video")
def download_youtube(youtube_url, work_dir):
    audio_fpath = youtube_to_audio(youtube_url, work_dir)
    # Get Youtube chapters, return empty list if is not in metadata
    yt_chapters = get_youtube_chapters(youtube_url)
    return audio_fpath, yt_chapters


@timing_decorator("Transcribing audio")
def audio_to_text(audio_fpath):
    # Transcribe video with Whisper
    timestamped_text = transcribe_audio(audio_fpath)
    return timestamped_text


@timing_decorator("Retrieving chapters")
def retrieve_chapters(timestamped_text, yt_chapters, openai_api_key):
    # Get chapters
    if len(yt_chapters) == 0:
        chapters = get_automatic_chapters(timestamped_text, openai_api_key)
    else:
        chapters = align_chapters(timestamped_text, yt_chapters)
    return chapters


@timing_decorator("Summarizing video")
def summarize_youtube_chapters(chapters, openai_api_key):
    # Summarize chapters
    summarized_chapters = summarize_chapters(chapters, openai_api_key)
    return summarized_chapters


def get_work_dir():
    temp_dir = tempfile.TemporaryDirectory()
    work_dir = temp_dir.name
    return work_dir


def convert_seconds(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int((seconds % 3600) % 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def summarize_video(youtube_url):
    st.video(youtube_url)
    # Create a temporary directory to store the audio file
    work_dir = get_work_dir()

    # Summarize the video
    audio_fpath, yt_chapters = download_youtube(youtube_url, work_dir)
    timestamped_text = audio_to_text(audio_fpath)

    chapters = retrieve_chapters(timestamped_text, yt_chapters, openai.api_key)
    summarized_chapters, overall_summary = summarize_youtube_chapters(
        chapters, openai.api_key
    )

    st.write(f"**TLDR:** {overall_summary}")

    for summarized_chapter in summarized_chapters:
        start_time = convert_seconds(summarized_chapter["start"])
        end_time = convert_seconds(summarized_chapter["end"])

        timestamp = f"{start_time} - {end_time}"
        title = summarized_chapter["title"]
        summary = summarized_chapter["summary"]

        # Display the hyperlink with timestamp and title
        hyperlink = (
            f"[{timestamp} - {title}]({youtube_url}&t={summarized_chapter['start']}s)"
        )
        st.markdown(hyperlink, unsafe_allow_html=True)

        st.write(summary)
    rmtree(work_dir)

current_config = None


def app():
    global current_config
    st.set_page_config(page_title="TCW Prof Transcriber", layout="wide")
    # Load secrets from secrets.toml
    bucket_name = st.secrets["gcs"]["bucket_name"]
    blob_name = st.secrets["gcs"]["blob_name"]

    # Get the config
    config = get_config(bucket_name, blob_name)

    # Update the current configuration if it has changed
    if config != current_config:
        # update the global variable
        current_config = config
        # Write the updated configuration to a file
        with open('config.yaml', 'w') as file:
            yaml.dump(current_config, file, default_flow_style=False)

        # Upload the file back to GCS
        upload_blob_to_gcs(bucket_name, 'config.yaml', blob_name)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status == False:
        st.error("Username/password is incorrect")
        try:
            username_forgot_pw, email_forgot_password, random_password = authenticator.forgot_password(
                'Forgot password')
            if username_forgot_pw:
                send_mail(email_forgot_password, random_password)
                st.success('New password sent securely and e-mail sent')
                # Random password to be transferred to user securely
                with open('config.yaml', 'w') as file:
                    yaml.dump(current_config, file, default_flow_style=False)

                # Upload the file back to GCS
                upload_blob_to_gcs(bucket_name, 'config.yaml', blob_name)
            else:
                st.error('Username not found')
        except Exception as e:
            st.error(e)

    if authentication_status == None:
        st.warning("Please enter your username and password")


    if authentication_status:
        st.title("Video Summarizer")
        openai.api_key = st.secrets["api_key"]
        if openai.api_key is None:
            openai.api_key = st.text_input("OPENAI_API_KEY")

        youtube_url = st.text_input("Enter a YouTube URL")

        # Add summarize button
        summarize_button = st.button("Summarize")

        if summarize_button:
            summarize_video(youtube_url)


if __name__ == "__main__":
    app()
