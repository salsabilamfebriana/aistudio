import streamlit as st
from PIL import Image
import tempfile
import requests
import base64
from transformers import pipeline

# -----------------------
# APP CONFIG
# -----------------------
st.set_page_config(page_title="Salsa AI Studio", page_icon="🎯", layout="centered")
st.sidebar.title("🎯 Salsa AI Studio")
menu = st.sidebar.radio("Select Tool", ["🏠 Home", "📄 Document OCR", "🎤 Voice to Text & Song Guess"])

# -----------------------
# LOAD MODELS
# -----------------------
@st.cache_resource
def load_ocr_pipeline():
    return pipeline(
        "image-to-text",
        model="microsoft/trocr-small-handwritten"
    )

@st.cache_resource
def load_voice_pipeline():
    return pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-tiny"
    )

ocr_pipe = load_ocr_pipeline()
voice_pipe = load_voice_pipeline()

# -----------------------
# SONG GUESS FUNCTION
# -----------------------
GENIUS_API_KEY = "YOUR_GENIUS_API_KEY"

def guess_song_from_lyrics(lyrics):
    base_url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {GENIUS_API_KEY}"}
    params = {"q": lyrics[:100]}
    res = requests.get(base_url, headers=headers, params=params)
    if res.status_code == 200:
        hits = res.json()["response"]["hits"]
        return hits[0]["result"]["full_title"] if hits else "Song not found"
    else:
        return f"API Error: {res.status_code}"

# -----------------------
# HOME
# -----------------------
if menu == "🏠 Home":
    st.title("🎯 Salsa AI Studio")
    st.markdown("""
    - 📄 **Document OCR**: Extract text from handwritten docs.
    - 🎤 **Voice to Text & Song Guess**: Record or upload audio to transcribe and guess.
    """)

# -----------------------
# DOCUMENT OCR
# -----------------------
elif menu == "📄 Document OCR":
    st.title("📄 Document OCR")
    uploaded_file = st.file_uploader("📂 Upload Image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded", use_container_width=True)

        if st.button("▶️ Extract Text"):
            with st.spinner("Extracting text..."):
                text = ocr_pipe(image)[0]['generated_text']
                st.text(text)
                st.download_button("📄 Download TXT", text, "ocr_text.txt")

# -----------------------
# VOICE TO TEXT & SONG GUESS
# -----------------------
elif menu == "🎤 Voice to Text & Song Guess":
    st.title("🎤 Voice to Text & Song Guess")
    audio_path = None

    # Upload WAV/MP3 (no pydub conversion)
    audio_file = st.file_uploader("🎵 Upload Audio (WAV preferred)", type=["wav", "mp3"])
    if audio_file:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}")
        tmp.write(audio_file.read())
        audio_path = tmp.name

    # Browser Recorder
    st.markdown("🎙️ **Record Voice** (Browser-based)")
    audio_recorder_html = """
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
    function stopRecording() { mediaRecorder.stop(); }
    </script>
    <button onclick="startRecording()">🎙️ Start Recording</button>
    <button onclick="stopRecording()">⏹️ Stop Recording</button>
    """
    recorded_base64 = st.text_input("Recorded Audio (hidden)", type="default", label_visibility="hidden")
    st.components.v1.html(audio_recorder_html, height=100)

    if recorded_base64:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.write(base64.b64decode(recorded_base64))
        audio_path = tmp.name
        st.success("✅ Voice recorded.")

    # Process
    if audio_path and st.button("▶️ Transcribe & Guess"):
        with st.spinner("Processing audio..."):
            text = voice_pipe(audio_path)['text']
            st.subheader("📝 Lyrics")
            st.write(text)

            guessed = guess_song_from_lyrics(text)
            st.subheader("🎵 Song Title")
            st.success(guessed)
