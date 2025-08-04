AI Studio
Deployed Version : https://salsa-ai-studio.streamlit.app/
<img width="1366" height="546" alt="image" src="https://github.com/user-attachments/assets/a2e66804-fbcc-4a44-ab90-ff328f5df507" />


Salsa AI Studio combines:  
📄 Document OCR: Extract handwritten or scanned text from images. 

🎤 Voice to Text & Song Guessing: Record or upload audio, transcribe lyrics, and guess song titles.

1️⃣ Before You Start
Requirements
- A working internet connection.
- Hugging Face API Key (for OCR and transcription).
- Genius API Key (for song title guessing).

How to Get API Keys
Hugging Face API Key:
- Go to https://huggingface.co/settings/tokens
- Click New Token, choose read access.
- Copy the token.

Genius API Key:
- Go to https://genius.com/api-clients
- Create a new API Client.
- Copy the Access Token.

2️⃣ Launching the App
- Open the app (either locally with streamlit run finalproject.py or on Streamlit Cloud).
- Enter your API Keys in the sidebar:
Hugging Face API Key
Genius API Key

3️⃣ Home Menu
Description of the features:
📄 Document OCR – Extract text from images.
🎤 Voice to Text & Song Guess – Record or upload audio → Transcription → Song title guessing.

4️⃣ 📄 Document OCR
Purpose: Convert handwritten or scanned images into text.
Steps:
- Click Document OCR in sidebar.
- Click Browse files or drag & drop an image (JPG/PNG).
- Once uploaded, preview appears.
- Click ▶️ Extract Text.
- Wait for processing.
- Result will appear:
Extracted text in the output box.
- Click 📄 Download as TXT to save.

5️⃣ 🎤 Voice to Text & Song Guess
Purpose: Transcribe speech or song lyrics from audio and guess song title.
Option A: Upload Existing Audio
- Click Voice to Text & Song Guess in sidebar.
- Upload .wav or .mp3 file.
- Click Process button (starts automatically in current version).
View:
- Transcribed text
- Guessed song title
Option B: Record Live Audio
- Click Voice to Text & Song Guess.
- Scroll to JS Recorder section.
- Click 🎙 Start Recording → speak/sing → Click ⏹ Stop Recording.
- Audio will appear in the playback box.
- Click Process to transcribe and guess song title.



