from fastapi import FastAPI
import requests
import os
import resend
import json
from typing import List, Optional
from pydantic import BaseModel
from openai import OpenAI

class Message(BaseModel):
    role: str
    content: str

class OpenAIRequest(BaseModel):
    model: Optional[str] = "gpt-4o"
    messages: List[Message]

class EmailRequest(BaseModel):
    email_account: str
    subject: str
    message: str

app = FastAPI()
openai_client = OpenAI()

openweathermap_api_key = os.environ["OPENWEATHERMAP_API_KEY"]
resend.api_key = os.environ["RESEND_API_KEY"]
sender_email_account = "Voice Assistant <rediat@nats.co>"


@app.get("/")
def read_root():
    return {"Content": "Welcome to the Backend of my Voice Assistant"}




@app.get("/get_weather/{city}")
def get_weather_for_city(city):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": openweathermap_api_key,
        "units": "metric"
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return {
                "status": "success",
                "temp" : temp,
                "description": description
                }
    else:
        return {
                "status": "failed",
                "message": "error: Unable to fetch weather data for {city}."
                }

@app.post('/send_email')
def send_email_to_user(email_request: EmailRequest):
    receiver_email_account = email_request.email_account
    subject = email_request.subject
    message = email_request.message

    params: resend.Emails.SendParams = {
            "from": sender_email_account,
            "to": [receiver_email_account],
            "subject": subject,
            "text": message
    }

    try:

        email = resend.Emails.send(params)
        success_response_json = {
                "status": "success",
                "receiver_email_account": receiver_email_account,
                "message": message
                }
        return success_response_json

    except Exception as err:

        print(f"Unexpected {err=}, {type(err)=}")
        failure_response_json = {
                "status": "failure",
                "receiver_email_account": receiver_email_account,
                "message": message
                }
        return failure_response_json


@app.post('/generate_response')
def generate_response_from_model(llm_request: OpenAIRequest):

    tools = [
            {
                "type": "function",
                "function":
                {
                    "name": "get_weather_for_city",
                    "description": "Get the weather for a given city. You can use to get the live weather information for the user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The city you want to know the weather of.",
                                },
                            },
                        "required": ["city"],
                        "additionalProperties": False,
                        },
                    }
                },
            {
                "type": "function",
                "function":
                {
                    "name": "send_email_to_user",
                    "description": "Send an email to a user given an email address. You can use this to email any information the user requests if they provide an email adddress.",
                    "parameters" : {
                        "type": "object",
                        "properties": {
                            "email_account" : {
                                "type": "string",
                                "description": "The email account you want to send the email to."
                                },
                            "subject" : {
                                "type": "string",
                                "description": "The subject line you want for the email."
                                },
                            "message": {
                                "type": "string",
                                "description": "The actual content/body/text of your email."
                                }
                            },
                        "required": ["email_account", "subject", "message"],
                        "additionalProperties": False,
                        }
                    },
                }
            ]

    chat_history = llm_request.messages

    completion = openai_client.chat.completions.create(
            model=llm_request.model,
            messages=chat_history,
            tools=tools
            )
    tool_calls = completion.choices[0].message.tool_calls
    if tool_calls is not None:
        for tool_call in tool_calls:

            arguments = json.loads(tool_call.function.arguments)
            function_name = tool_call.function.name

            if function_name == "get_weather_for_city":
                city = arguments.get('city')
                weather_response = get_weather_for_city(city)
                if weather_response["status"] is "success":
                    temp = weather_response["temp"]
                    description = weather_response["description"]
                    weather_message = Message(
                        role="system",
                        content=f"The temperature in {city} is {temp}°C. The weather is {description}. Respond to the user as requested."
                    )
                    chat_history.append(weather_message)
                else:
                    weather_failure_message = Message(
                            role="system",
                            content="Unable to get the weather due to technical issues."
                            )
                    chat_history.append(weather_failure_message)
                    print("Weather API Failure")

            if function_name == "send_email_to_user":
                email_account = arguments.get('email_account')
                subject = arguments.get('subject')
                message = arguments.get('message')
                email_request = EmailRequest(
                        email_account=email_account,
                        subject=subject,
                        message=message
                        )
                email_response = send_email_to_user(email_request)
                if email_response["status"] is "success":
                    email_message = Message(
                            role="system",
                            content="Email was successfully sent."
                            )
                    chat_history.append(email_message)
                else:
                    email_failure_message = Message(
                            role="systemt",
                            content="Unable to send the email to the user due to technical issues."
                            )
                    chat_history.append(email_failure_message)
                    print("Email API Failure")




        post_function_call_completion = openai_client.chat.completions.create(
            model=llm_request.model,
            messages=chat_history,
            tools=tools
            )

        if post_function_call_completion.choices[0].message.content is not None:
            post_function_call_message = Message(
                            role="assistant",
                            content=post_function_call_completion.choices[0].message.content
                        )

            chat_history.append(post_function_call_message)
    else:
        non_tool_call_message = Message(
                role="assistant",
                content=completion.choices[0].message.content
                )
        chat_history.append(non_tool_call_message)

    print(chat_history)        
    return chat_history


    

