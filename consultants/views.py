from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
import PyPDF2
from .models import Consultant, Competence
from .serializers import ConsultantSerializer

class UploadCV(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ConsultantSerializer(data=request.data)
        if serializer.is_valid():
            consultant = serializer.save()
            self.extract_competences(consultant.cv.path, consultant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def extract_competences(self, file_path, consultant):
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = " ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
            
            # Supposons que certaines compétences clés soient reconnues
            competences_reconnues = ["Python", "Django", "SQL", "Machine Learning"]
            for comp in competences_reconnues:
                if comp.lower() in text.lower():
                    Competence.objects.create(consultant=consultant, nom_competence=comp, niveau=5)
