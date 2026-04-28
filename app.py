from flask import Flask, render_template, request, url_for
from utils.ai_model import predire_fatigue
import sqlite3, os

app = Flask(__name__)

# Chemin ABSOLU pour Render (pour ne plus perdre les archives)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialisation de la base (une seule fois)
if not os.path.exists(DB_PATH):
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS collectes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, age INTEGER, 
        score_coherence INTEGER, verdict TEXT, fatigue_ia TEXT, 
        date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def auditer_coherence(data):
    score = 100
    remarques = []
    if data['age'] <= 0 or data['age'] > 110:
        score -= 40
        remarques.append(f"Âge de {data['age']} ans ? L'immortalité n'est pas encore gérée. 🛸")
    if data['travail'] == "non" and data['revenu'] > 100000:
        score -= 30
        remarques.append("Un revenu de ministre sans emploi ? On a trouvé le compte caché ! 💸")
    if data['sommeil'] < 3 or data['sommeil'] > 18:
        score -= 25
        remarques.append("Ton cycle de sommeil défi les lois de la biologie. 🌌")
    if not remarques: remarques.append("Profil d'une honnêteté déconcertante. 🧐")
    verdict = "Fiction 🏆" if score < 60 else "Suspect 🤨" if score < 90 else "Sincère ✨"
    return score, verdict, remarques

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        # Récupération des données du formulaire
        nom = request.form.get("nom", "Anonyme")
        age = int(request.form.get("age", 0))
        revenu = int(request.form.get("revenu", 0))
        sommeil = int(request.form.get("sommeil", 0))
        etudiant = request.form.get("etudiant", "non")
        fatigue_client = request.form.get("fatigue", "non")

        # Calculs
        data_audit = {"age": age, "travail": "non" if etudiant=="oui" else "oui", "revenu": revenu, "sommeil": sommeil}
        score, verdict, remarques = auditer_coherence(data_audit)
        res_fatigue = predire_fatigue(age, revenu, etudiant, data_audit["travail"], score)

        # SAUVEGARDE EN BASE (C'est ici que ça se jouait pour les archives !)
        conn = get_db_connection()
        conn.execute("INSERT INTO collectes (nom, age, score_coherence, verdict, fatigue_ia) VALUES (?,?,?,?,?)",
                     (nom, age, score, verdict, res_fatigue))
        conn.commit()
        conn.close()

        # On renvoie vers TON result.html (que je ne touche pas)
        return render_template("result.html", nom=nom, score=score, verdict=verdict, remarques=remarques, niveau_fatigue=res_fatigue)
    except Exception as e:
        return f"Oups ! Une petite erreur : {e}"

@app.route('/historique')
def historique():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM collectes ORDER BY date_saisie DESC').fetchall()
    conn.close()
    return render_template('dashboard.html', logs=logs, total=len(logs))

if __name__ == '__main__':
    app.run(debug=True)