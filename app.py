from flask import Flask, render_template, request, redirect, url_for, flash
from utils.ai_model import predire_fatigue
import sqlite3, random, os

app = Flask(__name__)
app.secret_key = "K3lly_C0h3r4_AI_2026_Secure" 
DB_PATH = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Cette fonction recrée la table si elle a été supprimée
def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS collectes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, age INTEGER, etudiant TEXT, niveau TEXT, 
            travail TEXT, revenu INTEGER, score_coherence INTEGER, 
            verdict TEXT, fatigue_ia TEXT, date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

def auditer_coherence(data):
    score = 100
    alertes = []
    if data['etudiant'] == "non" and data['niveau'] != "aucun":
        score -= 40
        alertes.append(f"Niveau {data['niveau']} sans être étudiant ? 😂")
    if data['travail'] == "non" and data['revenu'] > 100000:
        score -= 50
        alertes.append(f"Beaucoup d'argent sans travailler ? Louche ! 💸")
    
    verdict = "Fiction Totale 🏆" if score < 60 else "Profil Louche 🤨" if score < 100 else "Profil Nickel ✨"
    return max(0, score), verdict, alertes

@app.route('/')
def home():
    questions = [
        {"icon": "👤", "question": "Nom ?", "name": "nom", "type": "text", "placeholder": "Ton nom"},
        {"icon": "🎂", "question": "Âge ?", "name": "age", "type": "number", "placeholder": "Ex: 25"},
        {"icon": "🎓", "question": "Étudiant ?", "name": "etudiant", "type": "select", "options": ["oui", "non"]},
        {"icon": "📚", "question": "Diplôme ?", "name": "niveau", "type": "select", "options": ["aucun", "bac", "licence", "master", "doctorat"]},
        {"icon": "💼", "question": "Travail ?", "name": "travail", "type": "select", "options": ["oui", "non"]},
        {"icon": "💰", "question": "Revenu ?", "name": "revenu", "type": "number", "placeholder": "FCFA"}
    ]
    return render_template("index.html", questions=questions)

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        data = {
            "nom": request.form.get("nom", "Inconnu"),
            "age": int(request.form.get("age") or 0),
            "revenu": int(request.form.get("revenu") or 0),
            "etudiant": request.form.get("etudiant", "non"),
            "travail": request.form.get("travail", "non"),
            "niveau": request.form.get("niveau", "aucun")
        }
        score, verdict, critiques = auditer_coherence(data)
        fatigue = predire_fatigue(data['age'], data['revenu'], data['etudiant'], data['travail'], score)

        conn = get_db_connection()
        with conn:
            conn.execute("INSERT INTO collectes (nom, age, etudiant, niveau, travail, revenu, score_coherence, verdict, fatigue_ia) VALUES (?,?,?,?,?,?,?,?,?)",
                (data['nom'], data['age'], data['etudiant'], data['niveau'], data['travail'], data['revenu'], score, verdict, fatigue))
        
        return render_template("result.html", nom=data['nom'], score=score, fatigue=fatigue, verdict=verdict, critiques=critiques, couleur="pink", blague="KellyCohera a parlé !", niveau_fatigue=fatigue)
    except:
        flash("Erreur de saisie ! 💢")
        return redirect(url_for('home'))

@app.route('/historique')
def historique():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM collectes ORDER BY date_saisie DESC').fetchall()
    conn.close()
    
    total = len(rows)
    age_m = round(sum(r['age'] for r in rows)/total) if total > 0 else 0
    rev_m = round(sum(r['revenu'] for r in rows)/total) if total > 0 else 0
    etud_p = round((sum(1 for r in rows if r['etudiant'] == 'oui')/total)*100) if total > 0 else 0

    return render_template('dashboard.html', logs=rows, total=total, age_moyen=age_m, revenu_moyen=rev_m, pourcentage_etudiants=etud_p)

if __name__ == '__main__':
    if not os.path.exists(DB_PATH): init_db()
    app.run(debug=True)