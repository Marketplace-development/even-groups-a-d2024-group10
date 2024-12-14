from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort 
from app import db
from app.models import Persoon, Klusaanbieder, Kluszoeker, Categorie, Rating, klus_zoeker, Bericht
from app.forms import PersoonForm, KlusaanbiederForm, KluszoekerForm, RegistrationForm, LoginForm
from app.forms import RatingFormForZoeker, RatingFormForAanbieder, RatingForm
import uuid
from app.models import Klus  # Voeg deze regel toe om de Klus-klasse te importeren
from flask_login import login_required
from datetime import datetime
import requests

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


@main.route('/login', methods=['GET', 'POST'])
def login():
    print("Login route is reached")  # Debug om te zien of de route wordt aangeroepen
    form = LoginForm()

    # Controleer of het formulier wordt verzonden
    if form.validate_on_submit():  # Dit gebeurt alleen bij een POST-verzoek
        username = form.username.data
        user = Persoon.query.filter_by(username=username).first()

        if user:
            # Sla gebruiker op in de sessie en stuur door naar dashboard
            session['user_id'] = user.idnummer
            return redirect(url_for('main.dashboard'))
        else:
            # Flash alleen een foutmelding bij een foute gebruikersnaam
            flash('Ongeldige gebruikersnaam', 'danger')

    # Render het formulier (zonder flash-meldingen voor ingelogde gebruikers)
    return render_template('login.html', form=form)


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
    if 'user_id' not in session:
        flash('Je moet eerst inloggen om je profiel te bekijken.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    user = Persoon.query.get(user_id)

    if user:
        gemiddelde_score_aanbieder = user.gemiddelde_score_aanbieder()
        gemiddelde_score_zoeker = user.gemiddelde_score_zoeker()

        return render_template(
            'profile.html',
            user=user,
            gemiddelde_score_aanbieder=gemiddelde_score_aanbieder,
            gemiddelde_score_zoeker=gemiddelde_score_zoeker
        )
    else:
        flash('Profiel niet gevonden.', 'danger')   
        return redirect(url_for('main.home'))



@main.route('/logout')
def logout():
    session.clear()  # Wis de sessie om de gebruiker uit te loggen
    flash('Je bent succesvol uitgelogd.', 'success')
    return redirect(url_for('main.login'))  # Stuur de gebruiker naar de loginpagina


@main.route('/profiel_bewerken', methods=['GET', 'POST'])
def profiel_bewerken():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om je profiel te bewerken.', 'danger')
        return redirect(url_for('main.login'))

    user = Persoon.query.get(user_id)

    if request.method == 'POST':
        user.voornaam = request.form['voornaam']
        user.achternaam = request.form['achternaam']
        user.leeftijd = request.form['leeftijd']
        user.email = request.form['email']
        user.telefoonnummer = request.form['telefoonnummer']
        user.adres = request.form['adres']
        db.session.commit()
        flash('Profiel succesvol bijgewerkt!', 'success')
        return redirect(url_for('main.profile'))

    return render_template('profiel_bewerken.html', user=user)


@main.route('/profiel_verwijderen', methods=['POST'])
def profiel_verwijderen():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om je profiel te verwijderen.', 'danger')
        return redirect(url_for('main.login'))

    # Zoek de gebruiker op
    user = Persoon.query.filter_by(idnummer=user_id).first()

    if not user:
        flash('Profiel niet gevonden.', 'danger')
        return redirect(url_for('main.profile'))

    # Verwijder gekoppelde berichten van de gebruiker (berichten die de gebruiker heeft verstuurd)
    Bericht.query.filter_by(afzender_id=user_id).delete()
    Bericht.query.filter_by(ontvanger_id=user_id).delete()

    # Verwijder gekoppelde ratings
    Rating.query.filter_by(klusaanbieder_id=user_id).delete()
    Rating.query.filter_by(kluszoeker_id=user_id).delete()

    # Update gekoppelde categorie_statistiek records
    CategorieStatistiek.query.filter_by(idnummer=user_id).update({
        "idnummer": "0000000000"  # Of een andere standaardwaarde
    })

    # Update gekoppelde klus records
    Klus.query.filter_by(idnummer=user_id).update({
        "idnummer": "0000000000"  # Of een andere standaardwaarde
    })

    # Verwijder de gebruiker
    db.session.delete(user)
    db.session.commit()

    # Clear de sessie
    session.clear()  # Log de gebruiker uit
    flash('Je profiel en gekoppelde gegevens zijn succesvol verwijderd.', 'success')
    return redirect(url_for('main.home'))


# Helper functie voor het ophalen van suggesties
def get_suggestions(query, is_street=False):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query,
        'format': 'json',
        'addressdetails': 1,
        'limit': 5
    }
    if is_street:
        params['addressdetails'] = 1

    response = requests.get(url, params=params)
    data = response.json()

    suggestions = []
    for location in data:
        if is_street:
            suggestion = f"{location.get('address', {}).get('road', '')} {location.get('address', {}).get('house_number', '')}"
        else:
            suggestion = location.get('display_name', '')
        suggestions.append(suggestion)

    return suggestions

