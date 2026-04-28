from flask import Flask, render_template, request, redirect, url_for, flash
from utils.ai_model import predire_fatigue
import sqlite3, os, json

app = Flask(__name__)
app.secret_key = "K3lly_C0h3r4_AI_2026_Secure" 
DB_PATH = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la structure si elle n'existe pas."""
    conn = get_db_connection()
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS collectes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, age INTEGER, pays TEXT, etudiant TEXT, niveau TEXT, 
            travail TEXT, revenu INTEGER, fatigue_ressentie TEXT, sommeil INTEGER,
            score_coherence INTEGER, verdict TEXT, fatigue_ia TEXT, 
            date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.close()

def auditer_coherence(data):
    """Analyse rigoureuse et taquine des données saisies."""
    score = 100
    remarques = []
    
    # 1. Analyse de l'âge
    if data['age'] <= 0:
        score -= 50
        remarques.append("0 an ? Tu es un concept abstrait ou un futur génie pas encore né ? 🐣")
    elif data['age'] > 115:
        score -= 40
        remarques.append(f"{data['age']} ans ? Respect pour ta longévité, ou ton imagination débordante ! 🦖")

    # 2. Analyse Revenu vs Travail
    if data['travail'] == "non" and data['revenu'] > 0:
        if data['revenu'] > 100000:
            score -= 40
            remarques.append("Pas de job mais un revenu de PDG... On blanchit de l'argent ou on a un oncle en Amérique ? 💸")
        else:
            remarques.append("Pas d'emploi mais des revenus ? La vie de rentier a l'air douce ! 🍷")
    
    # 3. Analyse Sommeil
    if data['sommeil'] < 2:
        score -= 30
        remarques.append("Moins de 2h de sommeil... Tu es un robot ou tu vis sur une autre planète ? 🧛")
    elif data['sommeil'] > 18:
        score -= 20
        remarques.append("18h de dodo ? C'est une expertise fatigue, pas une étude sur l'hibernation des ours ! 🐻")

    # 4. Analyse Études vs Âge
    if data['etudiant'] == "oui" and data['age'] < 6:
        score -= 50
        remarques.append("Déjà étudiant à cet âge ? Bébé prodige ou petite erreur de saisie ? 👶")

    # Verdict final
    if score >= 90:
        verdict = "Sincère ✨"
    elif score >= 60:
        verdict = "Suspect 🤨"
    else:
        verdict = "Mythomane 🏆"
        
    return score, verdict, remarques

@app.route('/')
def home():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except:
        questions = []
    return render_template("index.html", questions=questions)

@app.route('/analyse', methods=['POST'])
def analyse():
    # Conversion sécurisée sans plantage
    def force_int(val):
        try: return int(float(str(val).strip()))
        except: return 0

    data = {
        "nom": request.form.get("nom", "Anonyme"),
        "age": force_int(request.form.get("age")),
        "pays": request.form.get("pays", "Inconnu"),
        "etudiant": request.form.get("etudiant", "non"),
        "niveau": request.form.get("niveau", "aucun"),
        "travail": request.form.get("travail", "non"),
        "revenu": force_int(request.form.get("revenu")),
        "fatigue": request.form.get("fatigue", "non"),
        "sommeil": force_int(request.form.get("sommeil"))
    }

    score, verdict, critiques = auditer_coherence(data)
    res_fatigue = predire_fatigue(data['age'], data['revenu'], data['etudiant'], data['travail'], score)

    # Sauvegarde
    try:
        conn = get_db_connection()
        with conn:
            conn.execute("""INSERT INTO collectes 
                (nom, age, pays, etudiant, niveau, travail, revenu, fatigue_ressentie, sommeil, score_coherence, verdict, fatigue_ia) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (data['nom'], data['age'], data['pays'], data['etudiant'], data['niveau'], data['travail'], 
                 data['revenu'], data['fatigue'], data['sommeil'], score, verdict, res_fatigue))
        conn.close()
    except:
        pass

    return render_template("result.html", nom=data['nom'], score=score, verdict=verdict, remarques=critiques, niveau_fatigue=res_fatigue)

@app.route('/historique')
def historique():
    try:
        conn = get_db_connection()
        rows = conn.execute('SELECT * FROM collectes ORDER BY date_saisie DESC').fetchall()
        conn.close()
        total = len(rows)
        return render_template('dashboard.html', logs=rows, total=total)
    except:
        return "Faites d'abord un test pour initialiser les archives ! 🌸"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)