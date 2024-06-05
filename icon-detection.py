import hashlib
import io
import os
import subprocess
from typing import List

import cv2
import nltk
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from sentence_transformers import SentenceTransformer, util

try:
    nltk.corpus.words.words()
except LookupError:
    nltk.download("words", quiet=True)
from nltk.corpus import words

# Create a set of English words
english_words = set(words.words())

def take_screenshot_to_pil(filename="temp_screenshot.png"):
    # Capture the screenshot and save it to a temporary file
    subprocess.run(["screencapture", "-x", filename], check=True)

    # Open the image file with PIL
    with open(filename, "rb") as f:
        image_data = f.read()
    image = Image.open(io.BytesIO(image_data))

    # Optionally, delete the temporary file if you don't need it after loading
    os.remove(filename)

    return image

def resize_image(image, target_size=(1280, 720)):
    return image.resize(target_size, Image.LANCZOS)

def get_element_boxes(image_data, debug=False):
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    debug_path = os.path.join(desktop_path, "oi-debug")

    if debug:
        if not os.path.exists(debug_path):
            os.makedirs(debug_path)

    pil_image = image_data.convert("L")

    def process_image(
        pil_image,
        contrast_level=1.0,
        debug=False,
        debug_path=None,
        adaptive_method=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        threshold_type=cv2.THRESH_BINARY,
        block_size=9,
        C=3,
    ):
        enhancer = ImageEnhance.Contrast(pil_image)
        contrasted_image = enhancer.enhance(contrast_level)

        if debug:
            contrasted_image_path = os.path.join(debug_path, "contrasted_image.jpg")
            contrasted_image.save(contrasted_image_path)

        contrasted_image_cv = cv2.cvtColor(np.array(contrasted_image), cv2.COLOR_RGB2BGR)
        gray_contrasted = cv2.cvtColor(contrasted_image_cv, cv2.COLOR_BGR2GRAY)

        if debug:
            image_path = os.path.join(debug_path, "gray_contrasted_image.jpg")
            cv2.imwrite(image_path, gray_contrasted)

        binary_contrasted = cv2.adaptiveThreshold(
            src=gray_contrasted,
            maxValue=255,
            adaptiveMethod=adaptive_method,
            thresholdType=threshold_type,
            blockSize=block_size,
            C=C,
        )

        if debug:
            binary_contrasted_image_path = os.path.join(debug_path, "binary_contrasted_image.jpg")
            cv2.imwrite(binary_contrasted_image_path, binary_contrasted)

        # Apply morphological operations to help detect smaller elements
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        binary_contrasted = cv2.morphologyEx(binary_contrasted, cv2.MORPH_CLOSE, kernel)

        contours_contrasted, _ = cv2.findContours(binary_contrasted, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        contour_image = np.zeros_like(binary_contrasted)
        cv2.drawContours(contour_image, contours_contrasted, -1, (255, 255, 255), 1)

        if debug:
            contoured_contrasted_image_path = os.path.join(debug_path, "contoured_contrasted_image.jpg")
            cv2.imwrite(contoured_contrasted_image_path, contour_image)

        return contours_contrasted

    contours_contrasted = process_image(pil_image, debug=debug, debug_path=debug_path)

    boxes = []
    for contour in contours_contrasted:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 16 and h > 9:  # Allow smaller boxes to be included
            boxes.append({"x": x, "y": y, "width": w, "height": h})

    if debug:
        print(f"Total boxes detected: {len(boxes)}")

    return boxes

def combine_boxes(icons_bounding_boxes, max_area=160000):
    while True:
        combined_boxes = []
        used_boxes = set()
        any_combined = False
        for i, box in enumerate(icons_bounding_boxes):
            if i in used_boxes:
                continue
            combined_box = box.copy()
            for j, other_box in enumerate(icons_bounding_boxes):
                if j in used_boxes or i == j:
                    continue
                if (
                    combined_box["x"] < other_box["x"] + other_box["width"] - 1
                    and combined_box["x"] + combined_box["width"] > other_box["x"] + 1
                    and combined_box["y"] < other_box["y"] + other_box["height"] - 1
                    and combined_box["y"] + combined_box["height"] > other_box["y"] + 1
                ):
                    combined_x = min(combined_box["x"], other_box["x"])
                    combined_y = min(combined_box["y"], other_box["y"])
                    combined_width = max(combined_box["x"] + combined_box["width"], other_box["x"] + other_box["width"]) - combined_x
                    combined_height = max(combined_box["y"] + combined_box["height"], other_box["y"] + other_box["height"]) - combined_y
                    combined_area = combined_width * combined_height
                    if combined_area <= max_area:
                        combined_box = {
                            "x": combined_x,
                            "y": combined_y,
                            "width": combined_width,
                            "height": combined_height
                        }
                        used_boxes.add(j)
                        any_combined = True
            combined_boxes.append(combined_box)
            used_boxes.add(i)

        if not any_combined:
            combined_boxes.extend([icons_bounding_boxes[i] for i in range(len(icons_bounding_boxes)) if i not in used_boxes])
            break
        icons_bounding_boxes = combined_boxes

    return combined_boxes

def draw_boxes(image_data, boxes, color='red', outline='blue', shuffle_colors=True):
    colors = ['red', 'green', 'blue', 'purple', 'darkgreen', 'mediumorchid', 'mediumblue', 'crimson', 'pink', 'cyan']
    # now we want to shuffle the colors
    np.random.shuffle(colors)
    draw = ImageDraw.Draw(image_data)
    for ind, box in enumerate(boxes):
        if shuffle_colors:
            color = colors[ind % len(colors)]
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]
        draw.rectangle([(x, y), (x + w, y + h)], outline=color)
        
        # add a label for the rectangle using the index
        draw.rectangle([(x, y-13), (x + 15, y)], fill=color)
        draw.text((x + 2, y-10), str(ind), fill='white')
    return image_data


