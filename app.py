import streamlit as st
import requests
import base64
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

# -----------------------
# 🔐 API KEYS (REPLACE)
# -----------------------
SARVAM_API_KEY = "sk_itu4hqil_JQ3BzkQfN7wGeiZiDoLYZmVr"
GROQ_API_KEY = "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"

# -----------------------
# 📁 Save uploaded audio
# -----------------------
def save_uploaded_file(uploaded_file, filename="input.wav"):
    with open(filename, "wb") as f:
        f.write(uploaded_file.read())

# -----------------------
# 🤖 Generate LLM Response
# -----------------------
def generate_response(data, lang):
    prompt = PromptTemplate.from_template("""
    Answer the following in {language} language in 50 words:
    {data}
    """)
    llm = ChatGroq(
        temperature=0,
        model_name="llama3-70b-8192",
        api_key=GROQ_API_KEY
    )
    chain = prompt | llm
    result = chain.invoke({"data": data, "language": lang})
    return result.content

# -----------------------
# 🔊 Text to Speech
# -----------------------
def text_to_speech(text, lang_code):
    response = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers={"api-subscription-key": SARVAM_API_KEY},
        json={"text": text, "target_language_code": lang_code}
    )
    audio_base64 = response.json().get("audios")[0]
    with open("output.wav", "wb") as f:
        f.write(base64.b64decode(audio_base64))
    return audio_base64

# -----------------------
# 🚀 Streamlit UI
# -----------------------
st.set_page_config(page_title="Voice Assistant", layout="centered")
st.title("🎤 Voice Assistant")

uploaded_audio = st.file_uploader("Upload audio from browser mic", type=["wav"])

if uploaded_audio:
    save_uploaded_file(uploaded_audio)

    # Step 1: Speech to Text
    with st.spinner("🧠 Transcribing..."):
        response = requests.post(
            "https://api.sarvam.ai/speech-to-text-translate",
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": ("input.wav", open("input.wav", "rb"), "audio/wav")}
        )
        result = response.json()
        transcript = result.get("transcript")
        lang_code = result.get("language_code")

    st.success("✅ Transcription Complete")
    st.markdown(f"**Transcript:** `{transcript}`")
    st.markdown(f"**Detected Language Code:** `{lang_code}`")

    # Step 2: Generate AI Response
    with st.spinner("🤖 Generating response..."):
        ai_reply = generate_response(transcript, lang_code)
        st.markdown("### 💬 AI Response")
        st.write(ai_reply)

    # Step 3: Text to Speech + Autoplay
    with st.spinner("🎧 Converting to speech..."):
        audio_base64 = text_to_speech(ai_reply, lang_code)
        st.success("🔊 AI Voice Ready")

    st.markdown("### 🔈 Playing AI Response")
    st.markdown(
        f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            Your browser does not support the audio element.
        </audio>
        """,
        unsafe_allow_html=True
    )
