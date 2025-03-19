from rest_framework import serializers
from .models import Consultant

class ConsultantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultant
        fields = ['nom', 'prenom', 'email', 'telephone', 'pays', 'ville', 'date_debut_dispo', 'date_fin_dispo', 'cv']

