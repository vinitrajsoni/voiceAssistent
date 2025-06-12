import streamlit as st
import pyaudio
import wave
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
# 🎙 Record Audio
# -----------------------
def record_audio(filename="input.wav", duration=5):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    frames = []
    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

# -----------------------
# 🤖 Get LLM Response
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
# 🔊 Convert Text to Speech
# -----------------------
def text_to_speech(text, lang_code, filename="output.wav"):
    response = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers={"api-subscription-key": SARVAM_API_KEY},
        json={"text": text, "target_language_code": lang_code}
    )
    audio_base64 = response.json().get("audios")[0]
    with open(filename, "wb") as f:
        f.write(base64.b64decode(audio_base64))
    return audio_base64

# -----------------------
# 🚀 Streamlit App
# -----------------------
st.set_page_config(page_title="Voice AI Assistant", page_icon="🎤")
st.title("🎤 Voice AI Assistant")

if st.button("🔴 Record Voice"):
    with st.spinner("🎙 Recording 5 seconds..."):
        record_audio("input.wav", duration=5)
        st.success("✅ Recording saved as input.wav")

    st.audio("input.wav", format="audio/wav")

    # Step 2: Speech to Text
    with st.spinner("🧠 Transcribing with SarvamAI..."):
        response = requests.post(
            "https://api.sarvam.ai/speech-to-text-translate",
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": ("input.wav", open("input.wav", "rb"), "audio/wav")}
        )
        result = response.json()
        transcript = result.get("transcript")
        lang_code = result.get("language_code")

    st.success("📝 Transcription Complete")
    st.markdown(f"**Transcript:** `{transcript}`")
    st.markdown(f"**Detected Language Code:** `{lang_code}`")

    # Step 3: Langchain + Groq
    with st.spinner("🤖 Generating AI response..."):
        ai_reply = generate_response(transcript, lang_code)
        st.markdown("### 💬 AI Response")
        st.write(ai_reply)

    # Step 4: Text to Speech
    with st.spinner("🎧 Converting to speech..."):
        audio_base64 = text_to_speech(ai_reply, lang_code)
        st.success("🔊 AI Voice Response Ready!")

    # Step 5: Autoplay response
    audio_bytes = base64.b64decode(audio_base64)
    st.markdown("### 🔈 Playing AI Response")
    st.markdown(
        f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
        </audio>
        """,
        unsafe_allow_html=True
    )
