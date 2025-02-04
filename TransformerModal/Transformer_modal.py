import os
import cv2
import easyocr
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Step 1: Preprocess the Image for Better OCR Accuracy
def preprocess_image(input_path, output_path):
    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read the image
    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Unable to read the image at: {input_path}")

    # Convert to grayscale and apply adaptive threshold
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    enhanced_image = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    cv2.imwrite(output_path, enhanced_image)

# Paths for the input and preprocessed image
image_path = "c:/Users/DELL/OneDrive/Desktop/Prescription_modal/dataset/image1.png"  # Update with the actual file name
enhanced_image_path = "c:/Users/DELL/OneDrive/Desktop/Prescription_modal/enhanced_image.png"

# Preprocess the image
try:
    preprocess_image(image_path, enhanced_image_path)
except Exception as e:
    print(f"Error during preprocessing: {e}")
    exit()

# Step 2: Initialize EasyOCR Reader
reader = easyocr.Reader(['en'])

# Step 3: Extract Text from the Preprocessed Image
results = reader.readtext(enhanced_image_path)
print("Raw OCR Results:")
for result in results:
    print(f"Text: {result[1]}, Confidence: {result[2]:.2f}")

# Combine Extracted Text
extracted_text = " ".join([result[1] for result in results])
print(f"\nCombined Extracted Text:\n{extracted_text}")

# Step 4: Load a Pretrained Model for Medical NER
model_name = "HUMADEX/english_medical_ner"  # Replace with a suitable model if needed
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)

# Create a pipeline for Named Entity Recognition
nlp_ner = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

# Step 5: Debug NER with Predefined Text
test_text = "Dr. John prescribed Amoxicillin 500mg for 7 days."
print("\nTesting NER with Predefined Text:")
ner_test_results = nlp_ner(test_text)
for entity in ner_test_results:
    print(f"Entity: {entity['word']}, Label: {entity['entity_group']}, Score: {entity['score']:.4f}")

# Step 6: Run NER on Extracted Text
print("\nRunning NER on Extracted Text:")
ner_results = []
if extracted_text.strip():
    ner_results = nlp_ner(extracted_text)
    for entity in ner_results:
        print(f"Entity: {entity['word']}, Label: {entity['entity_group']}, Score: {entity['score']:.4f}")
else:
    print("No text extracted from the image.")

# Step 7: Save Results to File
output_text = f"Raw Extracted Text:\n{extracted_text}\n\nNamed Entity Recognition Results:\n"
if ner_results:
    for entity in ner_results:
        output_text += f"Entity: {entity['word']}, Label: {entity['entity_group']}, Score: {entity['score']:.4f}\n"
else:
    output_text += "No entities were recognized.\n"

with open("extracted_and_ner_results.txt", "w") as file:
    file.write(output_text)

print("\nResults saved to 'extracted_and_ner_results.txt'")
