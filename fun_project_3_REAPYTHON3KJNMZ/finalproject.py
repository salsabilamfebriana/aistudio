import streamlit as st
from PIL import Image
import tempfile
import numpy as np
from pydub import AudioSegment
import requests
import base64
import shutil

# -----------------------
# APP CONFIG
# -----------------------
st.set_page_config(page_title="Salsa AI Studio", page_icon="🎯", layout="centered")
st.sidebar.title("🎯 Salsa AI Studio")
menu = st.sidebar.radio("Select Tool", ["🏠 Home", "📄 Document OCR", "🎤 Voice to Text & Song Guess"])

# -----------------------
# CHECK FFmpeg
# -----------------------
if shutil.which("ffmpeg") is None:
    st.sidebar.error("⚠️ FFmpeg not found. Audio conversion may not work.")

# -----------------------
# LOAD MODELS
# -----------------------
try:
    from transformers import pipeline
    
    @st.cache_resource
    def load_ocr_pipeline():
        return pipeline(
            "image-to-text",
            model="microsoft/trocr-small-handwritten",
            tokenizer="microsoft/trocr-small-handwritten",
            feature_extractor="microsoft/trocr-small-handwritten",
            use_fast=True
        )

    @st.cache_resource
    def load_voice_pipeline():
        return pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-tiny",
            use_fast=True
        )

    ocr_pipe = load_ocr_pipeline()
    voice_pipe = load_voice_pipeline()
    model_error = None
except Exception as e:
    ocr_pipe = None
    voice_pipe = None
    model_error = str(e)

# -----------------------
# SONG GUESS FUNCTION
# -----------------------
GENIUS_API_KEY = "YOUR_GENIUS_API_KEY"  # Replace with real Genius API key

def guess_song_from_lyrics(lyrics):
    base_url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {GENIUS_API_KEY}"}
    params = {"q": lyrics[:100]}
    try:
        res = requests.get(base_url, headers=headers, params=params)
        if res.status_code == 200:
            hits = res.json()["response"]["hits"]
            if hits:
                return hits[0]["result"]["full_title"]
            else:
                return "Song not found"
        else:
            return f"API Error: {res.status_code}"
    except Exception as e:
        return f"Error: {e}"

# -----------------------
# HOME PAGE
# -----------------------
if menu == "🏠 Home":
    st.title("🎯 Salsa AI Studio")
    if model_error:
        st.warning(f"⚠️ Some features disabled: {model_error}")
    st.markdown("""
**Features:**
- 📄 Document OCR
- 🎤 Voice to Text & Song Guess
""")

# -----------------------
# DOCUMENT OCR
# -----------------------
elif menu == "📄 Document OCR":
    st.title("📄 Document OCR")
    if ocr_pipe is None:
        st.error("❌ OCR model not loaded.")
    else:
        uploaded_file = st.file_uploader("📂 Upload Image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, caption="Uploaded", use_container_width=True)

            if st.button("▶️ Extract Text"):
                with st.spinner("Extracting text..."):
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
    if voice_pipe is None:
        st.error("❌ Voice model not loaded.")
    else:
        audio_path = None
        
        # Upload Audio
        audio_file = st.file_uploader("🎵 Upload Audio", type=["wav", "mp3"])
        if audio_file:
            if audio_file.name.endswith(".mp3"):
                audio = AudioSegment.from_mp3(audio_file)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                audio.export(tmp.name, format="wav")
                audio_path = tmp.name
            else:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                tmp.write(audio_file.read())
                audio_path = tmp.name

        st.markdown("---")
        st.subheader("🎤 Record Voice (No extra deps)")

        # JavaScript Recorder
        audio_recorder_code = """
        <script>
        let mediaRecorder;
        let audioChunks = [];
        async function startRecording() {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = e => { audioChunks.push(e.data); };
            mediaRecorder.onstop = e => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64data = reader.result.split(',')[1];
                    const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
                    input.value = base64data;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                };
                reader.readAsDataURL(audioBlob);
            };
            mediaRecorder.start();
        }
        function stopRecording() {
            mediaRecorder.stop();
        }
        </script>
        <button onclick="startRecording()">🎙️ Start Recording</button>
        <button onclick="stopRecording()">⏹️ Stop Recording</button>
        """
        
        recorded_base64 = st.text_input("Recorded Audio (hidden)", type="default", label_visibility="hidden")
        st.components.v1.html(audio_recorder_code, height=100)

        if recorded_base64:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp.write(base64.b64decode(recorded_base64))
            audio_path = tmp.name
            st.success("✅ Voice recorded successfully.")

        # Process audio
        if audio_path and st.button("▶️ Transcribe & Guess"):
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
