from django.core.management.base import BaseCommand
import fitz  # PyMuPDF
import os
import re
import pytesseract
import spacy
from PIL import Image
from consultants.models import Consultant, Competence
from django.utils.dateparse import parse_date
from django.db import transaction

# Configuration de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Chargement du modèle SpaCy pour le français
nlp = spacy.load("fr_core_news_sm")

# Liste des villes et pays associés
CITY_COUNTRY_MAP = {
    "Nouakchott": "Mauritanie",
    "Dakar": "Sénégal",
    "Casablanca": "Maroc",
    "Tunis": "Tunisie",
    "Alger": "Algérie",
    "Paris": "France",
    "Montréal": "Canada",
    "Bamako": "Mali",
    "Abidjan": "Côte d'Ivoire",
}

class Command(BaseCommand):
    help = "Analyse tous les CVs dans un dossier et enregistre chaque consultant en base de données"

    def handle(self, *args, **kwargs):
        cv_folder = r"C:\Users\HP\Downloads\cvs"

        if not os.path.exists(cv_folder):
            self.stdout.write(self.style.ERROR(f"Le dossier {cv_folder} n'existe pas."))
            return

        pdf_files = [f for f in os.listdir(cv_folder) if f.endswith(".pdf")]

        if not pdf_files:
            self.stdout.write(self.style.WARNING("Aucun fichier PDF trouvé dans le dossier."))
            return

        for pdf_file in pdf_files:
            pdf_path = os.path.join(cv_folder, pdf_file)
            print(f"\nTraitement du fichier : {pdf_file}")

            cv_data = self.extract_cv_data(pdf_path)

            if cv_data:
                self.save_cv_to_db(cv_data)
            else:
                print(f"Aucune donnée extraite pour {pdf_file}.")

    def extract_cv_data(self, pdf_path):
        """Extraction des informations depuis un CV PDF"""
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text("text") for page in doc)

        if not text.strip():
            print("Aucun texte détecté, utilisation de l'OCR...")
            text = self.extract_text_with_ocr(doc)

        print("======== Texte extrait du CV ========")
        print(text)
        print("=====================================")

        # Extraction des informations principales
        email = self.extract_email(text)
        telephone = self.extract_phone(text)
        nom, prenom = self.extract_name_spacy(text, email)
        ville, pays = self.extract_location(text)
        competences = self.extract_competences(text)

        if not email:
            print(f"Aucun email trouvé pour {nom} {prenom}. CV ignoré.")
            return None

        print(f"Nom: {nom}, Prénom: {prenom}, Email: {email}, Téléphone: {telephone}")
        print(f"Pays: {pays}, Ville: {ville}")
        print(f"Compétences: {competences}")

        return {
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "telephone": telephone,
            "ville": ville,
            "pays": pays,
            "competences": competences
        }

    def extract_text_with_ocr(self, doc):
        """Utilisation de l'OCR si aucun texte n'est extrait"""
        text = ""
        for page_num in range(len(doc)):
            pix = doc[page_num].get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img, lang="fra", config="--psm 6") + "\n"
        return text

    def extract_email(self, text):
        """Extraction de l'email avec validation du format"""
        email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        return email_match.group(0) if email_match else None

    def extract_phone(self, text):
        """Extraction du téléphone avec correction du format"""
        phone_match = re.search(r"\+?\d[\d\s-]{8,}\d", text)
        return phone_match.group(0) if phone_match else "Non spécifié"

    def extract_name_spacy(self, text, email=None):
        """Utilisation de SpaCy et email pour détecter le nom et prénom"""
        doc = nlp(text)
        noms_detectes = []

        # 1️⃣ Étape 1 : Utiliser SpaCy pour détecter les noms
        for ent in doc.ents:
            if ent.label_ == "PER":
                noms_detectes.append(ent.text)

        # 2️⃣ Étape 2 : Si SpaCy ne trouve rien, essayer d'extraire depuis l'email
        if email and not noms_detectes:
            username = email.split("@")[0]
            username_parts = re.split(r'[._-]', username)
            if len(username_parts) >= 2:
                return username_parts[0].capitalize(), username_parts[1].capitalize()

        # 3️⃣ Étape 3 : Sinon, chercher des mots en majuscule dans le texte
        if not noms_detectes:
            words = text.split()
            for i in range(len(words) - 1):
                if words[i].istitle() and words[i+1].istitle():
                    return words[i], words[i+1]

        # 4️⃣ Étape 4 : Retourner le premier nom trouvé par SpaCy
        if noms_detectes:
            name_parts = noms_detectes[0].split()
            if len(name_parts) >= 2:
                return name_parts[0], " ".join(name_parts[1:])
        
        return "Inconnu", "Inconnu"

    def extract_location(self, text):
        """Détection de la ville et pays à partir du texte du CV"""
        ville, pays = "Non spécifiée", "Non spécifié"

        for city in CITY_COUNTRY_MAP.keys():
            if re.search(rf"\b{city}\b", text, re.IGNORECASE):
                ville = city
                pays = CITY_COUNTRY_MAP[city]
                break

        return ville, pays

    def extract_competences(self, text):
        """Détection des compétences techniques à partir du texte du CV"""
        competences_match = re.findall(
            r"\b(Flask|PHP|Python|Django|Git|GitHub|Docker|Figma|Big Data|Spring Boot|Angular|Machine Learning|MySQL|MongoDB|Java|Laravel|HTML|CSS|JavaScript|React|Typescript|AWS|Oracle)\b",
            text, re.IGNORECASE
        )
        return list(set([c.strip() for c in competences_match if c.strip()]))


    def save_cv_to_db(self, cv_data):
        """Sauvegarde chaque consultant en base de données"""
        try:
            with transaction.atomic():
                consultant, created = Consultant.objects.update_or_create(
                    email=cv_data["email"],
                    defaults={
                        "nom": cv_data["nom"],
                        "prenom": cv_data["prenom"],
                        "telephone": cv_data["telephone"],
                        "ville": cv_data["ville"],
                        "pays": cv_data["pays"],
                        "date_debut_dispo": parse_date("2024-01-01"),
                        "date_fin_dispo": parse_date("2024-12-31"),
                    }
                )

                print(f"Consultant {cv_data['nom']} {cv_data['prenom']} {'ajouté' if created else 'mis à jour'}.")
                
                consultant.competences.set([
                    Competence.objects.get_or_create(nom_competence=comp)[0]
                    for comp in cv_data["competences"]
                ])

                print("Compétences enregistrées.")

        except Exception as e:
            print(f"Erreur lors de l'enregistrement du consultant : {e}")

