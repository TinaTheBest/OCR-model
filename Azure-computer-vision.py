import requests
import time

# Azure OCR Endpoint & API Key
AZURE_ENDPOINT = "https://npl-ocr.cognitiveservices.azure.com/"
AZURE_API_KEY = "your-azure-api-key"

# Use the Read API with the French language parameter
OCR_URL = f"{AZURE_ENDPOINT}vision/v3.1/read/analyze?language=fr"

def extract_text_from_image(image_path):
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
        "Content-Type": "application/octet-stream"
    }

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # Send the image for OCR processing
    response = requests.post(OCR_URL, headers=headers, data=image_data)

    if response.status_code != 202:
        print("API Error:", response.json())
        return None

    # Get operation URL from headers
    operation_url = response.headers["Operation-Location"]

    # Wait for OCR processing
    time.sleep(2)

    while True:
        response = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": AZURE_API_KEY})
        result = response.json()

        if result["status"] == "succeeded":
            return result
        elif result["status"] == "failed":
            print("OCR processing failed.")
            return None

        time.sleep(2)  # Check again after 2 seconds

def display_raw_text(ocr_result):
    if "analyzeResult" not in ocr_result:
        print("No text detected.")
        return
    
    print("\n--- Texte Extrait ---\n")
    for line in ocr_result["analyzeResult"]["readResults"][0]["lines"]:
        print(line["text"])

# Test avec une image
image_path = "dataset/vignette.jpg"  # Remplacez par le chemin de votre image
ocr_result = extract_text_from_image(image_path)

if ocr_result:
    display_raw_text(ocr_result)
