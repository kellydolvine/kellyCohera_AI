from flask import Flask, render_template, request, redirect, url_for, flash
from utils.ai_model import predire_fatigue
import json, sqlite3, random, os

app = Flask(__name__)
app.secret_key = "K3lly_C0h3r4_4I_U1tr4_S3cur3_2026!#" 
DB_PATH = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

# --- LOGIQUE D'AUDIT ---
def auditer_coherence(data):
    score = 100
    alertes = []
    
    if data['etudiant'] == "non" and data['niveau'] != "aucun":
        score -= 40
        alertes.append(f"Niveau {data['niveau']} sans être étudiant ? La logique a quitté le chat. 😂")

    if data['travail'] == "non" and data['revenu'] > 100000:
        score -= 50
        alertes.append(f"{data['revenu']} FCFA sans bosser ? Tu as trouvé un code de triche dans la vraie vie ? 💸🤣")

    if data['niveau'] == "master" and data['age'] < 20:
        score -= 60
        alertes.append(f"Un Master à {data['age']} ans ? Même Einstein est jaloux de ton mensonge. 🤡")

    if data['travail'] == "oui" and data['age'] < 14:
        score -= 80
        alertes.append("Travailler avant 14 ans... C'est non. KellyCohera ne valide pas ! 🚔💀")

    # Verdicts et Punchlines
    if score == 100:
        v, c = "Profil Nickel ✨", "#2ecc71"
        note = f"Wow {data['nom']} ! Quelqu'un d'honnête, ça fait du bien au moral. 🌸😇"
    elif score >= 60:
        v, c = "Profil Louche 🤨", "#f1c40f"
        note = f"On sent l'effort de mytho, {data['nom']}, mais je vois clair dans ton jeu ! 😂🤏"
    else:
        v, c = "Fiction Totale 🏆🔥", "#e74c3c"
        insultes = [
            f"Franchement {data['nom']}, ton intelligence est en option aujourd'hui ? 💀🤣",
            f"Même un enfant de 5 ans mentirait mieux que ça. Gênant... 🤦‍♂️🤡",
            f"Félicitations ! Record du monde du n'importe quoi battu. 🎖️😭"
        ]
        note = random.choice(insultes)

    return max(0, score), v, c, note, alertes

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        data = {
            "nom": request.form.get("nom", "Inconnu").strip()[:25],
            "age": int(request.form.get("age") or 0),
            "revenu": int(request.form.get("revenu") or 0),
            "etudiant": request.form.get("etudiant", "non").lower(),
            "travail": request.form.get("travail", "non").lower(),
            "niveau": request.form.get("niveau", "aucun").lower()
        }
    except ValueError:
        flash("Mets des chiffres là où il faut, ne m'énerve pas ! 🙄💢")
        return redirect(url_for('home'))

    score, verdict, couleur, note, critiques = auditer_coherence(data)
    fatigue = predire_fatigue(data['age'], data['revenu'], data['etudiant'], data['travail'], score)

    conn = get_db_connection()
    with conn:
        conn.execute("INSERT INTO collectes (nom, age, etudiant, niveau, travail, revenu, score_coherence, verdict, fatigue_ia) VALUES (?,?,?,?,?,?,?,?,?)",
                     (data['nom'], data['age'], data['etudiant'], data['niveau'], data['travail'], data['revenu'], score, verdict, fatigue))

    blagues = ["☀️ Belle journée !", "🌸 KellyCohera t'observe...", "✨ Reste authentique !"]
    
    return render_template("result.html", nom=data['nom'], score=score, fatigue=fatigue, 
                           verdict=verdict, critiques=critiques, couleur=couleur, 
                           note_expert=note, blague=random.choice(blagues))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)