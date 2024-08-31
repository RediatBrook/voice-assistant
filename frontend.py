import pyaudio
import audioop
import wave
import webrtcvad
import collections
import streamlit as st
import requests
import time
from openai import OpenAI

# Constants for WebRTC VAD
SAMPLE_RATE = 16000  # 16kHz
CHANNELS = 1  # Mono
SAMPLE_WIDTH = 2  # 16-bit
FRAME_DURATION_MS = 30  # 30ms frame duration
CHUNK = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # samples per frame

# VAD parameters
VAD_MODE = 3  # Aggressiveness mode (0-3)
SILENT_CHUNKS = 50  # Number of silent chunks before stopping
VOICE_CHUNKS = 2  # Number of voice chunks before starting

# Output file parameters
WAVE_OUTPUT_FILENAME = "output.wav"

# Initialize PyAudio and WebRTC VAD
p = pyaudio.PyAudio()
vad = webrtcvad.Vad(VAD_MODE)

st.title('Voice Assistant')

# Initialize Streamlit elements
transcription_text = st.empty()  # Container for displaying transcription
listening_text = st.empty()  # Container for displaying "Listening for speech..."
processing_text = st.empty()  # Container for displaying "Processing..." message

if 'messages' not in st.session_state:
    st.session_state["messages"] = []

def record_and_transcribe():
    """Record audio and transcribe it using OpenAI's Whisper model."""
    stream = p.open(format=p.get_format_from_width(SAMPLE_WIDTH),
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    voiced_frames = []
    ring_buffer = collections.deque(maxlen=VOICE_CHUNKS)
    silence_buffer = collections.deque(maxlen=SILENT_CHUNKS)
    triggered = False

    while True:
        data = stream.read(CHUNK)
        # Convert to mono if necessary
        if p.get_sample_size(p.get_format_from_width(SAMPLE_WIDTH)) != SAMPLE_WIDTH:
            data = audioop.lin2lin(data, p.get_sample_size(p.get_format_from_width(SAMPLE_WIDTH)), SAMPLE_WIDTH)
        if CHANNELS != 1:
            data = audioop.tomono(data, SAMPLE_WIDTH, 1, 0)

        is_speech = vad.is_speech(data, SAMPLE_RATE)

        if not triggered:
            ring_buffer.append(data)
            if len([f for f in ring_buffer if vad.is_speech(f, SAMPLE_RATE)]) >= VOICE_CHUNKS:
                triggered = True
                listening_text.text('Speech detected, recording...')
                voiced_frames.extend(ring_buffer)
                ring_buffer.clear()
        else:
            voiced_frames.append(data)
            silence_buffer.append(data)

            if not vad.is_speech(data, SAMPLE_RATE) and len(silence_buffer) == SILENT_CHUNKS:
                listening_text.empty()  # Clear the "Speech detected" message
                break
            elif vad.is_speech(data, SAMPLE_RATE):
                silence_buffer.clear()

    # Stop and close the stream
    stream.stop_stream()
    stream.close()

    # Save the detected speech to a WAV file
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(SAMPLE_WIDTH)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(voiced_frames))
    wf.close()

    client = OpenAI()
    audio_file = open(WAVE_OUTPUT_FILENAME, "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )

    transcribed_text = transcription.text
    if transcribed_text.strip():
        transcription_text.text(f"User: {transcribed_text}")  # Update the Streamlit container with the transcription

        # Append the transcribed text to the messages array with role 'user'
        st.session_state["messages"].append({"role": "user", "content": transcribed_text})

        # Send the transcribed text to the FastAPI endpoint
        api_endpoint = "http://localhost:8000/generate_response"
        payload = {
            "model": "gpt-4o",
            "messages": st.session_state["messages"]
        }

        # Send the request and show "Processing..." message
        processing_text.text("Assistant is processing...")  # Show "Processing" message
        response = requests.post(api_endpoint, json=payload)
        
        if response.status_code == 200:
            response_data = response.json()

            # Extract the last assistant message from the chat history
            assistant_response = None
            for message in reversed(response_data):
                if message['role'] == 'assistant':
                    assistant_response = message['content']
                    break

            processing_text.empty()  # Clear "Processing..." message

            if assistant_response:
                st.write(f"Assistant: {assistant_response}")
                # Append the assistant's response to the messages array
                st.session_state["messages"].append({"role": "assistant", "content": assistant_response})

                # Convert assistant response to speech and play it
                speech_file_path = "speech.mp3"
                tts_response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=assistant_response
                )
                tts_response.stream_to_file(speech_file_path)

                # Use Streamlit audio component to autoplay the response
                st.audio(speech_file_path, format="audio/mp3", autoplay=True)
            else:
                st.write("Assistant response not found.")
        else:
            processing_text.empty()  # Clear "Processing..." message
            st.write("Failed to get response from the assistant.")

while True:
    record_and_transcribe()

