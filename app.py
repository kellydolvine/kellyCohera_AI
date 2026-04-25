from flask import Flask, render_template, request, redirect, url_for, flash
from utils.ai_model import predire_fatigue
import json, sqlite3, random, os

app = Flask(__name__)
# Une clé secrète complexe pour une sécurité maximale
app.secret_key = "K3lly_C0h3r4_4I_U1tr4_S3cur3_2026!#" 
DB_PATH = "database.db"

# --- 🛠️ ARCHITECTURE ET RIGUEUR SQL ---

def get_db_connection():
    """Établit une connexion avec gestion fine des types."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Erreur fatale de connexion DB: {e}")
        return None

def init_db():
    """Initialise la base avec des contraintes d'intégrité strictes."""
    conn = get_db_connection()
    if conn:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS collectes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                age INTEGER NOT NULL CHECK(age BETWEEN 0 AND 120),
                etudiant TEXT NOT NULL,
                niveau TEXT NOT NULL,
                travail TEXT NOT NULL,
                revenu INTEGER NOT NULL CHECK(revenu >= 0),
                score_coherence INTEGER NOT NULL CHECK(score_coherence BETWEEN 0 AND 100),
                verdict TEXT NOT NULL,
                fatigue_ia TEXT,
                date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
        print("✅ Système KellyCohera_AI : Base de données certifiée et opérationnelle.")

# --- 🧠 LOGIQUE DE VALIDATION ET ANALYSE ---

def filtrer_entrees(form):
    """
    Validation rigoureuse des données entrantes. 
    Si l'utilisateur tente d'injecter n'importe quoi, on le bloque.
    """
    try:
        nom = form.get("nom", "Anonyme").strip()[:50] # Limite à 50 caractères
        age = int(form.get("age") or 0)
        revenu = int(form.get("revenu") or 0)
        etudiant = form.get("etudiant", "non").lower()
        travail = form.get("travail", "non").lower()
        niveau = form.get("niveau", "aucun").lower()

        if not nom: return None, "Le nom est obligatoire, même pour les agents secrets."
        if age <= 0: return None, "L'âge doit être un nombre positif. Tu n'es pas encore un projet ?"
        
        return {
            "nom": nom, "age": age, "revenu": revenu,
            "etudiant": etudiant, "travail": travail, "niveau": niveau
        }, None
    except ValueError:
        return None, "Erreur de format : stop aux lettres dans les chiffres ! 🛑"

@app.route('/')
def home():
    try:
        with open("questions.json", "r", encoding="utf-8") as f:
            questions = json.load(f)
    except Exception:
        questions = []
    return render_template("index.html", questions=questions)

@app.route('/analyse', methods=['POST'])
def analyse():
    # 1. Passage au filtre de rigueur
    data, erreur = filtrer_entrees(request.form)
    if erreur:
        flash(erreur)
        return redirect(url_for('home'))

    # 2. Algorithme de Cohérence KellyCohera (Zéro Tolérance)
    score = 100
    critiques = []

    # --- Test A : L'argent magique ---
    if data['travail'] == "non" and data['revenu'] > 5000:
        penalite = 40
        score -= penalite
        critiques.append(f"💸 Alerte 'Argent Magique' : {data['revenu']} FCFA sans emploi. KellyCohera suspecte un héritage caché ou une invention.")

    # --- Test B : Le Paradoxe de l'Étudiant ---
    if data['niveau'] == "master" and data['age'] < 19:
        score -= 50
        critiques.append(f"🎓 Paradoxe temporel : Un Master à {data['age']} ans ? Soit tu es l'enfant d'Einstein, soit tu as sauté 6 classes.")

    # --- Test C : Rigueur Légale ---
    if data['travail'] == "oui" and data['age'] < 14:
        score -= 70
        critiques.append("🚨 Anomalie Majeure : Travail déclaré avant 14 ans. Le système refuse la validité de cette saisie.")

    # 3. Bornage mathématique du score
    score = max(0, min(score, 100))
    
    # 4. Verdicts basés sur la précision
    if score >= 85:
        verdict, couleur = "Profil Cristallin 😎", "#2ecc71"
    elif score >= 55:
        verdict, couleur = "Profil Nébuleux 🤔", "#f1c40f"
    else:
        verdict, couleur = "Profil Hautement Incohérent ❌", "#e74c3c"

    # 5. Appel IA avec gestion d'exception
    try:
        fatigue_predite = predire_fatigue(data['age'], data['revenu'], data['etudiant'], data['travail'])
    except Exception:
        fatigue_predite = "Indéterminée (L'IA est perplexe)"

    # 6. Sauvegarde et Persistance
    conn = get_db_connection()
    if conn:
        with conn:
            conn.execute("""INSERT INTO collectes 
                (nom, age, etudiant, niveau, travail, revenu, score_coherence, verdict, fatigue_ia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data['nom'], data['age'], data['etudiant'], data['niveau'], 
                 data['travail'], data['revenu'], score, verdict, fatigue_predite))
    
    blagues = [
        "🌸 KellyCohera_AI a détecté que tu es 100% humain... ou un robot très poli.",
        "😴 Ton score est là, mais ton cerveau est resté sous la couette ?",
        "🤖 Analyse terminée : 0% de virus, mais 100% de fatigue détectée !"
    ]

    return render_template("result.html", 
                           nom=data['nom'], score=score, fatigue=fatigue_predite, 
                           verdict=verdict, critiques=critiques, couleur=couleur, 
                           blague=random.choice(blagues))

@app.route('/historique')
def historique():
    conn = get_db_connection()
    logs = []
    if conn:
        logs = conn.execute("SELECT * FROM collectes ORDER BY date_saisie DESC").fetchall()
    return render_template("historique.html", logs=logs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)