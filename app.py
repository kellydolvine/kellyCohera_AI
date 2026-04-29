import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "cle_secrete_kelly_cohera"

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            age INTEGER,
            revenu REAL,
            sommeil INTEGER,
            etudiant TEXT,
            score_coherence INTEGER,
            verdict TEXT,
            fatigue_ia TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialisation de la BDD au démarrage
init_db()

# --- LOGIQUE DE L'IA (CALCUL) ---
def analyser_profil(age, revenu, sommeil, etudiant):
    # Un petit calcul imaginaire pour la cohérence
    score = 100
    
    # Exemples de règles de cohérence :
    if etudiant == "oui" and revenu > 3000:
        score -= 30  # Rare d'être étudiant avec un très haut revenu
    if sommeil < 4:
        score -= 20  # Sommeil très bas impacte la cohérence
    if age < 18 and revenu > 1000:
        score -= 25  # Cohérence faible pour mineur avec gros revenus
        
    # Sécurité pour ne pas descendre sous 0
    score = max(0, score)
    
    # Détermination du verdict
    if score > 80:
        verdict = "Profil très cohérent"
        fatigue = "L'IA est impressionnée"
    elif score > 50:
        verdict = "Profil plausible"
        fatigue = "L'IA analyse encore"
    else:
        verdict = "Incohérences détectées"
        fatigue = "L'IA a besoin de repos"
        
    return score, verdict, fatigue

# --- ROUTES FLASK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyse', methods=['POST'])
def analyse():
    try:
        # Récupération des données du formulaire
        nom = request.form.get('nom')
        age = int(request.form.get('age'))
        revenu = float(request.form.get('revenu'))
        sommeil = int(request.form.get('sommeil'))
        etudiant = request.form.get('etudiant')

        # Analyse par l'IA
        score, verdict, fatigue = analyser_profil(age, revenu, sommeil, etudiant)

        # Enregistrement dans la base de données
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (nom, age, revenu, sommeil, etudiant, score_coherence, verdict, fatigue_ia)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nom, age, revenu, sommeil, etudiant, score, verdict, fatigue))
        conn.commit()
        conn.close()

        flash(f"Analyse terminée pour {nom} !")
        return redirect(url_for('historique'))
    
    except Exception as e:
        flash(f"Erreur lors de l'analyse : {str(e)}")
        return redirect(url_for('index'))

@app.route('/historique')
def historique():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY id DESC')
    logs = cursor.fetchall()
    conn.close()
    return render_template('historique.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True)