# Route voor het weergeven van suggesties en het verwerken van het formulier
@main.route('/add_klusaanbieder', methods=['GET', 'POST'])
def add_klusaanbieder():
    stad_suggesties = []
    adres_suggesties = []

    if request.method == 'POST':
        pass  # Hier kun je verdere formulierverwerking toevoegen

    stad_query = request.args.get('stad', '')
    if stad_query:
        stad_suggesties = get_suggestions(stad_query)

    adres_query = request.args.get('adres', '')
    if adres_query:
        adres_suggesties = get_suggestions(adres_query, is_street=True)

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
            # Haal de uur en minuut op uit het formulier
            tijd_uren = int(form.uren.data)  # Velden moeten bestaan in het formulier
            tijd_minuten = int(form.minuten.data)

            # Combineer het uur en de minuut in een tijd in het formaat 'HH:MM'
            tijd = f"{tijd_uren:02}:{tijd_minuten:02}"

            stad = form.stad.data
            adres = form.adres.data
            # Combineer stad en adres tot een locatie-string
            locatie = f"{stad}, {adres}"

            # Maak een nieuwe Klus aan
            nieuwe_klus = Klus(
                naam=form.naam.data,
                locatie=locatie,  # De gecombineerde locatie
                tijd=tijd,  # De gecombineerde tijd
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
            return redirect(url_for('main.mijn_aangeboden_klussen'))  # Redirect naar de klussenoverzicht
        except Exception as e:
            db.session.rollback()
            flash(f'Er is een fout opgetreden bij het opslaan: {e}', 'danger')
            return redirect(url_for('main.add_klusaanbieder'))
    else:
        if form.errors:
            flash(f'Formulierfout: {form.errors}', 'danger')

    # Toon het formulier
    return render_template('add_klusaanbieder.html', 
                           form=form, 
                           stad_suggesties=stad_suggesties, 
                           adres_suggesties=adres_suggesties)


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


from app.models import CategorieStatistiek, Klus, Persoon
@main.route('/klussen')
def klussen():
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om klussen te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    user_id = session['user_id']

    # Haal de categorieën op waar de gebruiker de meeste klussen in heeft geaccepteerd
    categorie_voorkeuren = (
        db.session.query(CategorieStatistiek.categorie)
        .filter_by(idnummer=user_id)
        .order_by(CategorieStatistiek.aantal_accepteerd.desc())
        .all()
    )

    # Zet de categorieën in een volgorde van meest naar minst voorkomend
    voorkeuren_volgorde = [voorkeur[0] for voorkeur in categorie_voorkeuren]

    # Haal alle beschikbare klussen op
    beschikbare_klussen = Klus.query.filter_by(status='beschikbaar').all()

    # Sorteer de klussen op basis van de voorkeursvolgorde
    def sorteer_klussen(klus):
        try:
            return voorkeuren_volgorde.index(klus.categorie)
        except ValueError:
            # Als de categorie niet in de voorkeursvolgorde zit, zet hem achteraan
            return len(voorkeuren_volgorde)

    gesorteerde_klussen = sorted(beschikbare_klussen, key=sorteer_klussen)

    return render_template('klussen_overzicht.html', klussen=gesorteerde_klussen)


@main.route('/klus/<klusnummer>/bekijken', methods=['GET'])
@login_required
def bekijk_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if klus:
        return render_template('klus_bekeken.html', klus=klus)
    else:
        flash('Deze klus bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))


@main.route('/klus/<klusnummer>/geaccepteerd')
def klus_geaccepteerd(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    
    if klus:
        return render_template('klus_geaccepteerd.html', klus=klus)
    else:
        flash('Deze klus bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))  # Terug naar de overzichtspagina als de klus niet gevonden wordt


@main.route('/aangeboden_klussen')
def aangeboden_klussen():
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))
    
    user = Persoon.query.get(session['user_id'])
    klussen = Klus.query.filter_by(idnummer=user.idnummer).all()
    return render_template('klussen_overzicht.html', klussen=klussen)


@main.route('/klus/<klusnummer>/bevestiging', methods=['GET'])
def bevestiging_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if klus:
        return render_template('bevestiging_klus.html', klus=klus)
    else:
        flash('Deze klus bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))


@main.route('/mijn_klussen')
def mijn_klussen():
    # Controleer of de gebruiker is ingelogd via de sessie
    if 'user_id' not in session:
        return redirect(url_for('main.login'))  # Als er geen user_id in de sessie is, doorverwijzen naar login

    user_id = session['user_id']
    user = Persoon.query.get(user_id)
    
    # Haal de klussen van de ingelogde gebruiker op
    klussen = Klus.query.filter(Klus.idnummer == user.idnummer, Klus.status == 'geaccepteerd').all()

    return render_template('mijn_klussen.html', klussen=klussen)


@main.route('/mijn_klussen_selectie', methods=['GET'])
def mijn_klussen_selectie():
    return render_template('mijn_klussen_selectie.html')


@main.route('/mijn_aangeboden_klussen', methods=['GET', 'POST'])
def mijn_aangeboden_klussen():
    user_id = session.get('user_id')  # Haal de ingelogde gebruiker op uit de sessie
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    # Query voor klussen aangeboden door de ingelogde gebruiker
    klussen = Klus.query.filter(Klus.idnummer == user_id).order_by(Klus.datum.desc()).all()

    # Verwerk de klussen voor de weergave
    klussen_info = []
    for klus in klussen:
        klussen_info.append({
            'id': klus.klusnummer,  # Gebruik 'klusnummer' als unieke ID
            'naam': klus.naam,
            'datum': klus.datum.strftime('%d-%m-%Y') if klus.datum else 'Onbekend',  # Controleer op None
            'status': klus.status,  # Gebruik de werkelijke status
        })
    print(klussen_info)

    # Als het formulier wordt verzonden (POST), update de voltooiingsstatus
    if request.method == 'POST':
        klus_id = request.form.get('klus_id')  # Haal de klus ID op uit het formulier
        klus = Klus.query.get_or_404(klus_id)
        if klus.idnummer != user_id:
            flash('Je kunt deze klus niet bijwerken.', 'danger')
            return redirect(url_for('main.mijn_aangeboden_klussen'))

        # Update de status naar 'voltooid' (of andere gewenste status)
        klus.status = 'voltooid'
        db.session.commit()
        flash('Klus is gemarkeerd als voltooid!', 'success')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    return render_template('mijn_aangeboden_klussen.html', klussen=klussen_info)


@main.route('/mijn_gezochte_klussen')
def mijn_gezochte_klussen():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    # Haal klussen op waar de gebruiker aan gekoppeld is als zoeker
    gezochte_klussen = Klus.query.filter(
        Klus.status == 'geaccepteerd',
        Klus.klussen_zoekers.any(Persoon.idnummer == user_id)
    ).order_by(Klus.created_at.desc()).all()

    # Debugging
    for klus in gezochte_klussen:
        print(f"Klus in template: {klus.naam}, Status: {klus.status}, Zoekers: {[zoeker.idnummer for zoeker in klus.klussen_zoekers]}")
    
    # Variabele naam consistent maken met de template
    return render_template('mijn_gezochte_klussen.html', klussen=gezochte_klussen)


@main.route('/leave_klus/<klusnummer>', methods=['POST'])
def leave_klus(klusnummer):
    # Zoek de ingelogde gebruiker via de sessie
    user_id = session.get('user_id')
    if not user_id:
        flash("Je bent niet ingelogd.", "danger")
        return redirect(url_for('main.login'))

    # Zoek de klus op basis van klusnummer
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash("Klus niet gevonden.", "danger")
        return redirect(url_for('main.mijn_gezochte_klussen'))

    # Zoek de kluszoeker die gekoppeld is aan de klus en ingelogde gebruiker
    kluszoeker = next((zoeker for zoeker in klus.klussen_zoekers if zoeker.idnummer == user_id), None)
    if not kluszoeker:
        flash("Je hebt deze klus niet geaccepteerd.", "danger")
        return redirect(url_for('main.mijn_gezochte_klussen'))

    # Verwijder de gebruiker van de klus en update de status
    klus.klussen_zoekers.remove(kluszoeker)
    klus.status = "beschikbaar"

    # Wijzigingen opslaan
    db.session.commit()

    flash("De klus is geannuleerd en opnieuw beschikbaar gemaakt.", "success")
    return redirect(url_for('main.mijn_gezochte_klussen'))


@main.route('/delete_klus/<uuid:klusnummer>', methods=['POST'])
def delete_klus(klusnummer):
    # Haal de klus op
    klus = Klus.query.filter_by(klusnummer=str(klusnummer)).first()

    if not klus:
        flash('Klus niet gevonden.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    # Controleer of de ingelogde gebruiker de aanbieder is
    user_id = session.get('user_id')
    if klus.idnummer != user_id:
        flash('Je hebt geen toestemming om deze klus te verwijderen.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    # Verwijder de klus
    db.session.delete(klus)
    db.session.commit()

    flash(f'De klus "{klus.naam}" is succesvol verwijderd.', 'success')
    return redirect(url_for('main.mijn_aangeboden_klussen'))


@main.route('/klus/<klusnummer>/accepteren', methods=['POST'])
def accepteer_klus(klusnummer):
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze klus te accepteren.', 'danger')
        return redirect(url_for('main.klussen'))  # Terug naar het overzicht van klussen

    # Zoek de klus op basis van klusnummer
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if klus and klus.status == 'beschikbaar':  # Controleer of de klus beschikbaar is
        # Verander de status naar 'geaccepteerd'
        klus.status = 'geaccepteerd'

        # Haal de gebruiker op die de klus accepteert
        user_id = session['user_id']
        gebruiker = Persoon.query.filter_by(idnummer=user_id).first()

        if not gebruiker:
            flash('Gebruiker niet gevonden.', 'danger')
            return redirect(url_for('main.klussen'))

        # Voeg de gebruiker toe aan de klus_zoeker relatie
        if gebruiker not in klus.klussen_zoekers:
            klus.klussen_zoekers.append(gebruiker)
            db.session.commit()

        # Werk de statistieken voor de categorie bij
        categorie_statistiek = CategorieStatistiek.query.filter_by(
            idnummer=user_id,
            categorie=klus.categorie
        ).first()

        if categorie_statistiek:
            # Als er al een statistiek bestaat, verhoog het aantal
            categorie_statistiek.aantal_accepteerd += 1
        else:
            # Anders maak een nieuwe record aan
            nieuwe_statistiek = CategorieStatistiek(
                idnummer=user_id,
                categorie=klus.categorie,
                aantal_accepteerd=1
            )
            db.session.add(nieuwe_statistiek)

        # Sla de wijzigingen op
        db.session.commit()
        print(f"Klusstatus na accepteren: {klus.status}")
        print(f"Zoekers gekoppeld aan klus: {[zoeker.idnummer for zoeker in klus.klussen_zoekers]}")


        flash('Je hebt de klus geaccepteerd!', 'success')
        return redirect(url_for('main.mijn_gezochte_klussen'))  # Redirect naar de juiste pagina
    else:
        flash('Deze klus is al geaccepteerd of bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))  # Terug naar het overzicht


@main.route('/mijn_geschiedenis')
def mijn_geschiedenis():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    # Aangeboden klussen
    aangeboden_klussen = Klus.query.filter(
        Klus.idnummer == user_id,
        Klus.status == 'voltooid',
        Klus.voltooid_op.isnot(None)
    ).order_by(Klus.voltooid_op.desc()).all()

    # Debugging
    for klus in aangeboden_klussen:
        print(f"Aangeboden klus: {klus.naam}, Beoordeeld door aanbieder: {klus.is_gewaardeerd_door_aanbieder()}, Beoordeeld door zoeker: {klus.is_gewaardeerd_door_zoeker()}")

    # Gezochte klussen
    gezochte_klussen = Klus.query.join(Klus.klussen_zoekers).filter(
        Persoon.idnummer == user_id,
        Klus.status == 'voltooid',
        Klus.voltooid_op.isnot(None)
    ).order_by(Klus.voltooid_op.desc()).all()

    # Debugging
    for klus in gezochte_klussen:
        print(f"Gezochte klus: {klus.naam}, Beoordeeld door aanbieder: {klus.is_gewaardeerd_door_aanbieder()}, Beoordeeld door zoeker: {klus.is_gewaardeerd_door_zoeker()}")

    return render_template(
        'mijn_geschiedenis.html',
        aangeboden_klussen=aangeboden_klussen,
        gezochte_klussen=gezochte_klussen
    )


@main.route('/klus/<klusnummer>/markeer_voltooid', methods=['POST'])
def markeer_klus_voltooid(klusnummer):
    # Haal de klus op
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if not klus:
        flash('Klus niet gevonden.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    # Haal de ingelogde gebruiker op
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze actie uit te voeren.', 'danger')
        return redirect(url_for('main.login'))

    # Controleer of de ingelogde gebruiker de aanbieder is
    if klus.idnummer != user_id:
        flash('Je hebt geen toestemming om deze klus te voltooien.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    # Markeer de klus als voltooid
    klus.status = 'voltooid'
    klus.voltooid_op = datetime.utcnow()
    db.session.commit()

    # Flash-bericht voor de aanbieder
    flash(f"De klus '{klus.naam}' is gemarkeerd als voltooid en toegevoegd aan je geschiedenis.", 'success')

    # Meldingen voor alle gekoppelde zoekers
    zoekers = klus.klussen_zoekers
    for zoeker in zoekers:
        flash(f"Klus '{klus.naam}' is toegevoegd aan de geschiedenis van zoeker {zoeker.voornaam} {zoeker.achternaam}.", 'info')

    return redirect(url_for('main.mijn_geschiedenis'))

    
@main.route('/rate_zoeker/<klusnummer>', methods=['GET', 'POST'])
def rate_zoeker(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash('Klus niet gevonden.', 'danger')
        return redirect(url_for('main.mijn_geschiedenis'))

    print(f"DEBUG: Klus {klusnummer}, Aanbieder: {klus.idnummer}, Zoekers: {[zoeker.idnummer for zoeker in klus.klussen_zoekers]}")

    # Controleer of er zoekers zijn voor de klus
    if not klus.klussen_zoekers:
        flash('Er zijn geen zoekers voor deze klus. Je kunt deze klus niet beoordelen.', 'warning')
        return redirect(url_for('main.mijn_geschiedenis'))

    # Controleer of er al een beoordeling is voor de kluszoeker
    existing_rating = Rating.query.filter_by(
        klusnummer=klusnummer,
        kluszoeker_id=klus.klussen_zoekers[0].idnummer,
        klusaanbieder_id=session.get('user_id')
    ).filter(Rating.vriendelijkheid_zoeker.isnot(None)).first()

    if existing_rating:
        flash('Je hebt deze kluszoeker al beoordeeld. Je kunt niet meerdere keren een beoordeling geven.', 'warning')
        return redirect(url_for('main.mijn_geschiedenis'))

    # Controleer of de huidige gebruiker de aanbieder is
    if session.get('user_id') != klus.idnummer:
        flash('Je bent niet de aanbieder van deze klus en kunt de kluszoeker dus niet beoordelen.', 'warning')
        return redirect(url_for('main.mijn_geschiedenis'))

    form = RatingFormForZoeker()
    # Voeg de beoordeling toe
    if form.validate_on_submit():
        new_rating = Rating(
            klusnummer=klusnummer,
            kluszoeker_id=klus.klussen_zoekers[0].idnummer,
            klusaanbieder_id=session.get('user_id'),
            vriendelijkheid_zoeker=form.vriendelijkheid.data,
            tijdigheid=form.tijdigheid.data,
            kwaliteit=form.kwaliteit.data,
            communicatie_zoeker=form.communicatie.data,
            algemene_ervaring_zoeker=form.algemene_ervaring.data,
            created_at=datetime.utcnow(),
        )
        db.session.add(new_rating)
        db.session.commit()
        print(f"DEBUG: Nieuwe beoordeling toegevoegd: {new_rating}")
        flash('Beoordeling voor de kluszoeker succesvol toegevoegd!', 'success')
        return redirect(url_for('main.mijn_geschiedenis'))

    return render_template('rate_zoeker.html', form=form, klus=klus)

@main.route('/rate_aanbieder/<klusnummer>', methods=['GET', 'POST'])
def rate_aanbieder(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash('Klus niet gevonden.', 'danger')
        return redirect(url_for('main.mijn_geschiedenis'))

    # Controleer of de gebruiker een van de kluszoekers is
    if not any(zoeker.idnummer == session.get('user_id') for zoeker in klus.klussen_zoekers):
        flash('Je bent niet bevoegd om deze beoordeling te maken.', 'danger')
        return redirect(url_for('main.mijn_geschiedenis'))

    # Controleer of er al een beoordeling is voor de klusaanbieder
    existing_rating = Rating.query.filter_by(
        klusnummer=klusnummer,
        kluszoeker_id=session.get('user_id'),
        klusaanbieder_id=klus.idnummer
    ).filter(Rating.vriendelijkheid_aanbieder.isnot(None)).first()

    if existing_rating:
        flash('Je hebt deze klusaanbieder al beoordeeld.', 'warning')
        return redirect(url_for('main.mijn_geschiedenis'))

    form = RatingFormForAanbieder()
    if form.validate_on_submit():
        new_rating = Rating(
            klusnummer=klusnummer,
            klusaanbieder_id=klus.idnummer,
            kluszoeker_id=session.get('user_id'),
            vriendelijkheid_aanbieder=form.vriendelijkheid.data,
            gastvrijheid=form.gastvrijheid.data,
            betrouwbaarheid=form.betrouwbaarheid.data,
            communicatie_aanbieder=form.communicatie.data,
            algemene_ervaring_aanbieder=form.algemene_ervaring.data,
            created_at=datetime.utcnow(),
        )
        db.session.add(new_rating)
        db.session.commit()
        flash('Beoordeling voor de klusaanbieder succesvol toegevoegd!', 'success')
        return redirect(url_for('main.mijn_geschiedenis'))

    return render_template('rate_aanbieder.html', form=form, klus=klus)


@main.route('/mijn_chats', methods=['GET'])
def mijn_chats():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    # Aangeboden klussen (waar de gebruiker de aanbieder is)
    aangeboden_klussen = Klus.query.filter(
        Klus.idnummer == user_id,
        Klus.status.in_(['geaccepteerd', 'voltooid']),
    ).order_by(Klus.voltooid_op.desc()).all()

    # Gezochte klussen (waar de gebruiker de zoeker is)
    gezochte_klussen = Klus.query.filter(
        Klus.klussen_zoekers.any(Persoon.idnummer == user_id),
        Klus.status.in_(['geaccepteerd', 'voltooid']),
    ).order_by(Klus.voltooid_op.desc()).all()

    # Combineer beide lijsten
    klussen_info = []

    for klus in aangeboden_klussen:
        berichten = Bericht.query.filter_by(klusnummer=klus.klusnummer).order_by(Bericht.verzonden_op.desc()).all()
        # Voeg de naam van de andere persoon toe (aanbieder of zoeker)
        ontvanger = None
        if klus.idnummer != user_id:  # Indien de gebruiker een aanbieder is, dan is de ontvanger de zoeker
            ontvanger = Persoon.query.filter_by(idnummer=klus.klussen_zoekers[0].idnummer).first()
        else:  # Indien de gebruiker een zoeker is, dan is de ontvanger de aanbieder
            ontvanger = Persoon.query.filter_by(idnummer=klus.idnummer).first()

        other_person_name = f"{ontvanger.voornaam} {ontvanger.achternaam}" if ontvanger else "Onbekend"
        
        klussen_info.append({
            'klusnummer': klus.klusnummer,
            'naam': klus.naam,
            'status': klus.status,
            'berichten': berichten,
            'type': 'aangeboden',
            'other_person_name': other_person_name
        })

    for klus in gezochte_klussen:
        berichten = Bericht.query.filter_by(klusnummer=klus.klusnummer).order_by(Bericht.verzonden_op.desc()).all()
        # Voeg de naam van de andere persoon toe (aanbieder of zoeker)
        ontvanger = None
        if klus.idnummer != user_id:  # Indien de gebruiker een aanbieder is, dan is de ontvanger de zoeker
            ontvanger = Persoon.query.filter_by(idnummer=klus.klussen_zoekers[0].idnummer).first()
        else:  # Indien de gebruiker een zoeker is, dan is de ontvanger de aanbieder
            ontvanger = Persoon.query.filter_by(idnummer=klus.idnummer).first()

        other_person_name = f"{ontvanger.voornaam} {ontvanger.achternaam}" if ontvanger else "Onbekend"

        klussen_info.append({
            'klusnummer': klus.klusnummer,
            'naam': klus.naam,
            'status': klus.status,
            'berichten': berichten,
            'type': 'gezocht',
            'other_person_name': other_person_name
        })

    # Sorteer op de datum van het laatste bericht, meest recent bovenaan
    klussen_info.sort(key=lambda x: x['berichten'][0].verzonden_op if x['berichten'] else datetime.min, reverse=True)

    return render_template('mijn_chats.html', klussen=klussen_info)




@main.route('/ratings/<rol>/<idnummer>', methods=['GET'])
def ratings(rol, idnummer):
    # Controleer of de rol geldig is
    if rol not in ['aanbieder', 'zoeker']:
        flash('Ongeldige rol opgegeven.', 'error')
        abort(404)

    # Haal de persoon op
    persoon = Persoon.query.filter_by(idnummer=idnummer).first()
    if not persoon:
        flash('Persoon niet gevonden.', 'error')
        abort(404)

    # Beoordelingen ophalen op basis van de rol, gesorteerd op de meest recente
    if rol == 'aanbieder':
        ratings = Rating.query.filter_by(klusaanbieder_id=idnummer).order_by(Rating.created_at.desc()).all()
    elif rol == 'zoeker':
        ratings = Rating.query.filter_by(kluszoeker_id=idnummer).order_by(Rating.created_at.desc()).all()

    # Bereken gemiddelde scores en extra statistieken
    gemiddelde_scores = {}
    if ratings:
        if rol == 'aanbieder':
            gemiddelde_scores = {
                'algemene_ervaring': round(sum(r.algemene_ervaring_aanbieder for r in ratings if r.algemene_ervaring_aanbieder) / len(ratings), 1),
            }
        elif rol == 'zoeker':
            gemiddelde_scores = {
                'algemene_ervaring': round(sum(r.algemene_ervaring_zoeker for r in ratings if r.algemene_ervaring_zoeker) / len(ratings), 1),
            }

    # Render de template met de gegevens
    return render_template(
        'bekijken_ratings.html',
        persoon=persoon,
        rol=rol,
        ratings=ratings,
        gemiddelde_scores=gemiddelde_scores
    )



@main.route('/rating/<int:rating_id>', methods=['GET'])
def ratings_detail(rating_id):
    # Zoek de beoordeling op in de database
    rating = Rating.query.get(rating_id)
    
    # Controleer of de beoordeling bestaat
    if not rating:
        abort(404, description="Rating not found")
    
    # Bepaal de rol (aanbieder of zoeker) door te controleren welke id ingevuld is
    if rating.klusaanbieder_id:
        rol = 'aanbieder'  # Beoordeling door de klusaanbieder
    elif rating.kluszoeker_id:
        rol = 'zoeker'  # Beoordeling door de kluszoeker
    else:
        rol = 'onbekend'  # Als er geen geldig id is, kun je dit als fallback gebruiken
    
    # Render de detailpagina
    return render_template(
        'ratings_detail.html',
        rating=rating,
        rol=rol
    )
