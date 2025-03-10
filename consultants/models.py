from django.db import models

class Consultant(models.Model):
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    pays = models.CharField(max_length=50)
    ville = models.CharField(max_length=50)
    disponibilite = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

class Competence(models.Model):
    NIVEAU_CHOICES = [
        ('Débutant', 'Débutant'),
        ('Intermédiaire', 'Intermédiaire'),
        ('Expert', 'Expert'),
    ]
    
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="competences")
    nom_competence = models.CharField(max_length=100)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)

    def __str__(self):
        return f"{self.nom_competence} ({self.niveau})"

class Experience(models.Model):
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="experiences")
    entreprise = models.CharField(max_length=100)
    poste = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.poste} chez {self.entreprise}"

class Document(models.Model):
    TYPE_DOCUMENT_CHOICES = [
        ('CV', 'CV'),
        ('Diplôme', 'Diplôme'),
        ('Contrat', 'Contrat'),
    ]
    
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="documents")
    nom_fichier = models.FileField(upload_to='documents/')
    type_document = models.CharField(max_length=50, choices=TYPE_DOCUMENT_CHOICES)
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom_fichier} ({self.type_document})"

class HistoriqueMission(models.Model):
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="missions")
    id_mission = models.IntegerField()  # Lien vers une autre BD "Mission"
    role = models.CharField(max_length=50)
    evaluation = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Mission {self.id_mission} - {self.role}"
