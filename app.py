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
    """Initialise la base de données avec la structure correcte."""
    conn = get_db_connection()
    with conn:
        # On ne supprime la table que si on veut vraiment repartir de zéro
        # Pour cette fois, on s'assure qu'elle est propre
        conn.execute("DROP TABLE IF EXISTS collectes")
        conn.execute("""
        CREATE TABLE collectes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, age INTEGER, pays TEXT, etudiant TEXT, niveau TEXT, 
            travail TEXT, revenu INTEGER, fatigue_ressentie TEXT, sommeil INTEGER,
            score_coherence INTEGER, verdict TEXT, fatigue_ia TEXT, 
            date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.close()

def auditer_coherence(data):
    score = 100
    alertes = []
    if data['travail'] == "non" and data['revenu'] > 150000:
        score -= 40
        alertes.append("Revenus élevés sans emploi.")
    if data['age'] < 16 and data['niveau'] not in ["aucun", "primaire"]:
        score -= 50
        alertes.append("Âge incohérent avec le niveau.")
    verdict = "Fiction 🏆" if score < 60 else "Suspect 🤨" if score < 90 else "Sincère ✨"
    return max(0, score), verdict, alertes

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
    try:
        # SECURITÉ : Conversion propre des nombres pour éviter l'erreur "Vérifiez vos saisies"
        def clean_int(val):
            try:
                if not val: return 0
                return int(float(str(val).replace(',', '.')))
            except:
                return 0

        data = {
            "nom": request.form.get("nom", "Anonyme"),
            "age": clean_int(request.form.get("age")),
            "pays": request.form.get("pays", "Non précisé"),
            "etudiant": request.form.get("etudiant", "non"),
            "niveau": request.form.get("niveau", "aucun"),
            "travail": request.form.get("travail", "non"),
            "revenu": clean_int(request.form.get("revenu")),
            "fatigue": request.form.get("fatigue", "non"),
            "sommeil": clean_int(request.form.get("sommeil"))
        }

        score, verdict, critiques = auditer_coherence(data)
        res_fatigue = predire_fatigue(data['age'], data['revenu'], data['etudiant'], data['travail'], score)

        conn = get_db_connection()
        with conn:
            conn.execute("""INSERT INTO collectes 
                (nom, age, pays, etudiant, niveau, travail, revenu, fatigue_ressentie, sommeil, score_coherence, verdict, fatigue_ia) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (data['nom'], data['age'], data['pays'], data['etudiant'], data['niveau'], data['travail'], 
                 data['revenu'], data['fatigue'], data['sommeil'], score, verdict, res_fatigue))
        
        return render_template("result.html", nom=data['nom'], score=score, verdict=verdict, 
                               niveau_fatigue=res_fatigue, remarques=critiques, couleur="blue")
    except Exception as e:
        print(f"ERREUR : {e}")
        flash("Une erreur est survenue lors du traitement.")
        return redirect(url_for('home'))

@app.route('/historique')
def historique():
    try:
        conn = get_db_connection()
        rows = conn.execute('SELECT * FROM collectes ORDER BY date_saisie DESC').fetchall()
        conn.close()
        
        total = len(rows)
        if total > 0:
            age_m = round(sum(r['age'] for r in rows)/total)
            rev_m = round(sum(r['revenu'] for r in rows)/total)
            etud_p = round((sum(1 for r in rows if r['etudiant'] == 'oui')/total)*100)
        else:
            age_m, rev_m, etud_p = 0, 0, 0

        return render_template('dashboard.html', logs=rows, total=total, 
                               age_moyen=age_m, revenu_moyen=rev_m, pourcentage_etudiants=etud_p)
    except Exception as e:
        print(f"ERREUR ARCHIVES : {e}")
        return "Erreur lors de l'accès aux archives. Veuillez d'abord valider une expertise."

if __name__ == '__main__':
    init_db()
    app.run(debug=True)