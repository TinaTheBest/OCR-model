import requests

# URL de l'API OCR.space
url = 'https://api.ocr.space/parse/image'

# Chemin de votre image
image_path = 'dataset/vignette.jpg'

# Votre clé API
api_key = 'K84545075888957'

# Paramètres supplémentaires pour une meilleure précision
payload = {
    'apikey': api_key,
    'language': 'fre',  # Spécifie la langue française
    'isOverlayRequired': True,
    'detectOrientation': True  ,
    'OCREngine': 2,  # Utilise l'OCR Engine 2 pour une meilleure qualité
}

# Envoyer l'image à l'API OCR.space
with open(image_path, 'rb') as f:
    response = requests.post(url, files={'file': f}, data=payload)

# Analyse de la réponse JSON
result = response.json()

# Afficher le texte extrait
if 'ParsedResults' in result:
    print("Texte extrait : ", result['ParsedResults'][0]['ParsedText'])
else:
    print("Erreur dans la réponse de l'API :", result)
