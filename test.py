

import base64
from io import BytesIO
import pyautogui
from dotenv import load_dotenv
from openai import OpenAI
import json


load_dotenv()

client = OpenAI()

def call_vision_api(inp_text):
    PROMPT = """
    You are an intelligent bot made by Apple to help blind Mac OS users. You describe their screens, making sure to explain the focused window, where the cursor is, and any available input boxes. There are a lot of possible details, so you try to focus on items related to the task they need help with.
    """
    
    EXAMPLE_INPUT_TEXT = "Overall, I am trying to find a video about monkeys. Right now, I am trying to search for a video about monkeys."
    
    with open("/Users/arvindh/Downloads/compressed.jpg", "rb") as image_file:
        EXAMPLE_INPUT_IMAGE = base64.b64encode(image_file.read()).decode('utf-8')
    
    EXAMPLE_OUTPUT = """The user's screen is focused on a Safari window. In the Safari window, there are four open tabs. YouTube is the active tab. The user's input is not focused on anything in the YouTube tab. There are many icons, but the relevant one is likely the search bar. The cursor is not visible, but pressing tab once will likely focus the cursor onto the search bar.
    """
    
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user",
             "content": [
                 {
                     "type": "text", "text": EXAMPLE_INPUT_TEXT
                 },
                 {
                     "type": "image_url",
                     "image_url": f"data:image/jpeg;base64,{EXAMPLE_INPUT_IMAGE}"
                 }
             ],
            },
            {"role": "assistant", "content": EXAMPLE_OUTPUT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", "text": "This is now a new user: " + inp_text
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{screen_to_base_64()}"
                    }
                ]
            }
        ],
        max_tokens=250
    )
    
    return response.choices[0].message.content

print(call_vision_api("Overall, I am trying to write a text to my friend Peter. Right now, I am trying to open the messages app."))