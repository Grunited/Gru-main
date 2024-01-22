import openai
import pyautogui
from llm_utils import screen_to_base_64
import subprocess

DEFAULT_SUCCESS = {
    "success": True
}

def click_on(x, y):
    try:
        pyautogui.click(x, y)
        return DEFAULT_SUCCESS
    except Exception as e:
        return {
            "error": str(e)
        }

def get_description_of_screen(client):
    PROMPT = "You are an intelligent caregiver assistant created by Apple. Your task is to describe the screen in a way that is easy for the user to understand. You only respond with the description. Do not include any explanations."
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system", "content": PROMPT
            },
            {
                "role": "user", 
                "content": [
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{screen_to_base_64()}"
                    },
                    {
                        "type": "text",
                        "text": "Describe this screen"
                    }
                ]
            }
        ],
        max_tokens=250
    )
    
    if response.choices[0].finish_reason not in ('stop', 'length'):
        return "Failed to generate description"
    return response.choices[0].message.content
    
def mdfind(query):
    try:
        return subprocess.check_output(["mdfind", query]).decode('utf-8')
    except Exception as e:
        return {
            "error": str(e)
        }
def open(filepath, reveal, background):
    args = ["open"]
    if reveal:
        args.append('-R')
    if background:
        args.append('-g')
    
    args.append(filepath)
    
    print(args)
    try:
        return subprocess.check_output(args).decode('utf-8')
    except Exception as e:
        return {
            "error": str(e)
        }

def write(text):
    pyautogui.write(text)
    return DEFAULT_SUCCESS

def press(key):
    pyautogui.press(key)
    return DEFAULT_SUCCESS

def hot_keys(keys):
    pyautogui.hotkey(*keys, interval=0.1)
    return DEFAULT_SUCCESS