from rest_framework import serializers
from .models import Consultant, Competence

class ConsultantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultant
        fields = [
            'user',
            'nom',
            'prenom',
            'email',
            'telephone',
            'pays',
            'ville',
            'date_debut_dispo',
            'date_fin_dispo',
            'cv',
        ]


class CompetenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competence
        fields = ['id', 'nom_competence', 'niveau', 'consultant']
