import pyautogui
import time
from typing import List, Type

def pause(func):
    def wrapper(*args, **kwargs):
        time.sleep(1)
        return func(*args, **kwargs)
    return wrapper
    
@pause
def write(text: str) -> None:
    pyautogui.write(text)
    
@pause
def press(key: str) -> None:
    pyautogui.press(key)

@pause
def hotKeys(keys: List[str]) -> None:
    for key in keys:
        pyautogui.keyDown(key)
        time.sleep(0.05)
    time.sleep(0.1)
    for key in keys[::-1]:
        pyautogui.keyUp(key)

if __name__ == "__main__":
    time.sleep(3)
    write("Hello, World!")
    press("enter")
    hotKeys(["a", "b", "c"])