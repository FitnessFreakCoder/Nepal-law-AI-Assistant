import base64
from openai import OpenAI
from Apikey import MyAPiKEY
import os
import re
import json

client = OpenAI(api_key=MyAPiKEY)

print("Generating text from provided image...")

# Read and encode image

def natural_sort_key(filename):
    """Extract numbers from filename for proper sorting"""
    numbers = re.findall(r'\d+', filename)
    return int(numbers[0]) if numbers else 0

# Get all image files and sort them naturally
images = sorted(
    [f for f in os.listdir('Constitution-of-Nepal') if f.endswith('.jpg')],
    key=natural_sort_key
)
for image in images:
    print(image)
    Text_title = image.split('.')[0]
    with open(f"Constitution-of-Nepal/{image}", "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")
        print(f'Extracting for {image}....')
        # API call
        response = client.responses.create(
    model="gpt-4.1-mini",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "Extract all text from provided Nepali langiage images to English language.Note:Only provide answers"},
            {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{image_b64}",
                "detail" : "auto"
            },
        ],
    }],
)
        

        output_text = {"Text": response.output_text}
        os.makedirs('Json_text' , exist_ok=True)
        with open(f'Json_text/{Text_title}.json', 'w', encoding="utf-8") as f:
            json.dump(output_text,f)


# Save output
print(f"Extracted Text saved to folder:Json_text")
    
    











