import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from PIL import Image
from openai import OpenAI


#skriv api nøgle her
client = OpenAI(api_key="")

# Directory to save images
DOWNLOAD_DIR = "static"

# Create directory if it doesn't exist
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)



def download_image(image_url):
    try:

        #henter sidens indhold ned i et response object
        response = requests.get(image_url)

        #tjekker for error codes - 200 OK
        response.raise_for_status()

        #Splitter billedets filnavn og url(image.jpg)
        image_name = image_url.split('/')[-1]

        #vælger stien for hvor billedet skal gemmes: så C://.../static/image.jpg
        image_path = os.path.join(DOWNLOAD_DIR, image_name)

        #Gemmer vi billedet til den specifikke path - WB:write binary
        with open(image_path, 'wb') as f:
            f.write(response.content)
        return image_path

    except Exception as e:
        print(f"Failed to download image {image_url}: {e}")
        return None

def gpt(image_url):
    try:

        #CHATGPT API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Create a short alt text for the image and only use around 15 words?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            max_tokens=50,
        )

        # Udskriver imageURL og Response - hvilket er objektet
        print(f"Full response for image {image_url}:", response)

        #ChatGPT returnere et response array som vi hopper ned igennem. VI får til sidst fat i content som er selve AI beskrivelsen
        #Response objekt nedenunder
        #ChatCompletion(id='chatcmpl-9c7sYrpxPWxdmobdEXjO2DOaNvf6Y', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='Blue house logo with a red window, text "FORSIKRINGSHUSET DANMARK" underneath.', role='assistant', function_call=None, tool_calls=None))],
        alt_text = response.choices[0].message.content
        return alt_text


    except Exception as e:
        print(f"An error occurred while calling ChatGPT API for image {image_url}: {e}")
        return None

def find_images_without_alt_text(url):
    image_list = []
    try:
        #Henter hele hjemmesiden ned med GET
        response = requests.get(url)
        #print("response objekt: " + response)

        #Tjekker for status kode 200 OK
        response.raise_for_status()

        #Henter alt html content som en string
        html_content = response.text

        #html.parser gør så man kan navigere gennem htmlen
        soup = BeautifulSoup(html_content, 'html.parser')

        #finder alle billeder der indeholder et img tag
        img_tags = soup.find_all('img')

        for img in img_tags:
            if not img.has_attr('alt') or img['alt'] == '':
                src = img.get('src')

                valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
                if any(src.endswith(ext) for ext in valid_extensions):
                    if not src.startswith('http'):
                        src = urljoin(url, src)

                    #SRC = Billedet
                    image_path = download_image(src)
                    if image_path:
                        # Generate alt text using GPT
                        ai_alt_text = gpt(src)  # Call the gpt function with the image URL
                        image_list.append({
                            'src': src,
                            'alt': "no alt text provided",
                            'ai': ai_alt_text
                        })
    except Exception as e:
        print("An error occurred while processing the URL:", e)

    print("Images without alt text:", image_list)
    return image_list

