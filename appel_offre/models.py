from django.db import models

class DonneesBase(models.Model):
    numero = models.CharField(max_length=50, unique=True, verbose_name="Numéro")
    financement = models.CharField(max_length=255, verbose_name="Financement")
    nom_projet = models.CharField(max_length=255, verbose_name="Nom du projet ou entité administrative")
    
    PREVU_REEL_CHOICES = [
        ('PREVU', 'Prévu'),
        ('REEL', 'Réel')
    ]
    prevu_vs_reel = models.CharField(max_length=10, choices=PREVU_REEL_CHOICES, verbose_name="Prévu vs. Réel")

    preselections = models.BooleanField(default=False, verbose_name="Présélection (oui/non)")

    methode_passation = models.CharField(max_length=255, verbose_name="Méthode de passation des marchés")

    montant_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Montant (USD)")
    montant_mru = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Montant (MRU)")

    def __str__(self):
        return f"{self.nom_projet} - {self.numero}"
    
    class ProcedurePreselection(models.Model):
       appel_offre = models.ForeignKey(DonneesBase, on_delete=models.CASCADE, related_name="preselections")
       date_publication = models.DateField(null=True, blank=True)
       soumission_TER = models.DateField(null=True, blank=True, verbose_name="Soumission du TER")
       date_non_objection_TER = models.DateField(null=True, blank=True, verbose_name="Date de non-objection du TER")
       submission_CER = models.DateField(null=True, blank=True, verbose_name="Soumission du CER")
       date_non_objection_CER = models.DateField(null=True, blank=True, verbose_name="Date de non-objection du CER")

    statut = models.CharField(max_length=50, choices=[
        ('EN COURS', 'En cours'),
        ('FINALISEE', 'Finalisée')
    ], default='EN COURS')

    def __str__(self):
        return f"Présélection pour {self.appel_offre.nom_projet}"

class ProcedureProposition(models.Model):
    appel_offre = models.ForeignKey(DonneesBase, on_delete=models.CASCADE, related_name="propositions")
    consultant = models.ForeignKey("consultant.Consultant", on_delete=models.CASCADE, related_name="propositions")
    date_soumission = models.DateField()
    montant_propose_usd = models.DecimalField(max_digits=15, decimal_places=2)
    montant_propose_mru = models.DecimalField(max_digits=15, decimal_places=2)
    document_proposition = models.FileField(upload_to="propositions/", null=True, blank=True)

    # Ajout des étapes de validation
    soumission_TER = models.DateField(null=True, blank=True, verbose_name="Soumission du TER")
    date_non_objection_TER = models.DateField(null=True, blank=True, verbose_name="Date de non-objection du TER")
    submission_CER = models.DateField(null=True, blank=True, verbose_name="Soumission du CER")
    date_non_objection_CER = models.DateField(null=True, blank=True, verbose_name="Date de non-objection du CER")

    statut = models.CharField(max_length=50, choices=[
        ('EN ATTENTE', 'En attente'),
        ('ACCEPTEE', 'Acceptée'),
        ('REJETEE', 'Rejetée')
    ], default='EN ATTENTE')

    def __str__(self):
        return f"Proposition de {self.consultant.nom} pour {self.appel_offre.nom_projet}"


class Evaluation(models.Model):
    proposition = models.ForeignKey(ProcedureProposition, on_delete=models.CASCADE, related_name="evaluations")
    critere_technique = models.DecimalField(max_digits=5, decimal_places=2, help_text="Score technique sur 100")
    critere_financier = models.DecimalField(max_digits=5, decimal_places=2, help_text="Score financier sur 100")
    critere_experience = models.DecimalField(max_digits=5, decimal_places=2, help_text="Score d'expérience sur 100")
    commentaire = models.TextField(null=True, blank=True)
    score_final = models.DecimalField(max_digits=5, decimal_places=2, help_text="Score total sur 100", null=True, blank=True)

    # Étapes de validation
    soumission_TER = models.DateField(null=True, blank=True, verbose_name="Soumission du TER")
    date_non_objection_TER = models.DateField(null=True, blank=True, verbose_name="Date de non-objection du TER")
    submission_CER = models.DateField(null=True, blank=True, verbose_name="Soumission du CER")
    date_non_objection_CER = models.DateField(null=True, blank=True, verbose_name="Date de non-objection du CER")

    def save(self, *args, **kwargs):
        self.score_final = (self.critere_technique * 0.5) + (self.critere_financier * 0.3) + (self.critere_experience * 0.2)
        super(Evaluation, self).save(*args, **kwargs)

    def __str__(self):
        return f"Évaluation de {self.proposition.consultant.nom} - Score {self.score_final}/100"


class AttributionContrat(models.Model):
    appel_offre = models.ForeignKey(DonneesBase, on_delete=models.CASCADE, related_name="attributions")
    consultant = models.ForeignKey("consultant.Consultant", on_delete=models.CASCADE, related_name="contrats_attribues")
    date_attribution = models.DateField()
    montant_final_usd = models.DecimalField(max_digits=15, decimal_places=2)
    montant_final_mru = models.DecimalField(max_digits=15, decimal_places=2)
    contrat_no = models.CharField(max_length=100, unique=True)
    date_signature = models.DateField()
    signataire = models.CharField(max_length=255)
    date_achevement = models.DateField(null=True, blank=True)
    document_contrat = models.FileField(upload_to="contrats/", null=True, blank=True)

    def __str__(self):
        return f"Contrat {self.contrat_no} attribué à {self.consultant.nom}"

