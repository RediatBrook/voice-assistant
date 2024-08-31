
# Voice Assistant

This project is a voice assistant that uses FastAPI for the backend and Streamlit for the frontend. It can listen to your voice commands, transcribe them, generate responses using OpenAI's GPT-4, and provide functionalities like checking the weather and sending emails.

## Features

- **Weather Information:** Get real-time weather updates for any city using the OpenWeatherMap API.
- **Email Sending:** Send emails directly through the assistant using the Resend API.
- **Voice Interaction:** Speak your commands, and the assistant will listen, transcribe, and respond.

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/voice-assistant.git
cd voice-assistant
```
### 2. Set Up Environment Variables

Ensure you have the following environment variables set in your shell:
On Mac/Linux:

```bash
export OPENWEATHERMAP_API_KEY='your_openweathermap_api_key'
export RESEND_API_KEY='your_resend_api_key'
export OPENAI_API_KEY='your_openai_api_key'
```

On Windows:

```cmd
set OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
set RESEND_API_KEY=your_resend_api_key
set OPENAI_API_KEY=your_openai_api_key
```
### 3. Install Dependencies

Ensure you have Python installed, then install the required Python packages:

```bash
pip install -r requirements.txt
```
### 4. Run the Backend

Start the FastAPI backend server:

```bash
fastapi dev app.py
```

### 5. Run the Frontend

In another terminal window, run the Streamlit frontend:

```bash
streamlit run frontend.py
```

API Endpoints
/get_weather/{city}

Fetch the weather for a specified city.

    Method: GET
    Parameters:
        city (string): Name of the city.
    Response:
        status: "success" or "failed"
        temp: Temperature in Celsius
        description: Weather description

/send_email

Send an email to a specified address.

    Method: POST
    Request Body:
        email_account (string): Receiver's email address.
        subject (string): Email subject.
        message (string): Email content.
    Response:
        status: "success" or "failure"

/generate_response

Generate a response from the GPT-4 model using voice transcriptions.

    Method: POST
    Request Body:
        model (string): The OpenAI model to use (default: "gpt-4o").
        messages (list): List of messages (roles: "user" or "assistant").
    Response:
        Returns the updated message history, including the assistant's response.

## How It Works

- **Frontend (Streamlit)**: 
Records your voice, detects speech using WebRTC VAD, and transcribes it using OpenAI's Whisper model. The transcription is then sent to the backend.

- **Backend (FastAPI)**: Processes the transcription, calls the OpenAI API to generate a response, and optionally performs actions like fetching weather data or sending an email.

- **Response Handling**: The assistant's response is sent back to the frontend, converted to speech, and played back to you.

## Environment Variables

    OPENWEATHERMAP_API_KEY: API key for OpenWeatherMap.
    RESEND_API_KEY: API key for Resend.
    OPENAI_API_KEY: API key for OpenAI.

### Commands to Set Environment Variables
Mac/Linux

```bash
export OPENWEATHERMAP_API_KEY='your_openweathermap_api_key'
export RESEND_API_KEY='your_resend_api_key'
export OPENAI_API_KEY='your_openai_api_key'
```
Windows

```cmd
set OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
set RESEND_API_KEY=your_resend_api_key
set OPENAI_API_KEY=your_openai_api_key
```

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.
License

This project is licensed under the MIT License.


