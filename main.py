import streamlit as st
import os
from pytube import YouTube
import requests
from time import sleep

ASSEMBLY_AI_API_KEY = '1ec305ccbc00486c832b541c2d584e98'


def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data


def download_and_extract_audio(video_url, output_path):
    yt = YouTube(video_url)
    audio_stream = yt.streams.filter(only_audio=True).first()

    st.info(f"Audio downloaded to: {output_path}")

    audio_stream.download(output_path)

    audio_file_path = os.path.join(output_path, audio_stream.default_filename)
    st.success(f"✅ Audio downloaded successfully.")

    return audio_file_path, yt.title


def transcribe_yt(audio_path):
    headers = {'authorization': ASSEMBLY_AI_API_KEY}
    response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=read_file(audio_path))
    audio_url = response.json().get('upload_url')
    if not audio_url:
        st.warning(f"Error uploading file: {response.text}")
        return None

    st.info('YouTube audio file has been uploaded to AssemblyAI')
    st.text('✔️ File uploaded successfully.')

    endpoint = "https://api.assemblyai.com/v2/transcript"
    json_payload = {
        "audio_url": audio_url,
        "content_safety": True
    }
    transcript_input_response = requests.post(endpoint, json=json_payload, headers=headers)
    st.info('Transcribing uploaded file')

    if transcript_input_response.status_code != 200:
        st.warning(f"Error starting transcription: {transcript_input_response.text}")
        return None

    # Get transcript ID
    transcript_id = transcript_input_response.json().get("id")
    if not transcript_id:
        st.warning("Error retrieving transcript ID.")
        return None

    while True:
        transcript_output_response = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)

        if transcript_output_response.status_code != 200:
            st.warning(f"Error retrieving transcript progress: {transcript_output_response.text}")
            break

        response_data = transcript_output_response.json()

        if response_data.get('status') == 'completed':
            break
        elif response_data.get('status') == 'failed':
            st.warning(f"Transcription failed: {response_data.get('error_message')}")
            break

        sleep(0.5)

    if response_data.get('status') == 'completed':
        transcription_text = response_data.get('text')
        return transcription_text
    else:
        return None


def main():
    st.title("YouTube Transcription App")

    # Sidebar with input fields
    with st.sidebar:
        st.subheader("Input Options")
        video_url = st.text_input("Enter YouTube Video URL:")

        # Example URL in sidebar expander
        with st.expander('Example URL'):
            st.code('https://www.youtube.com/watch?v=twG4mr6Jov0')
            if st.button("Try This"):
                video_url = 'https://www.youtube.com/watch?v=twG4mr6Jov0'

        st.markdown("---")
        st.markdown("Developed by Shivam Pawar")

    if not video_url:
        st.warning("Please enter a valid YouTube Video URL.")
        st.stop()

    output_path = 'downloads'
    os.makedirs(output_path, exist_ok=True)
    audio_file_path, yt_title = download_and_extract_audio(video_url, output_path)

    # Display title below the YouTube Video URL input
    st.subheader(f"Title: {yt_title}")

    st.info('Processing YouTube video...')

    # Add animation (e.g., spinner) instead of progress bar
    with st.spinner("Transcribing uploaded file in progress..."):
        transcription_result = transcribe_yt(audio_file_path)

    st.subheader("Transcription Result:")
    st.write(transcription_result)

    os.remove(audio_file_path)
    st.success(f"Deleted temporary audio file: {audio_file_path}")


if __name__ == "__main__":
    main()
