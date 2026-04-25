import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = "model.pkl"
DATA_PATH = "data.csv"

# Variable globale pour garder le modèle en mémoire (évite de recharger le fichier à chaque clic)
_model_cache = None

def entrainer_modele():
    """Entraîne le modèle si les données sont suffisantes."""
    if not os.path.exists(DATA_PATH):
        print("⚠️ Aucun fichier data.csv trouvé pour l'entraînement.")
        return None

    try:
        data = pd.read_csv(DATA_PATH)
        
        # Vérification du volume minimum pour que l'IA ait un sens
        if len(data) < 5: 
            print("⚠️ Pas assez de données (min 5) pour un entraînement IA.")
            return None

        # Nettoyage et encodage
        mapping = {"oui": 1, "non": 0}
        data["etudiant"] = data["etudiant"].map(mapping)
        data["travail"] = data["travail"].map(mapping)
        data["fatigue"] = data["fatigue"].map(mapping)
        
        data = data.dropna(subset=["age", "revenu", "etudiant", "travail", "fatigue"])

        X = data[["age", "revenu", "etudiant", "travail"]]
        y = data["fatigue"]

        # Entraînement
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)

        # Sauvegarde
        joblib.dump(model, MODEL_PATH)
        return model
    except Exception as e:
        print(f"❌ Erreur lors de l'entraînement : {e}")
        return None

def charger_modele():
    """Charge le modèle depuis le disque ou le cache mémoire."""
    global _model_cache
    
    if _model_cache is not None:
        return _model_cache

    if os.path.exists(MODEL_PATH):
        try:
            _model_cache = joblib.load(MODEL_PATH)
            return _model_cache
        except:
            return entrainer_modele()
    
    return entrainer_modele()

def predire_fatigue(age, revenu, etudiant, travail):
    """Prédit la fatigue avec fallback sur logique métier si l'IA n'est pas prête."""
    model = charger_modele()

    # Logique de repli (Fallback) si l'IA n'est pas encore entraînée
    if model is None:
        # Une règle simple pour ne pas renvoyer "non" tout le temps au début
        if (age < 25 and etudiant == "oui") or (travail == "oui" and revenu < 1200):
            return "Fatigué (Logique)"
        return "Reposé (Logique)"

    # Préparation des données pour la prédiction
    e_val = 1 if etudiant == "oui" else 0
    t_val = 1 if travail == "oui" else 0
    
    try:
        df_predict = pd.DataFrame([[age, revenu, e_val, t_val]], 
                                  columns=["age", "revenu", "etudiant", "travail"])
        prediction = model.predict(df_predict)
        return "Fatigué" if prediction[0] == 1 else "Reposé"
    except:
        return "Analyse impossible"