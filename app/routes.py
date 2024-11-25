from flask import Blueprint, render_template, redirect, url_for, flash, session
from app import db
from app.models import Persoon, Klusaanbieder, Kluszoeker, Categorie
from app.forms import PersoonForm, KlusaanbiederForm, KluszoekerForm, RegistrationForm, LoginForm
import uuid
from app.models import Klus  # Voeg deze regel toe om de Klus-klasse te importeren
from flask_login import current_user, login_required

# Maak een blueprint
main = Blueprint('main', __name__)

# Functie om een 10-cijferig ID-nummer te genereren
def generate_id_number():
    return str(uuid.uuid4().int)[:10]  # Genereer een unieke UUID (beperk tot 10 cijfers)

# Route voor de startpagina
@main.route('/')
def home():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    # Debugging: Controleer of het formulier is ingediend
    if form.validate_on_submit():
        print("Formulier is ingediend en geldig!")
        print(f"Gebruikersnaam: {form.username.data}")
        print(f"E-mail: {form.email.data}")
        print(f"Leeftijd: {form.leeftijd.data}")
        
        # Controleer of de gebruikersnaam al bestaat
        if Persoon.query.filter_by(username=form.username.data).first():
            print(f"De gebruikersnaam {form.username.data} is al in gebruik.")
            flash('Deze gebruikersnaam is al in gebruik. Kies een andere.', 'danger')
            return redirect(url_for('main.register'))
        
        # Controleer of het e-mailadres al bestaat
        if Persoon.query.filter_by(email=form.email.data).first():
            print(f"Het e-mailadres {form.email.data} is al in gebruik.")
            flash('Dit e-mailadres is al in gebruik. Kies een ander e-mailadres.', 'danger')
            return redirect(url_for('main.register'))

        # Maak een nieuw Persoon object aan
        new_person = Persoon(
            voornaam=form.voornaam.data,
            achternaam=form.achternaam.data,
            leeftijd=form.leeftijd.data,
            geslacht=form.gender.data,
            telefoonnummer=form.telefoonnummer.data,
            email=form.email.data,
            adres=form.adres.data,
            username=form.username.data,
            idnummer=generate_id_number()  # Dynamische ID
        )
        
        # Voeg de nieuwe persoon toe aan de database
        print("Nieuwe persoon wordt toegevoegd aan de database...")
        db.session.add(new_person)
        db.session.commit()
        
        # Bevestigingsbericht
        flash('Je bent succesvol geregistreerd!', 'success')
        
        # Debugging: Bekijk de redirect
        print("Redirecten naar de loginpagina...")
        
        # Directe redirect naar de loginpagina
        return redirect(url_for('main.login'))

    # Als het formulier niet is ingediend of niet geldig is, toon het registratieformulier
    print("Formulier niet geldig of nog niet ingediend.")
    return render_template('register.html', form=form)


from flask import session

@main.route('/login', methods=['GET', 'POST'])
def login():
    print("Login route is reached")  # Dit moet in je terminal verschijnen
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        user = Persoon.query.filter_by(username=username).first()
        
        if user:
            session['user_id'] = user.idnummer  # Sla het 'idnummer' op in de sessie
            flash(f'Ingelogd als {user.username}', 'success')
            return redirect(url_for('main.dashboard'))  # Redirect naar het dashboard of de oorspronkelijke pagina
        else:
            flash('Username niet gevonden', 'danger')
    
    return render_template('login.html', form=form)


# Controleer of de gebruiker is ingelogd in een andere route
@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Je moet eerst inloggen', 'danger')
        return redirect(url_for('main.login'))
    
    # Gebruik 'idnummer' om de gebruiker op te halen uit de sessie
    user = Persoon.query.get(session['user_id'])  # Haal gebruiker op met 'idnummer'
    
    return render_template('dashboard.html', user=user)

# Route voor het profiel (weergeven van gebruikersgegevens)
@main.route('/profile')
def profile():
    if 'user' not in session:
        flash('Je moet eerst inloggen om je profiel te bekijken.', 'warning')
        return redirect(url_for('main.login'))
    
    username = session['user']
    person = Persoon.query.filter_by(username=username).first()  # Verander Username naar username

    if person:
        return render_template('profile.html', person=person)
    else:
        flash('Profiel niet gevonden.', 'danger')
        return redirect(url_for('main.home'))

# Route voor afmelden (logout)
@main.route('/logout')
def logout():
    session.pop('user_id', None)  # Verwijder de user_id uit de sessie
    flash('Uitgelogd', 'success')
    return redirect(url_for('main.login'))


# Route voor het toevoegen van een persoon (voorbeeld)
@main.route('/add_person', methods=['GET', 'POST'])
def add_person():
    form = PersoonForm()
    if form.validate_on_submit():
        new_person = Persoon(
            voornaam=form.voornaam.data,
            achternaam=form.achternaam.data,
            leeftijd=form.leeftijd.data,
            adres=form.adres.data,
            email=form.email.data,
            telefoonnummer=form.tel_nr.data,
            voorkeur_categorie=form.voorkeur_categorie.data
        )
        db.session.add(new_person)
        db.session.commit()
        flash(f'Persoon {new_person.voornaam} {new_person.achternaam} is toegevoegd!', 'success')
        return redirect(url_for('main.profile'))
    return render_template('add_person.html', form=form)

