from flask import Blueprint, render_template, redirect, url_for, flash, session
from app import db
from app.models import Persoon, Klusaanbieder, Kluszoeker, Categorie
from app.forms import PersoonForm, KlusaanbiederForm, KluszoekerForm, RegistrationForm, LoginForm, KlusForm
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

    # Haal de gebruiker op uit de database
    user = Persoon.query.get(session['user_id'])
    if not user:
        flash('Gebruiker niet gevonden', 'danger')
        return redirect(url_for('main.login'))

    # Haal de geaccepteerde en aangeboden klussen op
    geaccepteerde_klussen = Klus.query.filter_by(idnummer=user.idnummer, status='geaccepteerd').all()
    aangeboden_klussen = Klus.query.filter_by(idnummer=user.idnummer).all()

    return render_template('dashboard.html', user=user, geaccepteerde_klussen=geaccepteerde_klussen, aangeboden_klussen=aangeboden_klussen)


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
    session.pop('username', None)  # Verwijder de username uit de sessie
    flash('Je bent uitgelogd.', 'info')
    return redirect(url_for('main.klussen'))


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
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze actie uit te voeren', 'danger')
        return redirect(url_for('main.login'))
    
    # Haal de ingelogde persoon op
    persoon = Persoon.query.get(session['user_id'])
    
    if not persoon:
        flash('Persoon niet gevonden', 'danger')
        return redirect(url_for('main.dashboard'))

    # Het formulier wordt aangemaakt
    form = KlusaanbiederForm()
    
    if form.validate_on_submit():
        try:
            # Maak een nieuwe Klus aan
            nieuwe_klus = Klus(
                naam=form.naam.data,
                locatie=form.locatie.data,
                tijd=form.tijd.data,
                beschrijving=form.beschrijving.data,
                vergoeding=form.vergoeding.data,
                categorie=form.categorie.data,
                datum=form.datum.data,
                verwachte_duur=form.verwachte_duur.data,
                idnummer=persoon.idnummer
            )
            db.session.add(nieuwe_klus)
            db.session.commit()

            flash('Klus succesvol toegevoegd!', 'success')
            return redirect(url_for('main.klussen'))  # Redirect naar de klussenoverzicht
        except Exception as e:
            db.session.rollback()
            flash(f'Er is een fout opgetreden bij het opslaan: {e}', 'danger')
            return redirect(url_for('main.add_klusaanbieder'))
    else:
        if form.errors:
            flash(f'Formulierfout: {form.errors}', 'danger')

    # Toon het formulier
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
        return redirect(url_for('main.klussen'))
    
    # Print de status van de klus om te controleren of het daadwerkelijk 'beschikbaar' is
    print(f"Status van de klus: {klus.status}")  # Voeg deze regel toe om de status te controleren

    return render_template('klus_detail.html', klus=klus)


@main.route('/klussen')
def klussen():
    # Haal alle beschikbare klussen op (die niet geaccepteerd zijn)
    klussen = Klus.query.filter_by(status='beschikbaar').all()

    return render_template('klussen_overzicht.html', klussen=klussen)


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

@main.route('/klus/<klusnummer>/bekijken', methods=['GET'])
@login_required
def bekijk_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if klus:
        return render_template('klus_bekeken.html', klus=klus)
    else:
        flash('Deze klus bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))



@main.route('/klus/<klusnummer>/accepteren', methods=['POST'])
def accepteer_klus(klusnummer):
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze klus te accepteren.', 'danger')
        return redirect(url_for('main.klussen'))  # Terug naar het overzicht van klussen

    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if klus and klus.status == 'beschikbaar':  # Controleer of de klus beschikbaar is
        # Verander de status naar 'geaccepteerd'
        klus.status = 'geaccepteerd'
        klus.geaccepteerd_door = session['user_id']  # Optioneel: voeg toe wie de klus accepteerde
        db.session.commit()

        flash('Je hebt de klus geaccepteerd!', 'success')
        return redirect(url_for('main.geaccepteerde_klussen'))  # Redirect naar geaccepteerde klussen
    else:
        flash('Deze klus is al geaccepteerd of bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))  # Terug naar het overzicht



@main.route('/klus/<klusnummer>/geaccepteerd')
def klus_geaccepteerd(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    
    if klus:
        return render_template('klus_geaccepteerd.html', klus=klus)
    else:
        flash('Deze klus bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))  # Terug naar de overzichtspagina als de klus niet gevonden wordt

@main.route('/geaccepteerde_klussen')
def geaccepteerde_klussen():
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))
    
    user = Persoon.query.get(session['user_id'])
    klussen = Klus.query.filter_by(idnummer=user.idnummer, status='geaccepteerd').all()
    return render_template('geaccepteerde_klussen.html', klussen=klussen)

@main.route('/aangeboden_klussen')
def aangeboden_klussen():
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))
    
    user = Persoon.query.get(session['user_id'])
    klussen = Klus.query.filter_by(idnummer=user.idnummer).all()
    return render_template('klussen_overzicht.html', klussen=klussen)


@main.route('/klus/<klusnummer>/bevestigen', methods=['GET'])
def bevestig_klus_accepteren(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if klus and klus.status == 'beschikbaar':
        return render_template('klus_bevestigen.html', klus=klus)
    else:
        flash('Deze klus kan niet worden geaccepteerd.', 'danger')
        return redirect(url_for('main.klussen'))

