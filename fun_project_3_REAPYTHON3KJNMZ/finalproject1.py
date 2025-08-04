import streamlit as st
import requests
from PIL import Image
import io
import base64

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Salsa AI Studio", page_icon="🎯", layout="centered")
st.sidebar.title("🎯 Salsa AI Studio")

menu = st.sidebar.radio("Select Tool", ["🏠 Home", "📄 Document OCR", "🎤 Voice to Text & Song Guess"])

HF_API_KEY = st.sidebar.text_input("🔑 Hugging Face API Key", type="password")
GENIUS_API_KEY = st.sidebar.text_input("🔑 Genius API Key", type="password")

# -----------------------
# HF API CALL
# -----------------------
def hf_inference(model, data, is_json=True):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    url = f"https://api-inference.huggingface.co/models/{model}"

    if is_json:
        res = requests.post(url, headers=headers, json=data)
    else:
        res = requests.post(url, headers=headers, data=data)

    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        return {"error": res.text}

# -----------------------
# SONG GUESS FUNCTION
# -----------------------
def guess_song_from_lyrics(lyrics):
    url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {GENIUS_API_KEY}"}
    params = {"q": lyrics[:100]}
    try:
        res = requests.get(url, headers=headers, params=params)
        hits = res.json().get("response", {}).get("hits", [])
        if hits:
            return hits[0]["result"]["full_title"]
        return "Song not found"
    except Exception as e:
        return f"Error: {e}"

# -----------------------
# HOME
# -----------------------
if menu == "🏠 Home":
    st.title("🎯 Salsa AI Studio")
    st.markdown("""
    **Features:**
    - 📄 Document OCR (Handwritten or scanned text → digital text)
    - 🎤 Voice to Text (Record or upload audio → transcription → Guess Song Title)
    """)

# -----------------------
# DOCUMENT OCR (AUTO MODE)
# -----------------------
elif menu == "📄 Document OCR":
    st.title("📄 Document OCR")
    uploaded_file = st.file_uploader("📂 Upload Image", type=["jpg", "jpeg", "png"])

    if uploaded_file and HF_API_KEY:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded Document", use_container_width=True)

        with st.spinner("Extracting text..."):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            buf.seek(0)

            result = hf_inference("microsoft/trocr-base-handwritten", buf.getvalue(), is_json=False)

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                extracted_text = result[0].get("generated_text", "")
                st.subheader("📝 Extracted Text")
                st.text(extracted_text)
                st.download_button("📄 Download as TXT", extracted_text, "ocr_result.txt")

# -----------------------
# VOICE TO TEXT + SONG GUESS (AUTO MODE)
# -----------------------
elif menu == "🎤 Voice to Text & Song Guess":
    st.title("🎤 Voice to Text & Song Guess")

    # ---- JS AUDIO RECORDER ----
    st.markdown("""
        <script>
        let recorder, audioChunks;
        function startRecording(){
            navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                recorder = new MediaRecorder(stream);
                audioChunks = [];
                recorder.ondataavailable = e => audioChunks.push(e.data);
                recorder.onstop = e => {
                    const blob = new Blob(audioChunks, { type: 'audio/wav' });
                    const reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = function() {
                        const base64Audio = reader.result.split(',')[1];
                        window.parent.postMessage({type: 'audio_base64', data: base64Audio}, '*');
                    }
                };
                recorder.start();
            });
        }
        function stopRecording(){
            recorder.stop();
        }
        </script>
        <button onclick="startRecording()">🎙 Start Recording</button>
        <button onclick="stopRecording()">⏹ Stop Recording</button>
    """, unsafe_allow_html=True)

    if "audio_base64" not in st.session_state:
        st.session_state.audio_base64 = None

    uploaded_audio = st.file_uploader("📂 Or Upload Audio (MP3/WAV)", type=["wav", "mp3"])

    audio_data = None
    if uploaded_audio:
        audio_data = uploaded_audio.read()
        st.audio(audio_data)

    if st.session_state.audio_base64:
        audio_data = base64.b64decode(st.session_state.audio_base64)
        st.audio(audio_data)

    if audio_data and HF_API_KEY:
        with st.spinner("Processing audio..."):
            result = hf_inference("openai/whisper-base", audio_data, is_json=False)

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                transcription = result.get("text", "")
                st.subheader("📝 Transcribed Lyrics")
                st.write(transcription)

                guessed_song = guess_song_from_lyrics(transcription)
                st.subheader("🎵 Guessed Song")
                st.success(guessed_song)