@main.route('/add_klusaanbieder', methods=['GET', 'POST'])
def add_klusaanbieder():
    # Controleer of de gebruiker ingelogd is via 'user_id'
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze actie uit te voeren', 'danger')
        return redirect(url_for('main.login'))
    
    # Haal de persoon op op basis van 'user_id' uit de sessie
    persoon = Persoon.query.get(session['user_id'])
    
    # Als de persoon niet wordt gevonden, redirect naar dashboard
    if not persoon:
        flash('Persoon niet gevonden', 'danger')
        return redirect(url_for('main.dashboard'))

    # Maak het formulier voor klusaanbieder aan
    form = KlusaanbiederForm()
    if form.validate_on_submit():
        # Als er geen categorie is geselecteerd, stel dan de waarde in op NULL of een defaultwaarde
        categorie = form.categorie.data if form.categorie.data else None

        # Maak een nieuwe klus aan
        nieuwe_klus = Klus(
            locatie=form.locatie.data,
            tijd=form.tijd.data,
            beschrijving=form.beschrijving.data,
            vergoeding=form.vergoeding.data,
            categorie=categorie,  # Als geen categorie is geselecteerd, zal deze None zijn
            idnummer=persoon.idnummer  # De idnummer van de ingelogde gebruiker
        )

        # Voeg de nieuwe klus toe aan de sessie en commit
        db.session.add(nieuwe_klus)
        db.session.commit()

        # Toon een succesbericht en redirect naar de klus detailpagina
        flash('Klus succesvol toegevoegd!', 'success')
        return redirect(url_for('main.klus_detail', klusnummer=nieuwe_klus.klusnummer))
    
    return render_template('add_klusaanbieder.html', form=form)



# Route voor het toevoegen van een kluszoeker
@main.route('/add_kluszoeker', methods=['GET', 'POST'])
def add_kluszoeker():
    form = KluszoekerForm()
    if form.validate_on_submit():
        new_kluszoeker = Kluszoeker(
            idnummer=form.idnummer.data,  # Zorg ervoor dat idnummer correct is ingesteld
            rating=form.rating.data,
            aantal_klussen=form.aantal_klussen.data,
            categorie=form.categorie.data
        )
        db.session.add(new_kluszoeker)
        db.session.commit()
        flash(f'Kluszoeker {new_kluszoeker.idnummer} is toegevoegd!', 'success')
        return redirect(url_for('main.profile', username=new_kluszoeker.idnummer))
    
    flash('Er is iets mis met het formulier. Controleer je gegevens.', 'danger')
    return render_template('add_kluszoeker.html', form=form)

@main.route('/choose_role')
def choose_role():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Zorg ervoor dat de gebruiker is ingelogd
    
    # Verkrijg de gebruiker via het idnummer in de sessie
    user = Persoon.query.get(session['user_id'])  # Gebruik get met idnummer
    if not user:
        flash('Geen gebruiker gevonden.', 'danger')
        return redirect(url_for('login'))

    # Voeg hier de logica toe voor het kiezen van een rol, bijvoorbeeld een formulier
    return render_template('choose_role.html', user=user)


# Route om de details van een klus te tonen
@main.route('/klus/<klusnummer>')
def klus_detail(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if klus is None:
        flash('Klus niet gevonden', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('klus_detail.html', klus=klus)

@main.route('/klussen') #haalt alle klussen op en toont deze
def klussen():
    alle_klussen = Klus.query.all()
    return render_template('klussen_overzicht.html', klussen=alle_klussen)


@main.route('/meld_aan_voor_klus/<klusnummer>', methods=['POST'])
def meld_aan_voor_klus(klusnummer):
    if 'username' not in session:
        flash('Je moet ingelogd zijn om je voor een klus aan te melden', 'danger')
        return redirect(url_for('main.login'))
    
    persoon = Persoon.query.filter_by(username=session['username']).first()
    if persoon is None:
        flash('Persoon niet gevonden', 'danger')
        return redirect(url_for('main.dashboard'))
    
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if klus is None:
        flash('Deze klus bestaat niet', 'danger')
        return redirect(url_for('main.klussen'))

    # Voeg de persoon toe aan de lijst van geïnteresseerden voor deze klus
    if persoon not in klus.klussen_zoekers:
        klus.klussen_zoekers.append(persoon)
        db.session.commit()
        flash('Je hebt je succesvol aangemeld voor deze klus!', 'success')
    else:
        flash('Je hebt je al voor deze klus aangemeld', 'warning')

    return redirect(url_for('main.klussen'))



from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from . import db
from .models import Klus

@main.route('/klus/<klusnummer>/bekijken', methods=['GET', 'POST'])
@login_required
def bekijk_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    
    if klus:
        # Verander de status van de klus naar 'bekeken'
        klus.status = 'bekeken'
        db.session.commit()
        
        return render_template('klus_bekeken.html', klus=klus)
    else:
        return redirect(url_for('index'))  # Of een andere foutpagina

@main.route('/klus/<klusnummer>/accepteren', methods=['POST'])
@login_required
def accepteer_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    
    if klus and klus.status == 'bekeken':  # Controleer of de klus bekeken is
        # Verander de status naar 'geaccepteerd'
        klus.status = 'geaccepteerd'
        db.session.commit()
        
        return render_template('klus_geaccepteerd.html', klus=klus)
    else:
        return redirect(url_for('index'))  # Of een andere foutpagina
