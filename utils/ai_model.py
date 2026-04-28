def predire_fatigue(age, revenu, etudiant, travail, score_coherence=100):
    """Analyse la fatigue en tenant compte de la sincérité du profil."""
    
    # Si l'utilisateur a trop menti, l'IA se fâche
    if score_coherence < 50:
        return "Analyse impossible : Ton profil est un tissu de mensonges ! 🤥"

    # Calcul de base
    fatigue_points = 0
    if age > 45: fatigue_points += 20
    if travail == "oui": fatigue_points += 30
    if etudiant == "oui": fatigue_points += 25
    if revenu < 30000: fatigue_points += 15 # Stress financier

    # Verdict
    if fatigue_points > 70:
        return "Épuisement total... Pose ce téléphone ! 🪫"
    elif fatigue_points > 40:
        return "Besoin d'un bon café et d'une sieste. ☕"
    else:
        return "Énergie au top, tu rayonnes ! ☀️"