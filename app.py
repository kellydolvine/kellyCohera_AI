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
    conn = get_db_connection()
    with conn:
        # Ajout des nouvelles colonnes pour correspondre au JSON
        conn.execute("""
        CREATE TABLE IF NOT EXISTS collectes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, age INTEGER, pays TEXT, etudiant TEXT, niveau TEXT, 
            travail TEXT, revenu INTEGER, fatigue_ressentie TEXT, sommeil INTEGER,
            score_coherence INTEGER, verdict TEXT, fatigue_ia TEXT, 
            date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

def auditer_coherence(data):
    score = 100
    alertes = []
    # Logique de détection de mensonges
    if data['etudiant'] == "non" and data['niveau'] in ["licence", "master", "doctorat"]:
        score -= 30
        alertes.append("Diplômé mais pas étudiant ? Cohérence moyenne.")
    if data['travail'] == "non" and data['revenu'] > 200000:
        score -= 50
        alertes.append("Gros revenus sans travail ? Très suspect ! 💸")
    if data['age'] < 18 and data['niveau'] in ["master", "doctorat"]:
        score -= 60
        alertes.append("Un Master à moins de 18 ans ? Impressionnant mais louche.")
        
    verdict = "Fiction 🏆" if score < 50 else "Suspect 🤨" if score < 90 else "Sincère ✨"
    return max(0, score), verdict, alertes

@app.route('/')
def home():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except Exception as e:
        print(f"Erreur lecture JSON: {e}")
        questions = []
    return render_template("index.html", questions=questions)

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        # Récupération de TOUTES les données du nouveau JSON
        data = {
            "nom": request.form.get("nom", "Inconnu"),
            "age": int(request.form.get("age") or 0),
            "pays": request.form.get("pays", "Inconnu"),
            "etudiant": request.form.get("etudiant", "non"),
            "niveau": request.form.get("niveau", "aucun"),
            "travail": request.form.get("travail", "non"),
            "revenu": int(request.form.get("revenu") or 0),
            "fatigue_ressentie": request.form.get("fatigue", "non"),
            "sommeil": int(request.form.get("sommeil") or 0)
        }

        score, verdict, critiques = auditer_coherence(data)
        # Appel à ton modèle dans utils/ai_model.py
        fatigue_ia = predire_fatigue(data['age'], data['revenu'], data['etudiant'], data['travail'], score)

        # Sauvegarde en base de données
        conn = get_db_connection()
        with conn:
            conn.execute("""INSERT INTO collectes 
                (nom, age, pays, etudiant, niveau, travail, revenu, fatigue_ressentie, sommeil, score_coherence, verdict, fatigue_ia) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (data['nom'], data['age'], data['pays'], data['etudiant'], data['niveau'], data['travail'], 
                 data['revenu'], data['fatigue_ressentie'], data['sommeil'], score, verdict, fatigue_ia))
        
        return render_template("result.html", 
                               nom=data['nom'], score=score, verdict=verdict, 
                               critiques=critiques, fatigue=fatigue_ia, niveau_fatigue=fatigue_ia,
                               couleur="pink" if score < 70 else "blue",
                               blague="L'IA ne dort jamais, contrairement à vous !")
    except Exception as e:
        print(f"Erreur: {e}")
        flash("Vérifiez vos saisies ! 💢")
        return redirect(url_for('home'))

@app.route('/historique')
def historique():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM collectes ORDER BY date_saisie DESC').fetchall()
    conn.close()
    
    total = len(rows)
    # Calculs pour le dashboard
    age_m = round(sum(r['age'] for r in rows)/total) if total > 0 else 0
    rev_m = round(sum(r['revenu'] for r in rows)/total) if total > 0 else 0
    etud_p = round((sum(1 for r in rows if r['etudiant'] == 'oui')/total)*100) if total > 0 else 0

    return render_template('dashboard.html', logs=rows, total=total, 
                           age_moyen=age_m, revenu_moyen=rev_m, pourcentage_etudiants=etud_p)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)