import requests
import json
from dotenv import load_dotenv
import os
from openai import OpenAI
from llm_utils import call_vision_api, get_and_validate_steps, get_and_validate_automated_steps, execute
import logging

load_dotenv()
logging.basicConfig()
client = OpenAI()

task = input()

step_response = get_and_validate_steps(client, task)

steps = step_response['steps']

for step in steps:
    executable_steps = {}
    executable_steps["pre_status"] = 0
    
    while executable_steps["pre_status"] == 0:
        vision_response = call_vision_api(client, task, step)
    
        executable_steps = get_and_validate_automated_steps(client, vision_response, task, step)
        for step in executable_steps["steps"]:
            execute(step)
    