def main(image_path, description="cat", debug=True):
    image_data = Image.open(image_path)
    image_data = resize_image(image_data, target_size=(1280, 720))
    icons_bounding_boxes = get_element_boxes(image_data, debug)
    
    if debug:
        combined_boxes = combine_boxes(icons_bounding_boxes, max_area=80000)
        image_with_boxes = draw_boxes(image_data.copy(), combined_boxes, color='blue')
        image_with_boxes.show()
        image_with_boxes.save("combined_boxes.png")

    icons = []
    for box in combined_boxes:
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]
        icon_image = image_data.crop((x, y, x + w, y + h))
        icon = {
            "data": icon_image,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "hash": hashlib.sha256(icon_image.tobytes()).hexdigest(),
        }
        icons.append(icon)
    
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    model = SentenceTransformer("clip-ViT-B-32").to(device)

    def image_search(query, icons, hashes, debug):
        hashed_icons = [icon for icon in icons if icon["hash"] in hashes]
        unhashed_icons = [icon for icon in icons if icon["hash"] not in hashes]

        query_and_unhashed_icons_embeds = model.encode(
            [query] + [icon["data"] for icon in unhashed_icons],
            batch_size=128,
            convert_to_tensor=True,
            show_progress_bar=debug,
        )

        query_embed = query_and_unhashed_icons_embeds[0]
        unhashed_icons_embeds = query_and_unhashed_icons_embeds[1:]

        for icon, emb in zip(unhashed_icons, unhashed_icons_embeds):
            hashes[icon["hash"]] = emb

        unhashed_icons_embeds = unhashed_icons_embeds.to(device)

        img_emb = torch.cat(
            [unhashed_icons_embeds]
            + [hashes[icon["hash"]].unsqueeze(0) for icon in hashed_icons]
        )

        hits = util.semantic_search(query_embed, img_emb)[0]

        results = [hit for hit in hits if hit["score"] > 90]

        if hits and (hits[0] not in results):
            results.insert(0, hits[0])

        return [icons[hit["corpus_id"]] for hit in results]

    hashes = {}
    top_icons = image_search(description, icons, hashes, debug)

    if debug:
        draw = ImageDraw.Draw(image_data)
        for icon in top_icons:
            x, y, w, h = icon["x"], icon["y"], icon["width"], icon["height"]
            draw.rectangle([(x, y), (x + w, y + h)], outline="green")
        image_data.show()
        image_data.save("final_image.png")

if __name__ == "__main__":
    image_path = "/Users/peter_liu/Desktop/Screenshot 2024-06-03 at 1.30.05 AM.png"  # Replace with your image path
    main(image_path)
