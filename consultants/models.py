from django.db import models


class Consultant(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    domaine_principal = models.CharField(max_length=50, null=True, blank=True)
    experience_totale = models.IntegerField(default=0)
    disponibilite = models.BooleanField(default=True)
    competences = models.TextField(null=True, blank=True)  # Stocker les compétences sous forme de texte
    cv_fichier = models.FileField(upload_to='cvs/')  # Stocker le fichier CV

    def __str__(self):
        return self.nom if self.nom else "Consultant sans nom"

class AppelOffre(models.Model):
    titre = models.CharField(max_length=255)
    organisme = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    date_limite = models.DateField()
    statut = models.CharField(choices=[('Ouvert', 'Ouvert'), ('Clôturé', 'Clôturé')], max_length=10)

class Mission(models.Model):
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE)
    appel_offre = models.ForeignKey(AppelOffre, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(choices=[('Assignée', 'Assignée'), ('En cours', 'En cours'), ('Terminée', 'Terminée')], max_length=10)
