import requests
import time
import re
import json
import os
import csv
import pandas as pd
import tkinter as tk
from tkinter import ttk
from transformers import pipeline

# Chargement du pipeline NER pour le français
# Le modèle "Jean-Baptiste/roberta-large-ner-french" est un modèle pré-entraîné sur le français
ner_pipeline = pipeline("ner", model="Jean-Baptiste/roberta-large-ner-french", aggregation_strategy="simple")

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

def extract_data_ner(text):
    """
    Utilise un modèle NER pré-entraîné pour extraire des entités du texte.
    Ensuite, on essaie d'associer ces entités à nos champs cibles.
    """
    entities = ner_pipeline(text)
    # Afficher pour debug
    # print("Entités détectées:", json.dumps(entities, indent=4, ensure_ascii=False))
    
    # Initialisation des champs
    data = {
        "Nom_Produit": None,
        "Dosage": None,
        "Principe_Actif": None,
        "Type_Produit": None,
        "Date_Expiration": None,
        "Date_Fabrication": None,
        "Date_Delivrance": None,
        "Numero_Lot": None,
        "Quantite_Boite": None,
        "Prix": None,
        "PPA": None,
        "Tarif_Reference": None,
        "SHP": None
    }
    
    # Exemple d'association d'entités aux champs (cela peut être affiné)
    for ent in entities:
        label = ent['entity_group'].lower()
        value = ent['word']
        # Ici, on utilise des règles basiques basées sur le label et le contexte (le modèle NER peut ne pas fournir directement nos labels souhaités)
        if not data["Nom_Produit"] and label == "misc":
            data["Nom_Produit"] = value.capitalize()
        if not data["Dosage"] and re.search(r"\d+\s*(mg|µg|g|ml)", value, re.IGNORECASE):
            data["Dosage"] = value
        if not data["Date_Expiration"] and re.search(r"\d{2}/\d{2,4}", value):
            # On suppose ici qu'il s'agit d'une date d'expiration si le contexte contient "exp" (à ajuster selon besoin)
            if "exp" in text.lower():
                data["Date_Expiration"] = value
        # Pour les autres champs, vous pouvez ajouter d'autres règles selon vos observations.
    
    # Pour compléter, on applique des regex sur le texte brut en complément du NER
    match_product = re.search(r"([A-Za-zÉÈÊÀÂÔÎÛÙÇ]+)\s*(\d+\s*(mg|µg|g|ml))", text, re.IGNORECASE)
    if match_product:
        data["Nom_Produit"] = match_product.group(1).capitalize()
        data["Dosage"] = match_product.group(2)
    
    match_type = re.search(r"(Flacon|Gélules|Sachet|Poudre pour .+ en sachet)", text, re.IGNORECASE)
    if match_type:
        data["Type_Produit"] = match_type.group(1)
    
    match_lot = re.search(r"(lot|n° de lot)\s*[: ]*(\w+)", text, re.IGNORECASE)
    if match_lot:
        data["Numero_Lot"] = match_lot.group(2)
    
    match_qty = re.search(r"(bo[iî]te|flacon|gélule|sachet)s?\s*de\s*(\d+)", text, re.IGNORECASE)
    if match_qty:
        data["Quantite_Boite"] = int(match_qty.group(2))
    
    match_prix = re.search(r"prix\s*[: ]*([\d,]+)", text, re.IGNORECASE)
    if match_prix:
        data["Prix"] = float(match_prix.group(1).replace(",", "."))
    
    match_ppa = re.search(r"(ppa|prix public)\s*[: ]*([\d,]+)\s*da", text, re.IGNORECASE)
    if match_ppa:
        data["PPA"] = float(match_ppa.group(2).replace(",", "."))
    
    match_tarif = re.search(r"tarif de réf\s*[: ]*([\d,]+)\s*da", text, re.IGNORECASE)
    if match_tarif:
        data["Tarif_Reference"] = float(match_tarif.group(1).replace(",", "."))
    
    match_shp = re.search(r"shp\s*[: ]*(\d+)", text, re.IGNORECASE)
    if match_shp:
        data["SHP"] = int(match_shp.group(1))
    
    return data

def process_image(image_path):
    ocr_result = extract_text_from_image(image_path)
    if not ocr_result:
        return None
    extracted_text = "\n".join([line["text"] for line in ocr_result["analyzeResult"]["readResults"][0]["lines"]])
    # Optionnel : afficher le texte brut pour debug
    # print("Texte OCR brut:\n", extracted_text)
    extracted_data = extract_data_ner(extracted_text)
    return extracted_data

def append_to_csv(data, csv_file, fieldnames):
    try:
        with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow(data)
    except Exception as e:
        print("Erreur lors de l'écriture du fichier CSV :", e)

def display_csv_table(csv_file):
    if not os.path.exists(csv_file):
        print("Le fichier CSV n'existe pas encore.")
        return
    try:
        df = pd.read_csv(csv_file)
        window = tk.Toplevel()
        window.title("Contenu du fichier CSV")
        frame = ttk.Frame(window, padding="3 3 12 12")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        tree = ttk.Treeview(frame, columns=list(df.columns), show="headings")
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        for _, row in df.iterrows():
            tree.insert("", tk.END, values=list(row))
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        window.mainloop()
    except Exception as e:
        print("Erreur lors de la lecture du fichier CSV :", e)

def main():
    csv_file = "result.csv"
    fieldnames = [
        "Nom_Produit", "Dosage", "Principe_Actif", "Type_Produit",
        "Date_Expiration", "Date_Fabrication", "Date_Delivrance",
        "Numero_Lot", "Quantite_Boite", "Prix", "PPA", "Tarif_Reference", "SHP"
    ]
    if not os.path.exists(csv_file):
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
    
    root = tk.Tk()
    root.title("Application OCR - Menu")
    
    def traiter_image():
        image_path = input_entry.get().strip()
        if not os.path.exists(image_path):
            result_label.config(text="Fichier non trouvé. Veuillez réessayer.")
            return
        result_data = process_image(image_path)
        if result_data:
            result_label.config(text=json.dumps(result_data, indent=4, ensure_ascii=False))
            append_to_csv(result_data, csv_file, fieldnames)
            result_label.config(text=result_label.cget("text") + f"\nLes données ont été ajoutées au fichier {csv_file}")
        else:
            result_label.config(text="Aucune donnée n'a été extraite pour cette image.")
    
    def afficher_csv():
        display_csv_table(csv_file)
    
    def quitter_app():
        root.destroy()
    
    input_label = tk.Label(root, text="Entrez le chemin de l'image :")
    input_label.pack(pady=5)
    input_entry = tk.Entry(root, width=50)
    input_entry.pack(pady=5)
    process_button = tk.Button(root, text="Traiter l'image", command=traiter_image)
    process_button.pack(pady=5)
    display_button = tk.Button(root, text="Afficher le fichier CSV", command=afficher_csv)
    display_button.pack(pady=5)
    quit_button = tk.Button(root, text="Quitter", command=quitter_app)
    quit_button.pack(pady=5)
    result_label = tk.Label(root, text="", justify="left")
    result_label.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
