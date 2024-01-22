import base64
from io import BytesIO
import pyautogui
import requests
import os
import json
from jsonschema import validate
from retry import retry
from automation_utils import hotKeys, write, press

def send_pushover(text, print_args=False, lst=None, dct=None):
    PUSHOVER_API_KEY = os.getenv("PUSHOVER_API_KEY")
    PUSHOVER_USER = os.getenv("PUSHOVER_USER")
    if print_args:
        message = {
            "text": text,
            "list": lst,
            "dict": dct
        }
    else:
        message = text
    requests.post(
        'https://api.pushover.net/1/messages.json',
        json={
            'token': PUSHOVER_API_KEY,
            'user': PUSHOVER_USER,
            'message': json.dumps(message)
        }
    )

def log(text):
    # decorator that calls send_pushover(text) and then calls the function
    def decorator(function):
        def wrapper(*args, **kwargs):
            print(text)
            send_pushover(text, lst=args, dct=kwargs)
            ret = function(*args, **kwargs)
            send_pushover("Return: " + json.dumps(ret))
            return ret
        return wrapper
    return decorator

def screen_to_base_64():
    # takes a screenshot
    # and converts to base64
    # and returns that base64
    
    im = pyautogui.screenshot().convert("RGB")
    buffered = BytesIO()
    im.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

@log("Getting steps")
def get_steps(client, task):
    HIGH_LEVEL_PROMPT = """
    You are an intelligent caregiver assistant, skilled in giving specific explanations of how to use computers to elderly people. Their vision is poor, so try to avoid mouse movements in favor of keyboard inputs and commands. Avoid using terms like "click on" in favor of "focus" or "select".

    You output a JSON with a "steps" attribute holding a list of strings, with each string corresponding to a step.
    My grandma needs help to send a happy birthday text to Peter Liu on her Macbook Air. Can you offer specific steps for doing so?
    {
        "steps": [
            "Open Spotlight",
            "Use Spotlight to open the Messages app", 
            "Create a new message",
            "Focus on the sender field",
            "Type 'Peter Liu'",
            "Focus on the body of the message",
            "Type 'Happy Birthday'", 
            "Send the message"
        ]
    }
    """
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": HIGH_LEVEL_PROMPT},
            {"role": "user", "content": f"My grandmother needs help to {task} on her Macbook Air. Can you offer specific steps for doing so?"}
        ],
        response_format={
            "type": "json_object"
        }
    )
    
    return json.loads(completion.choices[0].message.content)


def validate_steps(steps):
    step_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": [
            "steps"
        ]
    }
    
    validate(instance=steps, schema=step_schema)
    
@retry(
    tries=5,
    delay=2,
)

def validate_automated_steps(steps):
    functions = [
        {
            "name": "write",
            "arguments": {
                "text": {
                    "type": "string"
                }
            }
        },
        {
            "name": "press",
            "arguments": {
                "key": {
                    "enum": pyautogui.KEYBOARD_KEYS
                }
            }
        },
        {
            "name": "hotKeys",
            "arguments": {
                "keys": {
                    "type": "array",
                    "items": {
                        "enum": pyautogui.KEYBOARD_KEYS
                    }
                }
            }
        },
        {
            "name": "promptUser",
            "arguments": {
                "text": {
                    "type": "string"
                }
            }
        }
    ]
    
    function_objs = []
    for function in functions:
        a = {}
        a["type"] = "object"
        a["properties"] = {
            "function": {
                "type": "string",
                "enum": [
                    function["name"]
                ]
            },
            "arguments": {
                "type": "object",
                "properties": function["arguments"],
                "required": list(function["arguments"].keys())
            }
                
        }
        a["required"] = ["function", "arguments"]
        function_objs.append(a)
        
    automated_step_schema = {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {
                    "oneOf": function_objs
                }
            },
            "pre_status": {
                "type": "number",
                "enum": [0, 1]
            },
        },
        "required": ["steps", "pre_status"]
    }
        
    return validate(instance=steps, schema=automated_step_schema)


def get_and_validate_steps(client, task):
    steps = get_steps(client, task)
    validate_steps(steps)
    return steps  

