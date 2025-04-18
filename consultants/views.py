import re, fitz, pytesseract
from PIL import Image, ImageEnhance
import spacy
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Consultant, Competence, User
from .serializers import ConsultantSerializer, CompetenceSerializer

# Charger le modèle NLP de spaCy
nlp = spacy.load("en_core_web_sm")


def extract_competences_from_cv(file_path):
    try:
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text("text") for page in doc])

        if not text.strip():
            text = ""
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img = img.convert("L")
                img = ImageEnhance.Contrast(img).enhance(3.0)
                img = ImageEnhance.Sharpness(img).enhance(2.0)
                text += pytesseract.image_to_string(img, lang="eng")

        doc_nlp = nlp(text)
        competences = set()

        for ent in doc_nlp.ents:
            if ent.label_ in ["ORG", "PRODUCT", "SKILL", "WORK_OF_ART", "LANGUAGE"]:
                cleaned = ent.text.strip().title()
                if 2 < len(cleaned) < 40 and not re.search(r"\d", cleaned):
                    competences.add(cleaned)

        for token in doc_nlp:
            if token.pos_ in ["PROPN", "NOUN"] and token.is_alpha and token.ent_type_ == "":
                cleaned = token.text.strip().title()
                if 2 < len(cleaned) < 30:
                    competences.add(cleaned)

        return list(competences)

    except Exception as e:
        print("Erreur NLP:", e)
        return []


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def consultant_register(request):
    try:
        email = request.data.get('email')
        nom = request.data.get('nom') or 'Consultant'
        password = request.data.get('password') or 'consultant123'

        if User.objects.filter(username=email).exists():
            return Response({"error": "Un utilisateur avec cet email existe déjà."}, status=400)

        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                nom=nom,
                role='CONSULTANT'
            )

            data = request.data.copy()
            data['user'] = user.id
            serializer = ConsultantSerializer(data=data)

            if serializer.is_valid():
                consultant = serializer.save()
                competences = []

                cv_file = request.FILES.get('cv')
                if cv_file:
                    path = default_storage.save(f"cvs/{cv_file.name}", cv_file)
                    file_path = default_storage.path(path)

                    competences = extract_competences_from_cv(file_path)

                    for nom_comp in competences:
                        try:
                            Competence.objects.create(
                                consultant=consultant,
                                nom_competence=nom_comp,
                                niveau=1
                            )
                        except Exception as e:
                            print(f"Erreur compétence {nom_comp} :", e)

                return Response({
                    "message": "Consultant créé avec succès.",
                    "consultant_id": consultant.id,
                    "competences": competences
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print("💥 Exception:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def consultant_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    try:
        user = User.objects.get(username=email)
        if not user.check_password(password):
            return Response({"error": "Mot de passe incorrect"}, status=400)

        if not hasattr(user, 'consultant_profile'):
            return Response({"error": "Ce compte n’est pas un consultant"}, status=400)

        return Response({"consultant_id": user.consultant_profile.id})
    except User.DoesNotExist:
        return Response({"error": "Email incorrect"}, status=404)


@api_view(['GET'])
def consultant_data(request, consultant_id):
    try:
        consultant = get_object_or_404(Consultant, id=consultant_id)
        competences = Competence.objects.filter(consultant=consultant)
        competences_list = [c.nom_competence for c in competences]

        nb = len(competences_list)
        expertise = "Expert" if nb >= 10 else "Intermédiaire" if nb >= 5 else "Débutant"

        return Response({
            "firstName": consultant.prenom,
            "lastName": consultant.nom,
            "email": consultant.user.email,
            "phone": consultant.telephone,
            "country": consultant.pays,
            "city": consultant.ville,
            "startAvailability": consultant.date_debut_dispo,
            "endAvailability": consultant.date_fin_dispo,
            "skills": ", ".join(competences_list),
            "expertise": expertise,
            "cvFilename": consultant.cv.name.split('/')[-1] if consultant.cv else None
        })

    except Exception as e:
        print("Erreur récupération consultant:", e)
        return Response({"error": "Erreur lors de la récupération des données."}, status=500)


@api_view(['GET'])
def consultant_competences(request, consultant_id):
    consultant = get_object_or_404(Consultant, id=consultant_id)
    competences = Competence.objects.filter(consultant=consultant)
    serializer = CompetenceSerializer(competences, many=True)
    return Response(serializer.data)
