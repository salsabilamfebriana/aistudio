import streamlit as st
import requests
import base64
from PIL import Image
import io

# -----------------------
# APP CONFIG
# -----------------------
st.set_page_config(page_title="Salsa AI Studio", page_icon="🎯", layout="centered")
st.sidebar.title("🎯 Salsa AI Studio")

# Hugging Face API Key and Genius API Key
HF_API_KEY = st.sidebar.text_input("🔑 Hugging Face API Key (Optional)", type="password")
GENIUS_API_KEY = st.sidebar.text_input("🎵 Genius API Key (Optional)", type="password")

menu = st.sidebar.radio("Select Tool", ["🏠 Home", "📄 Document OCR", "🎤 Voice to Text & Song Guess"])

# -----------------------
# Helper: Call Hugging Face API
# -----------------------
def hf_inference(model, data, is_json=True):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    url = f"https://api-inference.huggingface.co/models/{model}"
    if is_json:
        response = requests.post(url, headers=headers, json=data)
    else:
        response = requests.post(url, headers=headers, data=data)
    return response.json()

# -----------------------
# Guess Song from Genius
# -----------------------
def guess_song_from_lyrics(lyrics):
    if not GENIUS_API_KEY:
        return "⚠️ Genius API Key not provided."
    base_url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {GENIUS_API_KEY}"}
    params = {"q": lyrics[:100]}
    res = requests.get(base_url, headers=headers, params=params)
    if res.status_code == 200:
        hits = res.json()["response"]["hits"]
        if hits:
            return hits[0]["result"]["full_title"]
        else:
            return "Song not found."
    else:
        return f"API Error: {res.status_code}"

# -----------------------
# HOME
# -----------------------
if menu == "🏠 Home":
    st.title("🎯 Salsa AI Studio")
    st.markdown("""
    - 📄 **Document OCR** → Extract text from images using TrOCR  
    - 🎤 **Voice to Text & Song Guess** → Record or upload audio, transcribe with Whisper, guess song title with Genius  
    """)

# -----------------------
# DOCUMENT OCR
# -----------------------
elif menu == "📄 Document OCR":
    st.title("📄 Document OCR with TrOCR")
    uploaded_file = st.file_uploader("📂 Upload Document Image", type=["jpg", "jpeg", "png"])
    if uploaded_file and HF_API_KEY:
        image = Image.open(uploaded_file).convert("RGB")
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()
        
        with st.spinner("Extracting text..."):
            result = hf_inference("microsoft/trocr-base-handwritten", image_bytes, is_json=False)
            if isinstance(result, list) and "generated_text" in result[0]:
                extracted_text = result[0]["generated_text"]
                st.subheader("📝 Extracted Text")
                st.text(extracted_text)
                st.download_button("📄 Download as TXT", extracted_text, "document_text.txt")
            else:
                st.error(f"❌ Error: {result}")

# -----------------------
# VOICE TO TEXT & SONG GUESS
# -----------------------
elif menu == "🎤 Voice to Text & Song Guess":
    st.title("🎤 Voice to Text & Song Guess")

    # Upload audio
    audio_file = st.file_uploader("🎵 Upload Audio", type=["wav", "mp3"])
    
    # JS-based Recorder
    st.markdown("""
    <script>
    async function recordAudio() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        let chunks = [];
        mediaRecorder.ondataavailable = e => chunks.push(e.data);
        mediaRecorder.onstop = e => {
            const blob = new Blob(chunks, { type: 'audio/wav' });
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64Audio = reader.result.split(',')[1];
                window.parent.postMessage({ type: 'audio', data: base64Audio }, '*');
            };
            reader.readAsDataURL(blob);
        };
        mediaRecorder.start();
        setTimeout(() => mediaRecorder.stop(), 5000); // Record for 5 seconds
    }
    </script>
    <button onclick="recordAudio()">🎤 Start Recording (5s)</button>
    """, unsafe_allow_html=True)

    # Receive recorded audio
    audio_base64 = st.session_state.get("recorded_audio", None)
    if audio_base64:
        audio_bytes = base64.b64decode(audio_base64)
        st.audio(audio_bytes, format="audio/wav")
        audio_file = io.BytesIO(audio_bytes)

    if audio_file and HF_API_KEY:
        with st.spinner("Processing audio..."):
            result = hf_inference("openai/whisper-base", audio_file.read(), is_json=False)
            if "text" in result:
                transcription = result["text"]
                st.subheader("📝 Transcribed Lyrics")
                st.write(transcription)
                
                song_guess = guess_song_from_lyrics(transcription)
                st.subheader("🎵 Guessed Song Title")
                st.success(song_guess)
            else:
                st.error(f"❌ Error: {result}")
