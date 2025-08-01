import streamlit as st
from transformers import pipeline
from PIL import Image
from pydub import AudioSegment
import tempfile
import av
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import requests

# -----------------------
# APP CONFIG
# -----------------------
st.set_page_config(page_title="Salsa AI Studio", page_icon="🎯", layout="centered")
st.sidebar.title("🎯 Salsa AI Studio")
menu = st.sidebar.radio("Select Tool", ["🏠 Home", "📄 Document OCR", "🎤 Voice to Text & Song Guess"])

# -----------------------
# CACHE MODELS
# -----------------------
@st.cache_resource
def load_ocr_pipeline():
    return pipeline("image-to-text", model="microsoft/trocr-base-handwritten")

@st.cache_resource
def load_voice_pipeline():
    return pipeline("automatic-speech-recognition", model="openai/whisper-base", use_fast=True)

ocr_pipe = load_ocr_pipeline()
voice_pipe = load_voice_pipeline()

# -----------------------
# SONG GUESS FUNCTION (GENIUS API)
# -----------------------
def guess_song_from_lyrics(lyrics):
    base_url = "https://api.genius.com/search"
    headers = {"Authorization": "Bearer YOUR_GENIUS_API_KEY"}  # Replace with Genius API Key
    params = {"q": lyrics[:100]}  # Search first 100 chars
    try:
        res = requests.get(base_url, headers=headers, params=params)
        if res.status_code == 200:
            hits = res.json()["response"]["hits"]
            if hits:
                return hits[0]["result"]["full_title"]
            else:
                return "Song not found in Genius"
        else:
            return f"API Error: {res.status_code}"
    except Exception as e:
        return f"Error: {e}"

# -----------------------
# HOME
# -----------------------
if menu == "🏠 Home":
    st.title("🎯 Salsa AI Studio")
    st.markdown("""
**Salsa AI Studio** combines:
- 📄 **Document OCR**: Extract handwritten or scanned text from images.
- 🎤 **Voice to Text & Song Guessing**: Record or upload audio, transcribe lyrics, and guess song titles.
""")

# -----------------------
# DOCUMENT OCR
# -----------------------
elif menu == "📄 Document OCR":
    st.title("📄 Document OCR (TrOCR Pipeline)")

    uploaded_file = st.file_uploader("📂 Upload Document Image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded Document", use_container_width=True)

        if st.button("▶️ Extract Text"):
            with st.spinner("Extracting text with TrOCR..."):
                try:
                    extracted_text = ocr_pipe(image)[0]['generated_text']
                    st.subheader("📝 Extracted Text")
                    st.text(extracted_text)
                    st.download_button("📄 Download as TXT", extracted_text, "document_text.txt")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# -----------------------
# VOICE TO TEXT & SONG GUESS
# -----------------------
elif menu == "🎤 Voice to Text & Song Guess":
    st.title("🎤 Voice to Text & Song Guess")

    audio_file = st.file_uploader("🎵 Upload Audio (MP3/WAV)", type=["wav", "mp3"])
    audio_path = None

    # Handle uploaded audio
    if audio_file:
        if audio_file.name.endswith(".mp3"):
            audio = AudioSegment.from_mp3(audio_file)
            tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            audio.export(tmp_wav.name, format="wav")
            audio_path = tmp_wav.name
        else:
            tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp_wav.write(audio_file.read())
            audio_path = tmp_wav.name

    # Recorder class
    class AudioRecorder(AudioProcessorBase):
        def __init__(self):
            self.frames = []
            self.is_recording = False

        def start(self):
            self.is_recording = True
            self.frames = []

        def stop(self):
            self.is_recording = False

        def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
            if self.is_recording:
                self.frames.append(frame.to_ndarray())
            return frame

    st.subheader("🎤 Record Voice")
    st.caption("🔔 Click 'Start Recording' then 'Stop Recording' when done.")

    webrtc_ctx = webrtc_streamer(
        key="voice-recorder",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=AudioRecorder,
        media_stream_constraints={"audio": True, "video": False},
        audio_receiver_size=256
    )

    # Manual Start/Stop buttons
    if webrtc_ctx.audio_processor:
        col1, col2 = st.columns(2)
        if col1.button("▶️ Start Recording"):
            webrtc_ctx.audio_processor.start()
            st.info("Recording started...")
        if col2.button("⏹ Stop Recording"):
            webrtc_ctx.audio_processor.stop()
            st.success("Recording stopped.")

    # Process recorded audio
    if webrtc_ctx.audio_processor and not webrtc_ctx.audio_processor.is_recording and webrtc_ctx.audio_processor.frames:
        all_audio = np.concatenate(webrtc_ctx.audio_processor.frames, axis=0)
        tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        AudioSegment(
            all_audio.tobytes(),
            frame_rate=16000,
            sample_width=all_audio.dtype.itemsize,
            channels=1
        ).export(tmp_wav.name, format="wav")
        audio_path = tmp_wav.name

    # Auto-transcribe & guess
    if audio_path:
        with st.spinner("Processing audio..."):
            try:
                text_result = voice_pipe(audio_path)
                transcription = text_result['text']
                st.subheader("📝 Transcribed Lyrics")
                st.write(transcription)

                guessed_song = guess_song_from_lyrics(transcription)
                st.subheader("🎵 Guessed Song Title")
                st.success(guessed_song)
            except Exception as e:
                st.error(f"❌ Error: {e}")
