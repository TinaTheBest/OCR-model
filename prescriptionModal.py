import requests
import time
import re
import json
import csv
import os
import pandas as pd
import tkinter as tk
from tkinter import ttk

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
    
    # Extraction du nom du produit + dosage
    match_product = re.search(r"([A-Za-zÉÈÊÀÂÔÎÛÙÇ]+(?:\s+[A-Za-zÉÈÊÀÂÔÎÛÙÇ]+)*)\s*(\d+\s*(mg|µg|g|ml)?)", text, re.IGNORECASE)
    if match_product:
        data["Nom_Produit"] = match_product.group(1).capitalize()
        data["Dosage"] = match_product.group(2)
    
    # Extraction du principe actif
    match_principle = re.search(r"DCI[: ]*(\w+)", text, re.IGNORECASE)
    if match_principle:
        data["Principe_Actif"] = match_principle.group(1).capitalize()
    
    # Extraction du type de produit
    match_type = re.search(r"(Flacon|Gélules|Sachet|Poudre pour .+ en sachet)", text, re.IGNORECASE)
    if match_type:
        data["Type_Produit"] = match_type.group(1)
    
    match_de = re.search(r"(DE|Code|Référence)\s*[: ]*(\d{2}/\d{2}(?:\s*A\s*\d+/[A-Za-z0-9]+)?)", text, re.IGNORECASE)
    if match_de:
        data["DE"] = match_de.group(2)

    # Extraction des dates
    match_per = re.search(r"(per|péremption|expiration|exp)\s*[: ]*(\d{2}\s*/\s*\d{4})", text, re.IGNORECASE)
    if match_per:
        data["Date_Expiration"] = match_per.group(2).replace(" ", "")
    
    match_fab = re.search(r"(fab|fabrication|fabriqué)\s*[: ]*(\d{2}\s*/\s*\d{4})", text, re.IGNORECASE)
    if match_fab:
        data["Date_Fabrication"] = match_fab.group(2).replace(" ", "")
    
    match_lot = re.search(r"(lot|n° de lot)\s*[: ]*(\w+)", text, re.IGNORECASE)
    if match_lot:
        data["Numero_Lot"] = match_lot.group(2)
    
    # Extraction de la quantité en boîte
    match_qty = re.search(r"(bo[iî]te|flacon|gélule|sachet)s?\s*de\s*(\d+)", text, re.IGNORECASE)
    if match_qty:
        data["Quantite_Boite"] = int(match_qty.group(2))  # Quantité en boîte
    
    # Extraction des prix
    match_prix = re.search(r"prix\s*[: ]*([\d,]+)", text, re.IGNORECASE)
    if match_prix:
        data["Prix"] = float(match_prix.group(1).replace(',', '.'))
    
    match_ppa = re.search(r"(ppa|prix public)\s*[: ]*([\d,]+)\s*DA", text, re.IGNORECASE)
    if match_ppa:
        data["PPA"] = float(match_ppa.group(2).replace(',', '.'))
    
    match_tarif = re.search(r"(tarif de réf|t.r|tr)\s*[: ]*([\d,]+)\s*DA", text, re.IGNORECASE)
    if match_tarif:
        data["Tarif_Reference"] = float(match_tarif.group(1).replace(',', '.'))
    
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
        # Créer une nouvelle fenêtre pour afficher le tableau
        window = tk.Toplevel()
        window.title("Contenu du fichier CSV")
        
        frame = ttk.Frame(window, padding="3 3 12 12")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        
        # Créer le Treeview avec les colonnes du CSV
        tree = ttk.Treeview(frame, columns=list(df.columns), show="headings")
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Insérer les lignes du DataFrame dans le Treeview
        for _, row in df.iterrows():
            tree.insert("", tk.END, values=list(row))
        
        tree.grid(row=0, column=0, sticky="nsew")
        
        # Ajouter une scrollbar verticale
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
    
    # Créer le fichier CSV s'il n'existe pas (avec entête)
    if not os.path.exists(csv_file):
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
    
    # Créer la fenêtre principale du menu Tkinter
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
