from django.core.management.base import BaseCommand
from django.db import transaction
from dateutil.parser import parse as parse_date
import re
import os
import fitz
import logging
from PIL import Image, ImageEnhance
from consultants.models import Consultant, Competence

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration des villes Mauritanie
CITY_COUNTRY_MAP = {
    "Nouakchott": "Mauritanie",
    "Nouadhibou": "Mauritanie",
    "Rosso": "Mauritanie",
    "Kaédi": "Mauritanie",
    "Zouérat": "Mauritanie",
    "Atar": "Mauritanie",
    "Kiffa": "Mauritanie",
    "Sélibaby": "Mauritanie",
    "Aïoun": "Mauritanie",
    "Tidjikja": "Mauritanie",
}

COMMON_FRENCH_NAMES = {
    "mohamed", "mariem", "fatimetou", "abdallah", "aichetou",
    "jean", "marie", "pierre", "sophie", "nouha", "ahmed",
    "ali", "amina", "khadijetou", "brahim", "salma"
}

COMMON_TITLES = {
    "développeur", "ingénieur", "manager", "chef", "projet",
    "technicien", "spécialiste", "analyste", "consultant", "cv"
}

class Command(BaseCommand):
    help = "Extraction des informations de CV PDF"

    def handle(self, *args, **options):
        cv_folder = r"C:\Users\HP\Downloads\cvs"
        
        if not os.path.exists(cv_folder):
            self.stdout.write(self.style.ERROR(f"Dossier introuvable: {cv_folder}"))
            return

        for filename in [f for f in os.listdir(cv_folder) if f.endswith(".pdf")]:
            pdf_path = os.path.join(cv_folder, filename)
            self.stdout.write(f"\n🔍 Traitement de {filename}...")

            try:
                cv_data = self.process_pdf(pdf_path)
                if cv_data:
                    self.save_consultant(cv_data)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur: {str(e)}"))

    def process_pdf(self, path):
        """Traitement principal du PDF"""
        doc = fitz.open(path)
        text = self.extract_text(doc)
        
        if not text:
            self.stdout.write("Aucun texte détecté - Vérifier le format du PDF")
            return None

        return self.parse_cv_data(text)

    def extract_text(self, doc):
        """Extraction du texte avec OCR amélioré"""
        text = "\n".join(page.get_text("text") for page in doc)
        
        if not text.strip() and OCR_AVAILABLE:
            self.stdout.write("Utilisation de l'OCR...")
            text = self.ocr_processing(doc)
        
        return self.clean_text(text)

    def ocr_processing(self, doc):
        """Traitement OCR avancé"""
        full_text = ""
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Prétraitement d'image
            img = img.convert("L")
            img = ImageEnhance.Contrast(img).enhance(3.0)
            img = ImageEnhance.Sharpness(img).enhance(2.0)
            
            # Configuration Tesseract
            config = (
                "-l fra+ara+eng --oem 3 --psm 6 "
                "-c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@.-_àéèêëïîôùûçâäÀÉÈÊËÏÎÔÙÛÇÂÄ"
            )
            
            text = pytesseract.image_to_string(img, config=config)
            full_text += text + "\n"
        
        return full_text

    def clean_text(self, text):
        """Nettoyage du texte pour l'analyse"""
        replacements = [
            (r"\s+", " "),
            (r"\s?[@\.]\s?", lambda m: m.group().strip()),
            (r"ﬁ", "fi"),
            (r"ﬂ", "fl"),
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
            
        return text.strip()

    def parse_cv_data(self, text):
        """Extraction des données CV"""
        email = self.extract_email(text)
        phone = self.extract_phone(text)
        nom, prenom = self.extract_name(text, email)
        ville, pays = self.extract_location(text)
        competences = self.extract_skills(text)

        if not email:
            self.stdout.write("Aucun email détecté - CV ignoré")
            return None

        return {
            "email": email,
            "nom": nom,
            "prenom": prenom,
            "telephone": phone,
            "ville": ville,
            "pays": pays,
            "competences": competences,
        }

    def extract_email(self, text):
        """Détection robuste d'email"""
        email_regex = r"""
            (?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+
            (?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*
            |"
            (?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]
            |\\[\x01-\x09\x0b\x0c\x0e-\x7f])*"
            )@
            (?:(?:[a-z0-9]
            (?:[a-z0-9-]*[a-z0-9])?
            \.)+
            [a-z0-9]
            (?:[a-z0-9-]*[a-z0-9])?
            |\[
            (?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}
            (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)
            \])
        """
        match = re.search(email_regex, text, re.VERBOSE | re.IGNORECASE)
        return match.group(0).lower() if match else None

    def extract_phone(self, text):
        """Détection des numéros Mauritaniens"""
        patterns = [
            r"(?:\+?222|00222)[\s-]?(\d{2}[\s-]?){3}\d{2}",  # International
            r"(?:06|07|05|02)[\s-]?(\d{2}[\s-]?){3}\d{2}",    # National
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return re.sub(r"\s|-", "", match.group())
        return "Non spécifié"

    def extract_name(self, text, email):
        """Extraction des noms avec priorité CV"""
        # Stratégie avancée : utiliser le prénom et le nom à partir des patterns détectés
        name_match = re.search(
            r"(?i)(?:nom|name)[\s:]*([A-ZÉÈÇÀÂÊÎÔÛËÏÖÜ][a-zéèçàâêîôûëïöüÿæœ]+)[\s,]+([A-ZÉÈÇÀÂÊÎÔÛËÏÖÜ][a-zéèçàâêîôûëïöüÿæœ]+)",
            text,
        )
        if name_match:
            return name_match.group(1), name_match.group(2)

        # Si le CV contient un email, nous extrayons aussi le nom de l'email
        if email:
            username = email.split("@")[0]
            parts = re.split(r"[._-]", username)
            if len(parts) >= 2:
                return parts[0].capitalize(), parts[1].capitalize()
        
        return ("Inconnu", "Inconnu")

    def extract_location(self, text):
        """Détection de la localisation"""
        for city, country in CITY_COUNTRY_MAP.items():
            if re.search(rf"\b{re.escape(city)}\b", text, re.IGNORECASE):
                return city, country
        return ("Non spécifié", "Mauritanie")

    def extract_skills(self, text):
        """Détection des compétences"""
        skills = [
            "Python", "Django", "Flask", "Java", "JavaScript",
            "React", "Angular", "PHP", "Laravel", "SQL",
            "PostgreSQL", "MongoDB", "Docker", "Git", "AWS",
            "Machine Learning", "Data Analysis", "Power BI",
        ]
        return [skill for skill in skills if re.search(rf"\b{skill}\b", text, re.IGNORECASE)]

    def save_consultant(self, data):
        """Sauvegarde en base de données"""
        try:
            with transaction.atomic():
                consultant, created = Consultant.objects.update_or_create(
                    email=data["email"],
                    defaults={
                        "nom": data["nom"],
                        "prenom": data["prenom"],
                        "telephone": data["telephone"],
                        "ville": data["ville"],
                        "pays": data["pays"],
                        "date_debut_dispo": parse_date("2024-01-01"),
                        "date_fin_dispo": parse_date("2024-12-31"),
                    },
                )

                for competence in data["competences"]:
                    Competence.objects.get_or_create(
                        consultant=consultant,
                        nom_competence=competence,
                        defaults={"niveau": 2},
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{'Créé' if created else 'Mis à jour'} : "
                        f"{data['prenom']} {data['nom']}"
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur DB: {str(e)}"))