@retry(
    tries=5,
    delay=2
)
def get_and_validate_automated_steps(client, vision_output, overall_task, curr_step):
    steps = parse_vision_response(client, vision_output, overall_task, curr_step)
    validate_automated_steps(steps)
    return steps

@log("Parsing vision response")
def parse_vision_response(client, vision_output, overall_task, curr_step):
    low_level_prompt = """
        You are an intelligent bot made by Apple, skilled at taking a specific action and decomposing it into function calls to help blind customers. You make reasonable assumptions about the input. Make sure to remember that users need to click enter after inputting text. Also remember users can jump around using tab.
        The available functions are:

        hotKeys(keys: list[str]) -- Simultaneously presses multiple keys
        write(text: str) -- Writes plain text. For example, for filling input boxes. Not displayed to user.
        press(key: str) -- Presses a key. For example, for hitting 'enter'.
        promptUser(text: str) -- Prompts the user for input. For example, if the user's password is needed. This should be very rarely used.

        You output a JSON that is used by their screenreader to tell them to perform the action. The schema has two attributes: "steps" and "pre_status". "steps" is a series of function calls. "pre_status" is 0 or 1, with 0 representing that the task was already done and 1 representing that the task was not yet done by the time the conversation started (i.e., no steps are required).

        Keys are defined by pyautogui.KEYBOARD_KEYS. This is 'backspace', 'capslock', 'space', 'enter', 'tab', 'f1', 'f2', 'f3', etc.
    """
    
    example_vision_output = """
        The user's screen is showing Visual Studio Code with two open files, `overall.py` and `utils.py`, within a project containing various Python files and a virtual environment. The `overall.py` tab is active, and the file contains Python code, seemingly to work with an API. 

        The integrated terminal at the bottom displays a command line that has just run `python3 overall.py`, indicating an execution of the Python script that might be interfaced with an API, as noted with the output "Calling vision API."

        To open Messages without using a mouse, you can press `Command` + `Space` to open Spotlight Search. Then, start typing "Messages" until the Messages app is highlighted in the search results, and press `Enter` to launch the application.
    """
    
    example_input = "Overall, I am trying to send a message to Peter. Currently, I am trying to open the messages app."
    
    example_output = """{
        "steps": [
            {
                "function": "hotKeys",
                "arguments": {
                    "keys": ["command", "space"]
                }
            },
            {
                "function": "write",
                "arguments": {
                    "text": "Messages"
                }
            },
            {
                "function": "press",
                "arguments": {
                    "key": "enter"
                }
            }
        ],
        "pre_status": 0
    }"""
    
    example_user_content = f"""
    Apple's Dictation: {example_vision_output}
    Input: {example_input}
    """
    
    actual_user_content = f"""
    Apple's Dictation: {vision_output}
    Input: Overall, I am trying to {overall_task} on my Macbook Air. Currently, I am trying to {curr_step}
    """
    
    messages = [
        {
            "role": "system",
            "content": low_level_prompt
        },
        {
            "role": "user",
            "content": example_user_content
        },
        {
            "role": "assistant",
            "content": example_output
        },
        {
            "role": "user",
            "content": actual_user_content
        }
    ]
    
    ret = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        response_format={
            "type": "json_object"
        }
    )
    
    return json.loads(ret.choices[0].message.content)
    
def execute(step):
    if step["function"] == "hotKeys":
        hotKeys(step["arguments"]["keys"])
    elif step["function"] == "write":
        write(step["arguments"]["text"])
    elif step["function"] == "press":
        press(step["arguments"]["key"])
    elif step["function"] == "promptUser":
        print(step["arguments"]["text"])


@log("Calling vision API")
def call_vision_api(client, overall_task, curr_step):
    PROMPT = """
    You are an intelligent bot made by Apple to help blind Mac OS users. You describe their screens, making sure to explain the focused window, where the cursor is, and any available input boxes. There are a lot of possible details, so you try to focus on items related to the task they need help with. Try to only provide one, simple, mouse-less way of achieving the task.
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
                        "type": "text",
                        "text": "This is now a new user: " + f'Overall, I am trying to {overall_task}. Right now, I am trying to {curr_step}'
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