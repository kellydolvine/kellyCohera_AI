from flask import Flask, render_template, request
from utils.ai_model import predire_fatigue
import sqlite3, os

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if not os.path.exists(DB_PATH):
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS collectes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, age INTEGER, 
        score_coherence INTEGER, verdict TEXT, fatigue_ia TEXT, 
        date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        nom = request.form.get("nom")
        age = int(request.form.get("age"))
        revenu = int(request.form.get("revenu"))
        sommeil = int(request.form.get("sommeil"))
        etudiant = request.form.get("etudiant")

        score = 100
        if age < 18 and revenu > 2000: score -= 30
        if sommeil < 4: score -= 20
        
        verdict = "Sincère" if score > 70 else "Suspect"
        res_fatigue = predire_fatigue(age, revenu, etudiant, "oui", score)

        conn = get_db_connection()
        conn.execute("INSERT INTO collectes (nom, age, score_coherence, verdict, fatigue_ia) VALUES (?,?,?,?,?)",
                     (nom, age, score, verdict, res_fatigue))
        conn.commit()
        conn.close()

        return render_template("result.html", nom=nom, score=score, verdict=verdict, niveau_fatigue=res_fatigue)
    except:
        return "Erreur lors de la saisie des données."

@app.route('/historique')
def historique():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM collectes ORDER BY date_saisie DESC').fetchall()
    conn.close()
    return render_template('dashboard.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)