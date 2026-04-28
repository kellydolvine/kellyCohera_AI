from flask import Flask, render_template, request, url_for
from utils.ai_model import predire_fatigue
import sqlite3, os

app = Flask(__name__)

# Sécurité pour Render : Chemin absolu vers la base de données
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Création de la table si elle n'existe pas (avec toutes les colonnes)
if not os.path.exists(DB_PATH):
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS collectes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, age INTEGER, 
        score_coherence INTEGER, verdict TEXT, fatigue_ia TEXT, 
        date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def auditer_coherence(data):
    """L'intelligence taquine de KellyCohera"""
    score = 100
    remarques = []
    
    if data['age'] <= 0 or data['age'] > 110:
        score -= 40
        remarques.append(f"Âge de {data['age']} ans ? L'immortalité n'est pas encore gérée par nos serveurs. 🛸")
    
    if data['etudiant'] == "non" and data['revenu'] > 100000:
        score -= 30
        remarques.append("Un revenu de ministre sans emploi ? On a trouvé le compte caché ! 💸")
    
    if data['sommeil'] < 3 or data['sommeil'] > 18:
        score -= 25
        remarques.append("Ton cycle de sommeil défie les lois de la biologie humaine. 🌌")

    if not remarques:
        remarques.append("Profil d'une honnêteté presque déconcertante. Bravo. 🧐")
    
    verdict = "Fiction 🏆" if score < 60 else "Suspect 🤨" if score < 90 else "Sincère ✨"
    return score, verdict, remarques

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        nom = request.form.get("nom", "Explorateur")
        age = int(request.form.get("age", 0))
        revenu = int(request.form.get("revenu", 0))
        sommeil = int(request.form.get("sommeil", 0))
        etudiant = request.form.get("etudiant", "non")

        # Calculs et blagues
        score, verdict, remarques = auditer_coherence({"age": age, "etudiant": etudiant, "revenu": revenu, "sommeil": sommeil})
        res_fatigue = predire_fatigue(age, revenu, etudiant, "oui", score)

        # Enregistrement en base pour l'archive
        conn = get_db_connection()
        conn.execute("INSERT INTO collectes (nom, age, score_coherence, verdict, fatigue_ia) VALUES (?,?,?,?,?)",
                     (nom, age, score, verdict, res_fatigue))
        conn.commit()
        conn.close()

        return render_template("result.html", nom=nom, score=score, verdict=verdict, remarques=remarques, niveau_fatigue=res_fatigue)
    except Exception as e:
        return f"Erreur système : {e}"

@app.route('/historique')
def historique():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM collectes ORDER BY date_saisie DESC').fetchall()
    conn.close()
    return render_template('dashboard.html', logs=logs, total=len(logs))

if __name__ == '__main__':
    app.run(debug=True)