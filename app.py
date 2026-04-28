from flask import Flask, render_template, request, redirect, url_for
from utils.ai_model import predire_fatigue
import sqlite3, os, json

app = Flask(__name__)
app.secret_key = "Kelly_DeepSpace_2026"

# Chemin absolu pour la base de données (Crucial pour Render)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la table si elle n'existe pas."""
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
    """Analyse rigoureuse et taquine."""
    score = 100
    remarques = []
    
    if data['age'] <= 0 or data['age'] > 110:
        score -= 40
        remarques.append(f"Âge de {data['age']} ans ? L'immortalité n'est pas encore supportée par nos serveurs. 🛸")
    
    if data['travail'] == "non" and data['revenu'] > 100000:
        score -= 30
        remarques.append("Un revenu de ministre sans emploi ? On a trouvé le compte caché ! 💸")
    
    if data['sommeil'] < 3 or data['sommeil'] > 18:
        score -= 25
        remarques.append("Ton cycle de sommeil défie les lois de la biologie humaine. 🌌")

    if not remarques: remarques.append("Profil d'une honnêteté presque déconcertante. 🧐")
    
    verdict = "Fiction 🏆" if score < 60 else "Suspect 🤨" if score < 90 else "Sincère ✨"
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
    def force_int(val):
        try: return int(float(str(val).strip()))
        except: return 0

    data = {
        "nom": request.form.get("nom", "Explorateur"),
        "age": force_int(request.form.get("age")),
        "pays": request.form.get("pays", "Terre"),
        "etudiant": request.form.get("etudiant", "non"),
        "niveau": request.form.get("niveau", "aucun"),
        "travail": request.form.get("travail", "non"),
        "revenu": force_int(request.form.get("revenu")),
        "fatigue": request.form.get("fatigue", "non"),
        "sommeil": force_int(request.form.get("sommeil"))
    }

    score, verdict, critiques = auditer_coherence(data)
    res_fatigue = predire_fatigue(data['age'], data['revenu'], data['etudiant'], data['travail'], score)

    # Sauvegarde SQL
    try:
        conn = get_db_connection()
        with conn:
            conn.execute("""INSERT INTO collectes 
                (nom, age, pays, etudiant, niveau, travail, revenu, fatigue_ressentie, sommeil, score_coherence, verdict, fatigue_ia) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (data['nom'], data['age'], data['pays'], data['etudiant'], data['niveau'], data['travail'], 
                 data['revenu'], data['fatigue'], data['sommeil'], score, verdict, res_fatigue))
    except Exception as e:
        print(f"Erreur DB : {e}")

    return render_template("result.html", nom=data['nom'], score=score, verdict=verdict, remarques=critiques, niveau_fatigue=res_fatigue)

@app.route('/historique')
def historique():
    try:
        if not os.path.exists(DB_PATH): return render_template('dashboard.html', logs=[], total=0, age_moyen=0)
        
        conn = get_db_connection()
        rows = conn.execute('SELECT * FROM collectes ORDER BY date_saisie DESC').fetchall()
        conn.close()
        
        total = len(rows)
        age_m = round(sum(r['age'] for r in rows)/total) if total > 0 else 0
        return render_template('dashboard.html', logs=rows, total=total, age_moyen=age_m)
    except:
        return "Erreur d'accès aux archives. Lancez un test d'abord ! 🚀"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)