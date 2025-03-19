from django.db import models

# Consultant
class Consultant(models.Model):
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    email = models.EmailField(max_length=255)
    telephone = models.CharField(max_length=20)
    pays = models.CharField(max_length=50)
    ville = models.CharField(max_length=50)
    date_debut_dispo = models.DateField()
    date_fin_dispo = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    # cv = models.FileField(upload_to="cv/", null=True, blank=True)  # Ajout du champ

    def __str__(self):
        return f"{self.nom} {self.prenom}"

# Compétences
class Competence(models.Model):
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="competences")
    nom_competence = models.CharField(max_length=100)
    niveau = models.IntegerField()

    def __str__(self):
        return f"{self.nom_competence} ({self.niveau})"

# Appels d'Offres
class AppelOffre(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    nom_projet = models.CharField(max_length=255)
    description = models.TextField()
    budget_usd = models.DecimalField(max_digits=15, decimal_places=2)
    date_limite = models.DateField()
    methode_passation = models.CharField(max_length=50)
    statut = models.CharField(max_length=20)

    def __str__(self):
        return self.nom_projet

# Critères d'Évaluation
class CriteresEvaluation(models.Model):
    appel_offre = models.ForeignKey(AppelOffre, on_delete=models.CASCADE, related_name="criteres")
    nom_critere = models.CharField(max_length=255)
    poids = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.nom_critere

# Missions
class Mission(models.Model):
    appel_offre = models.ForeignKey(AppelOffre, on_delete=models.CASCADE, related_name="missions")
    titre = models.CharField(max_length=255)
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=20)

    def __str__(self):
        return self.titre

# Participation aux missions
class ParticipationMission(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="participants")
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="missions")
    role = models.CharField(max_length=50)
    evaluation = models.IntegerField()

    def __str__(self):
        return f"{self.consultant} - {self.role}"

# Documents
class Document(models.Model):
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="documents")
    type_document = models.CharField(max_length=20)
    fichier = models.FileField(upload_to="documents/", null=True, blank=True)
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.fichier.name

# Projets
class Projet(models.Model):
    nom = models.CharField(max_length=255)
    responsable = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

# Suivi des Projets
class SuiviProjet(models.Model):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="suivi")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="suivi_projet")
    avancement = models.DecimalField(max_digits=5, decimal_places=2)
    date_maj = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Suivi {self.projet} - {self.avancement}%"

