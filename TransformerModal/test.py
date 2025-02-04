import easyocr
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Step 1: Initialize EasyOCR Reader
reader = easyocr.Reader(['en'])  # 'en' specifies we want to extract English text

# Step 2: Provide Path to the Image
image_path = "dataset\image.png"  # Update with the correct image path

# Step 3: Extract Text from the Image Using EasyOCR
results = reader.readtext(image_path)

# Step 4: Combine Extracted Text into a Single String
extracted_text = " ".join([result[1] for result in results])

# Step 5: Load a pretrained model for medical NER
model_name = "HUMADEX/english_medical_ner"  
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)

# Step 6: Create a pipeline for Named Entity Recognition
nlp_ner = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

# Step 7: Get NER results for the extracted text from the image
ner_results = nlp_ner(extracted_text)

# Step 8: Prepare results for saving to file
output_text = f"Extracted Text from Image:\n{extracted_text}\n\n"
output_text += "Named Entity Recognition Results:\n"

if ner_results:
    for entity in ner_results:
        output_text += f"Entity: {entity['word']}, Label: {entity['entity_group']}, Score: {entity['score']:.4f}\n"
else:
    output_text += "No entities were recognized.\n"

# Step 9: Save the results into a file
with open("extracted_and_ner_results.txt", "w") as file:
    file.write(output_text)

print("Results have been saved to 'extracted_and_ner_results.txt'")


