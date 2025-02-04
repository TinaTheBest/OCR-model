import requests
import time
import re
import json
import csv

# Azure OCR Endpoint & API Key
AZURE_ENDPOINT = "https://npl-ocr.cognitiveservices.azure.com/"
AZURE_API_KEY = "9NV7bUaKBwO4I8yAolJYADwhEgNZhH7CVpRYDwtOv3BzbsJcqddDJQQJ99BBAC5RqLJXJ3w3AAAFACOGsQ8R"
OCR_URL = f"{AZURE_ENDPOINT}vision/v3.1/read/analyze?language=fr"

def extract_text_from_image(image_path):
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
        "Content-Type": "application/octet-stream"
    }
    
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    response = requests.post(OCR_URL, headers=headers, data=image_data)
    if response.status_code != 202:
        print("API Error:", response.json())
        return None
    
    operation_url = response.headers["Operation-Location"]
    time.sleep(2)
    
    while True:
        response = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": AZURE_API_KEY})
        result = response.json()
        
        if result["status"] == "succeeded":
            return result
        elif result["status"] == "failed":
            print("OCR processing failed.")
            return None
        
        time.sleep(2)

def extract_data(text):
    data = {}
    
    match_product = re.search(r"([A-ZÉÈÊÀÂÔÎÛÙÇ]+)\s+(\d+)\s*mg", text, re.IGNORECASE)
    if match_product:
        data["Nom_Produit"] = match_product.group(1).capitalize()
        data["Dosage"] = match_product.group(2) + " mg"
    
    match_principle = re.search(r"([A-Za-zéèêàâôîûùç]+)\s+\d+\s*mg", text, re.IGNORECASE)
    if match_principle:
        data["Principe_Actif"] = match_principle.group(1).capitalize()
    
    match_type = re.search(r"(Poudre pour .+ en sachet)", text, re.IGNORECASE)
    if match_type:
        data["Type_Produit"] = match_type.group(1)
    
    match_per = re.search(r"(per|péremption|expiration|exp)\s*:\s*(\d{2}\s*/\s*\d{4})", text, re.IGNORECASE)
    if match_per:
        data["Date_Expiration"] = match_per.group(2).replace(" ", "")
    
    match_fab = re.search(r"(fab|fabrication|fabriqué)\s*:\s*(\d{2}\s*/\s*\d{4})", text, re.IGNORECASE)
    if match_fab:
        data["Date_Fabrication"] = match_fab.group(2).replace(" ", "")
    
    match_de = re.search(r"(de|délivrance)\s*:\s*([\d/]+)", text, re.IGNORECASE)
    if match_de:
        data["Date_Delivrance"] = match_de.group(2)
    
    match_lot = re.search(r"(lot|n° de lot)\s*:\s*(\d+)", text, re.IGNORECASE)
    if match_lot:
        data["Numero_Lot"] = match_lot.group(2)
    
    match_qty = re.search(r"bo[iî]te de (\d+) sachets", text, re.IGNORECASE)
    if match_qty:
        data["Quantite_Boite"] = int(match_qty.group(1))
    
    match_prix = re.search(r"prix\s*:\s*([\d.]+)", text, re.IGNORECASE)
    if match_prix:
        data["Prix"] = float(match_prix.group(1))
    
    match_ppa = re.search(r"(ppa|prix public)\s*:\s*([\d.]+)\s*DA", text, re.IGNORECASE)
    if match_ppa:
        data["PPA"] = float(match_ppa.group(2))
    
    match_tarif = re.search(r"tarif de réf\s*:\s*([\d.]+)\s*DA", text, re.IGNORECASE)
    if match_tarif:
        data["Tarif_Reference"] = float(match_tarif.group(1))
    
    # Extraction de la donnée SHP (attendu sous la forme "shp : <nombre>")
    match_shp = re.search(r"shp\s*:\s*(\d+)", text, re.IGNORECASE)
    if match_shp:
        data["SHP"] = int(match_shp.group(1))
    else:
        data["SHP"] = None  # ou une valeur par défaut si SHP n'est pas trouvé
    
    return data

def process_image(image_path):
    ocr_result = extract_text_from_image(image_path)
    if not ocr_result:
        return None
    
    # Concaténer les lignes de texte extraites
    extracted_text = "\n".join([
        line["text"] for line in ocr_result["analyzeResult"]["readResults"][0]["lines"]
    ])
    
    extracted_data = extract_data(extracted_text)
    return extracted_data

# Chemin de l'image à traiter
image_path = "dataset/vignette.jpg"  # Remplacez par le chemin de votre image

# Traitement de l'image
result_data = process_image(image_path)
if result_data:
    print("Données extraites :")
    print(json.dumps(result_data, indent=4, ensure_ascii=False))
    
    # Définir les noms de colonnes souhaitées dans le CSV
    fieldnames = [
        "Nom_Produit", "Dosage", "Principe_Actif", "Type_Produit",
        "Date_Expiration", "Date_Fabrication", "Date_Delivrance",
        "Numero_Lot", "Quantite_Boite", "Prix", "PPA", "Tarif_Reference", "SHP"
    ]
    
    # Écriture dans le fichier CSV
    csv_file = "result.csv"
    try:
        with open(csv_file, mode="w", newline='', encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(result_data)
        print(f"Les données ont été enregistrées dans le fichier {csv_file}")
    except Exception as e:
        print("Erreur lors de l'écriture du fichier CSV :", e)
else:
    print("Aucune donnée n'a été extraite.")
