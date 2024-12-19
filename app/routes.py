from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort 
from app import db
from app.models import Persoon, Klusaanbieder, Kluszoeker, Categorie, Rating, klus_zoeker, Bericht, valideer_adres, Notificatie
from app.forms import PersoonForm, KlusaanbiederForm, KluszoekerForm, RegistrationForm, LoginForm
from app.forms import RatingFormForZoeker, RatingFormForAanbieder, RatingForm
import uuid
from app.models import Klus  # Voeg deze regel toe om de Klus-klasse te importeren
from flask_login import login_required
from datetime import datetime, date
import requests # type: ignore
from app.chat import get_ongelezen_chats_count
from werkzeug.exceptions import NotFound
from sqlalchemy.sql import func
from app.helpers import utc_to_plus_one



def maak_melding(gebruiker_id, bericht):
    notificatie = Notificatie(gebruiker_id=gebruiker_id, bericht=bericht)
    db.session.add(notificatie)
    db.session.commit()

def get_aantal_ongelezen_meldingen(user_id):
    return Bericht.query.filter_by(ontvanger_id=user_id, gelezen=False).count()


# Maak een blueprint
main = Blueprint('main', __name__)

# Functie om een 10-cijferig ID-nummer te genereren
def generate_id_number():
    return str(uuid.uuid4().int)[:10]  # Genereer een unieke UUID (beperk tot 10 cijfers)

# Route voor de startpagina
@main.route('/')
def home():
    return render_template('index.html')

from datetime import date
from flask import render_template, redirect, flash, url_for
from .models import Persoon  # Zorg ervoor dat je de juiste import hebt voor je model
from . import db  # Je moet 'db' importeren voor database interactie
from .forms import RegistrationForm  # Zorg ervoor dat je de juiste import hebt voor je formulier

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        print("Formulier is ingediend en geldig!")
        print(f"Gebruikersnaam: {form.username.data}")
        print(f"E-mail: {form.email.data}")
        print(f"Geboortedatum: {form.geboortedatum.data}")

        # Leeftijd berekenen
        geboortedatum = form.geboortedatum.data
        today = date.today()
        leeftijd = today.year - geboortedatum.year - ((today.month, today.day) < (geboortedatum.month, geboortedatum.day))

        # Controleer of de leeftijd minder dan 16 jaar is
        if leeftijd < 16:
            session['age_error'] = 'Je moet ouder zijn dan 16 jaar om een account aan te maken.'
            return redirect(url_for('main.register'))

        # Controleer of de gebruikersnaam al bestaat
        if Persoon.query.filter_by(username=form.username.data).first():
            flash('Deze gebruikersnaam is al in gebruik. Kies een andere.', 'danger')
            return redirect(url_for('main.register'))

        # Controleer of het e-mailadres al bestaat
        if Persoon.query.filter_by(email=form.email.data).first():
            flash('Dit e-mailadres is al in gebruik. Kies een ander e-mailadres.', 'danger')
            return redirect(url_for('main.register'))

        # Combineer stad en adres in een volledige locatie
        stad = form.stad.data
        adres = form.adres.data
        volledige_locatie = f"{stad}, {adres}"

        # Valideer het gecombineerde adres
        if not valideer_adres(volledige_locatie):
            flash("Het ingevoerde adres is ongeldig of bestaat niet.", 'danger')
            return redirect(url_for('main.register'))

        # Maak een nieuw Persoon object aan
        new_person = Persoon(
            voornaam=form.voornaam.data,
            achternaam=form.achternaam.data,
            geboortedatum=form.geboortedatum.data,
            geslacht=form.gender.data,
            telefoonnummer=form.telefoonnummer.data,
            email=form.email.data,
            adres=volledige_locatie,  # De gecombineerde locatie opslaan
            username=form.username.data,
            idnummer=generate_id_number()  # Dynamische ID
        )

        # Voeg de nieuwe persoon toe aan de database
        db.session.add(new_person)
        db.session.commit()

        # Bevestigingsbericht
        flash('Je bent succesvol geregistreerd!', 'success')

        # Redirect naar de loginpagina
        return redirect(url_for('main.login'))

    # Als het formulier niet is ingediend of niet geldig is, toon het registratieformulier
    age_error = session.pop('age_error', None)  # Get and remove 'age_error' from the session
    return render_template('register.html', form=form, age_error=age_error)





@main.route('/login', methods=['GET', 'POST'])
def login():
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
    ongelezen_chats_count = get_ongelezen_chats_count(user)

    return render_template('dashboard.html', 
                           user=user, 
                           geaccepteerde_klussen=geaccepteerde_klussen, 
                           aangeboden_klussen=aangeboden_klussen, 
                           ongelezen_chats_count=ongelezen_chats_count)

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

@main.route('/about')
def about():
    return render_template('about.html')



@main.route('/logout')
def logout():
    session.clear()  # Wis de sessie om de gebruiker uit te loggen
    flash('Je bent succesvol uitgelogd.', 'success')
    return redirect(url_for('main.login'))  # Stuur de gebruiker naar de loginpagina


@main.route('/profiel_bewerken', methods=['GET', 'POST'])
def profiel_bewerken():
    user_id = session.get('user_id')
    
    # Controleer of de gebruiker is ingelogd
    if not user_id:
        flash('Je moet ingelogd zijn om je profiel te bewerken.', 'danger')
        return redirect(url_for('main.login'))

    # Haal de gebruiker op uit de database
    user = Persoon.query.get(user_id)
    if not user:
        raise NotFound("Gebruiker niet gevonden.")
    
    if request.method == 'POST':
        # Verkrijg gegevens uit het formulier
        geboortedatum = datetime.strptime(request.form['geboortedatum'], '%Y-%m-%d').date()

        # Leeftijd berekenen
        today = date.today()
        leeftijd = today.year - geboortedatum.year - ((today.month, today.day) < (geboortedatum.month, geboortedatum.day))

        if leeftijd < 16:
            flash('Je moet ouder zijn dan 16 jaar.', 'danger')
            return redirect(url_for('main.profiel_bewerken'))

        # Update de gegevens van de gebruiker
        user.voornaam = request.form['voornaam']
        user.achternaam = request.form['achternaam']
        user.geboortedatum = geboortedatum
        user.email = request.form['email']
        user.telefoonnummer = request.form['telefoonnummer']
        user.adres = request.form['adres']
        user.geslacht = request.form['geslacht']
        user.username = request.form['username']
        
        db.session.commit()
        flash('Profiel succesvol bijgewerkt!', 'success')
        return redirect(url_for('main.profile'))

    return render_template('profiel_bewerken.html', user=user)





@main.route('/bevestig_verwijdering', methods=['GET', 'POST'])
def bevestig_verwijdering():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        try:
            user = Persoon.query.filter_by(idnummer=user_id).first()

            if not user:
                flash('Profiel niet gevonden.', 'danger')
                return redirect(url_for('main.profile'))

            # **1. Verwijder records uit klus_zoeker**
            db.session.execute(
                klus_zoeker.delete().where(
                    klus_zoeker.c.idnummer == user_id
                )
            )

            # **2. Verwijder gekoppelde berichten**
            Bericht.query.filter_by(afzender_id=user_id).delete()
            Bericht.query.filter_by(ontvanger_id=user_id).delete()

            # **3. Behoud beoordelingen die de gebruiker heeft gemaakt**
            # Verwijder alleen beoordelingen die de gebruiker ONTVANGEN heeft
            Rating.query.filter_by(klusaanbieder_id=user_id).delete()  # Beoordelingen over hem als klusaanbieder
            Rating.query.filter_by(kluszoeker_id=user_id).delete()    # Beoordelingen over hem als kluszoeker

            # **4. Verwijder aangeboden klussen**
            klussen = Klus.query.filter_by(idnummer=user_id).all()
            for klus in klussen:
                # Verwijder records uit klus_zoeker gekoppeld aan deze klus
                db.session.execute(
                    klus_zoeker.delete().where(
                        klus_zoeker.c.klusnummer == klus.klusnummer
                    )
                )
                db.session.delete(klus)

            # **5. Verwijder gekoppelde notificaties**
            Notificatie.query.filter_by(gebruiker_id=user_id).delete()

            # **6. Verwijder gekoppelde categorie_statistieken**
            CategorieStatistiek.query.filter_by(idnummer=user_id).delete()

            # **7. Verwijder het profiel**
            db.session.delete(user)
            db.session.commit()

            # **8. Clear de sessie en uitloggen**
            session.clear()
            flash('Je profiel en gekoppelde gegevens zijn succesvol verwijderd. Beoordelingen die je hebt gemaakt zijn behouden.', 'success')
            return redirect(url_for('main.home'))

        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Fout bij het verwijderen van het profiel: {e}")
            flash('Er is een fout opgetreden bij het verwijderen van je profiel. Probeer het opnieuw.', 'danger')
            return redirect(url_for('main.profile'))

    return render_template('bevestig_verwijdering.html')



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
            tijd_uren = int(form.uren.data)
            tijd_minuten = int(form.minuten.data)

            # Combineer het uur en de minuut in een tijd in het formaat 'HH:MM'
            tijd = f"{tijd_uren:02}:{tijd_minuten:02}"

            # Haal de uren en minuten voor de verwachte duur op
            verwachte_duur_uren = int(form.verwachte_duur_uren.data)
            verwachte_duur_minuten = int(form.verwachte_duur_minuten.data)

            # Combineer de uren en minuten in een totale duur in minuten
            verwachte_duur = f"{verwachte_duur_uren:01} u {verwachte_duur_minuten:02} min"

            # Stad en adres
            stad = form.stad.data
            adres = form.adres.data

            # Validatie: controleer of het ingevoerde adres bestaat
            volledige_locatie = f"{stad}, {adres}"
            if not valideer_adres(volledige_locatie):
                flash("Het ingevoerde adres is ongeldig of bestaat niet.", 'danger')
                return redirect(url_for('main.add_klusaanbieder'))

            # Maak een nieuwe Klus aan
            nieuwe_klus = Klus(
                naam=form.naam.data,
                locatie=volledige_locatie,  # De gecombineerde locatie
                tijd=tijd,  # De gecombineerde tijd
                beschrijving=form.beschrijving.data,
                vergoeding=form.vergoeding.data,
                categorie=form.categorie.data,
                datum=form.datum.data,
                verwachte_duur=verwachte_duur,  # De totale geschatte duur in minuten
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
    return render_template('add_klusaanbieder.html', form=form)




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


@main.route('/eigen_klus/<klusnummer>')
def details_eigen_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if klus is None:
        flash('Klus niet gevonden', 'danger')
        return redirect(url_for('main.klussen'))
    
    return render_template('details_eigen_klus.html', klus=klus)



from app.models import CategorieStatistiek, Klus, Persoon
from datetime import datetime
from flask import flash, redirect, url_for, request
from sqlalchemy import func

from datetime import datetime

@main.route('/klussen')
def klussen():
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om klussen te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    user = Persoon.query.get(user_id)

    # Filters ophalen uit de querystring
    geselecteerde_categorie = request.args.get('categorie', '')
    geselecteerde_locatie = request.args.get('locatie', '').lower()
    datum_van = request.args.get('datum_van', '')
    datum_tot = request.args.get('datum_tot', '')

    # Query voor alle beschikbare klussen (basisquery)
    vandaag = datetime.utcnow().date()
    basis_klussen_query = Klus.query.filter(Klus.status == 'beschikbaar', Klus.persoon_aanbieder != user, Klus.datum >= vandaag)

    # Query voor beschikbare klussen (inclusief actieve filters)
    beschikbare_klussen_query = basis_klussen_query

    # Filter op categorie
    if geselecteerde_categorie:
        beschikbare_klussen_query = beschikbare_klussen_query.filter(Klus.categorie == geselecteerde_categorie)

    # Filter op locatie (stad zonder postcode)
    if geselecteerde_locatie:
        beschikbare_klussen_query = beschikbare_klussen_query.filter(
            func.lower(Klus.locatie).like(f"%{geselecteerde_locatie}%")
        )

    # Filter op datumbereik
    if datum_van:
        try:
            datum_van = datetime.strptime(datum_van, '%Y-%m-%d').date()
            beschikbare_klussen_query = beschikbare_klussen_query.filter(Klus.datum >= datum_van)
        except ValueError:
            flash('Ongeldig formaat voor datum_van. Gebruik YYYY-MM-DD.', 'danger')

    if datum_tot:
        try:
            datum_tot = datetime.strptime(datum_tot, '%Y-%m-%d').date()
            beschikbare_klussen_query = beschikbare_klussen_query.filter(Klus.datum <= datum_tot)
        except ValueError:
            flash('Ongeldig formaat voor datum_tot. Gebruik YYYY-MM-DD.', 'danger')

    # Haal gefilterde klussen op
    beschikbare_klussen = beschikbare_klussen_query.all()

    # Locaties ophalen uit de basisquery (zonder actieve locatie-filter)
    beschikbare_locaties_query = basis_klussen_query.with_entities(func.lower(Klus.locatie)).distinct()
    unieke_steden = sorted({
        ''.join(filter(str.isalpha, locatie[0].split(",")[0])).strip().capitalize()
        for locatie in beschikbare_locaties_query
    })

    return render_template(
        'klussen_overzicht.html',
        klussen=beschikbare_klussen,
        categorieën=[c[0] for c in db.session.query(Klus.categorie).distinct()],
        locaties=unieke_steden,
        geselecteerde_categorie=geselecteerde_categorie,
        geselecteerde_locatie=geselecteerde_locatie,
        datum_van=datum_van,
        datum_tot=datum_tot
    )





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

from sqlalchemy.orm import joinedload


@main.route('/mijn_aangeboden_klussen', methods=['GET', 'POST'])
def mijn_aangeboden_klussen():
    user_id = session.get('user_id')  # Haal de ingelogde gebruiker op uit de sessie
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    # Query: Haal alleen klussen op die niet voltooid zijn
    klussen = Klus.query.filter(
        Klus.idnummer == user_id,   # Alleen klussen aangeboden door de gebruiker
        Klus.status != 'voltooid'   # Sluit voltooide klussen uit
    ).order_by(Klus.datum.desc()).all()

    return render_template('mijn_aangeboden_klussen.html', klussen=klussen)

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

    # Variabele naam consistent maken met de template
    return render_template('mijn_gezochte_klussen.html', klussen=gezochte_klussen)


@main.route('/leave_klus/<klusnummer>', methods=['POST'])
def leave_klus(klusnummer):
    user_id = session.get('user_id')
    if not user_id:
        flash("Je bent niet ingelogd.", "danger")
        return redirect(url_for('main.login'))

    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash("Klus niet gevonden.", "danger")
        return redirect(url_for('main.mijn_gezochte_klussen'))

    # Zoek de kluszoeker
    kluszoeker = next((zoeker for zoeker in klus.klussen_zoekers if zoeker.idnummer == user_id), None)
    if kluszoeker:
        # Verwijder de gebruiker van de klus
        klus.klussen_zoekers.remove(kluszoeker)
        klus.status = "beschikbaar"
        db.session.commit()

        # Notificatie naar klusaanbieder
        maak_melding(
            gebruiker_id=klus.idnummer,
            bericht=f"De kluszoeker heeft jouw klus '{klus.naam}' geannuleerd."
        )
        flash("De klus is geannuleerd en de aanbieder is op de hoogte gesteld.", "success")
    return redirect(url_for('main.mijn_gezochte_klussen'))


@main.route('/delete_klus/<klusnummer>', methods=['POST'])
def delete_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=str(klusnummer)).first()
    if not klus:
        flash('Klus niet gevonden.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    user_id = session.get('user_id')
    if klus.idnummer != user_id:
        flash('Je hebt geen toestemming om deze klus te verwijderen.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    try:
        # Notificatie naar alle gekoppelde kluszoekers
        for zoeker in klus.klussen_zoekers:
            maak_melding(
                gebruiker_id=zoeker.idnummer,
                bericht=f"De klus '{klus.naam}' is verwijderd door de aanbieder."
            )

        # Notificatie naar de klusaanbieder zelf
        maak_melding(
            gebruiker_id=user_id,
            bericht=f"Je hebt de klus '{klus.naam}' succesvol verwijderd."
        )

        # Verwijder de klus
        db.session.delete(klus)
        db.session.commit()
        flash(f"De klus '{klus.naam}' is verwijderd en de zoekers zijn op de hoogte gesteld.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Er is een fout opgetreden bij het verwijderen van de klus: {e}", 'danger')
        print(f"Fout bij verwijderen klus: {e}")

    return redirect(url_for('main.mijn_aangeboden_klussen'))


@main.route('/klus/<klusnummer>/accepteren', methods=['POST'])
def accepteer_klus(klusnummer):
    # Controleer of de gebruiker is ingelogd
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze klus te accepteren.', 'danger')
        return redirect(url_for('main.klussen'))

    # Zoek de klus op basis van klusnummer
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash('Deze klus bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))

    # Controleer of de klus beschikbaar is
    if klus.status != 'beschikbaar':
        flash('Deze klus is niet beschikbaar.', 'danger')
        return redirect(url_for('main.klussen'))

    # Haal de ingelogde gebruiker op
    user_id = session['user_id']
    gebruiker = Persoon.query.filter_by(idnummer=user_id).first()

    if not gebruiker:
        flash('Gebruiker niet gevonden.', 'danger')
        return redirect(url_for('main.klussen'))

    try:
        # Verander de status naar 'geaccepteerd'
        klus.status = 'geaccepteerd'

        # Voeg de gebruiker toe aan de klus_zoeker relatie
        if gebruiker not in klus.klussen_zoekers:
            klus.klussen_zoekers.append(gebruiker)
            print(f"Kluszoeker {gebruiker.idnummer} toegevoegd aan klus {klus.klusnummer}")
        else:
            print(f"Kluszoeker {gebruiker.idnummer} was al gekoppeld aan klus {klus.klusnummer}")

        # Werk de statistieken voor de categorie bij
        categorie_statistiek = CategorieStatistiek.query.filter_by(
            idnummer=user_id,
            categorie=klus.categorie
        ).first()

        if categorie_statistiek:
            categorie_statistiek.aantal_accepteerd += 1
        else:
            nieuwe_statistiek = CategorieStatistiek(
                idnummer=user_id,
                categorie=klus.categorie,
                aantal_accepteerd=1
            )
            db.session.add(nieuwe_statistiek)


        # Maak een melding voor de klusaanbieder
        maak_melding(
            gebruiker_id=klus.idnummer,
            bericht=f"Je klus '{klus.naam}' is geaccepteerd door {gebruiker.voornaam} {gebruiker.achternaam}."
        )

        # Sla de wijzigingen op
        db.session.commit()

        flash('Je hebt de klus geaccepteerd!', 'success')
        return redirect(url_for('main.mijn_gezochte_klussen'))
    except Exception as e:
        db.session.rollback()  # Rollback bij een fout
        flash(f'Er is een fout opgetreden: {e}', 'danger')
        return redirect(url_for('main.klussen'))


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

    # Gezochte klussen
    gezochte_klussen = Klus.query.join(Klus.klussen_zoekers).filter(
        Persoon.idnummer == user_id,
        Klus.status == 'voltooid',
        Klus.voltooid_op.isnot(None)
    ).order_by(Klus.voltooid_op.desc()).all()

    return render_template(
        'mijn_geschiedenis.html',
        aangeboden_klussen=aangeboden_klussen,
        gezochte_klussen=gezochte_klussen
    )


@main.route('/klus/<klusnummer>/markeer_voltooid', methods=['POST'])
def markeer_klus_voltooid(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash('Klus niet gevonden.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    # Haal de ingelogde gebruiker op
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze actie uit te voeren.', 'danger')
        return redirect(url_for('main.login'))
    
    user_id = session.get('user_id')
    if klus.idnummer != user_id:
        flash('Je hebt geen toestemming om deze actie uit te voeren.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    # Markeer de klus als voltooid
    klus.status = 'voltooid'
    klus.voltooid_op = utc_to_plus_one()
    db.session.commit()

    # Notificatie naar kluszoekers
    for zoeker in klus.klussen_zoekers:
        maak_melding(
            gebruiker_id=zoeker.idnummer,
            bericht=f"De klus '{klus.naam}' is gemarkeerd als voltooid. Je kunt nu een beoordeling nalaten."
        )

    # Notificatie naar klusaanbieder
    maak_melding(
        gebruiker_id=klus.idnummer,
        bericht=f"De klus '{klus.naam}' is voltooid. Je kunt nu een beoordeling nalaten."
    )

    flash("De klus is gemarkeerd als voltooid en beide partijen zijn op de hoogte gesteld.", 'success')
    return redirect(url_for('main.mijn_geschiedenis'))

    
@main.route('/rate_zoeker/<klusnummer>', methods=['GET', 'POST'])
def rate_zoeker(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash('Klus niet gevonden.', 'danger')
        return redirect(url_for('main.mijn_geschiedenis'))

    # Zoek bestaande beoordeling
    existing_rating = Rating.query.filter_by(
        klusnummer=klusnummer,
        kluszoeker_id=klus.klussen_zoekers[0].idnummer
    ).first()

    form = RatingFormForZoeker()
    if form.validate_on_submit():
        if existing_rating:
            # Update bestaande beoordeling
            existing_rating.vriendelijkheid_zoeker = form.vriendelijkheid.data
            existing_rating.tijdigheid = form.tijdigheid.data
            existing_rating.kwaliteit = form.kwaliteit.data
            existing_rating.communicatie_zoeker = form.communicatie.data
            existing_rating.algemene_ervaring_zoeker = form.algemene_ervaring.data
            existing_rating.comment = form.comment.data
        else:
            # Maak een nieuwe beoordeling
            new_rating = Rating(
                klusnummer=klusnummer,
                kluszoeker_id=klus.klussen_zoekers[0].idnummer,
                klusaanbieder_id=session.get('user_id'),
                vriendelijkheid_zoeker=form.vriendelijkheid.data,
                tijdigheid=form.tijdigheid.data,
                kwaliteit=form.kwaliteit.data,
                communicatie_zoeker=form.communicatie.data,
                algemene_ervaring_zoeker=form.algemene_ervaring.data,
                comment=form.comment.data,
            )
            db.session.add(new_rating)

        db.session.commit()

        # Meldingen
        # Melding naar de kluszoeker
        maak_melding(
            gebruiker_id=klus.klussen_zoekers[0].idnummer,
            bericht=f"Je bent beoordeeld door de klusaanbieder voor de klus '{klus.naam}'."
        )
        # Melding naar de klusaanbieder
        maak_melding(
            gebruiker_id=session.get('user_id'),
            bericht=f"Bedankt voor het achterlaten van een beoordeling voor de kluszoeker van '{klus.naam}'."
        )

        flash('Beoordeling succesvol toegevoegd!', 'success')
        return redirect(url_for('main.mijn_geschiedenis'))

    return render_template('rate_zoeker.html', form=form, klus=klus)


@main.route('/rate_aanbieder/<klusnummer>', methods=['GET', 'POST'])
def rate_aanbieder(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash('Klus niet gevonden.', 'danger')
        return redirect(url_for('main.mijn_geschiedenis'))

    # Controleer of de huidige gebruiker een kluszoeker is
    if not any(zoeker.idnummer == session.get('user_id') for zoeker in klus.klussen_zoekers):
        flash('Je bent niet bevoegd om deze beoordeling te maken.', 'danger')
        return redirect(url_for('main.mijn_geschiedenis'))

    # Zoek bestaande beoordeling
    existing_rating = Rating.query.filter_by(
        klusnummer=klusnummer,
        kluszoeker_id=session.get('user_id'),
        klusaanbieder_id=klus.idnummer
    ).first()

    form = RatingFormForAanbieder()
    if form.validate_on_submit():
        if existing_rating:
            # Update bestaande beoordeling
            existing_rating.vriendelijkheid_aanbieder = form.vriendelijkheid.data
            existing_rating.gastvrijheid = form.gastvrijheid.data
            existing_rating.betrouwbaarheid = form.betrouwbaarheid.data
            existing_rating.communicatie_aanbieder = form.communicatie.data
            existing_rating.algemene_ervaring_aanbieder = form.algemene_ervaring.data
            existing_rating.comment = form.comment.data
            flash('Beoordeling succesvol bijgewerkt!', 'success')
        else:
            # Voeg nieuwe beoordeling toe als er geen bestaat
            new_rating = Rating(
                klusnummer=klusnummer,
                klusaanbieder_id=klus.idnummer,
                kluszoeker_id=session.get('user_id'),
                vriendelijkheid_aanbieder=form.vriendelijkheid.data,
                gastvrijheid=form.gastvrijheid.data,
                betrouwbaarheid=form.betrouwbaarheid.data,
                communicatie_aanbieder=form.communicatie.data,
                algemene_ervaring_aanbieder=form.algemene_ervaring.data,
                comment=form.comment.data,
                created_at=utc_to_plus_one()
            )
            db.session.add(new_rating)
            flash('Beoordeling succesvol toegevoegd!', 'success')

        db.session.commit()

        # Meldingen
        # Melding naar de klusaanbieder
        maak_melding(
            gebruiker_id=klus.idnummer,
            bericht=f"Je bent beoordeeld door de kluszoeker voor de klus '{klus.naam}'."
        )
        # Melding naar de kluszoeker
        maak_melding(
            gebruiker_id=session.get('user_id'),
            bericht=f"Bedankt voor het achterlaten van een beoordeling voor de klusaanbieder van '{klus.naam}'."
        )

        return redirect(url_for('main.mijn_geschiedenis'))

    return render_template('rate_aanbieder.html', form=form, klus=klus)


@main.route('/ratings/<rol>/<idnummer>', methods=['GET'])
def ratings(rol, idnummer):
    back_url = request.args.get('back_url', url_for('main.dashboard'))
    
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
        gemiddelde_scores=gemiddelde_scores,
        back_url=back_url
    )


@main.route('/rating/<int:rating_id>', methods=['GET'])
def ratings_detail(rating_id):
    # Zoek de beoordeling op in de database
    rating = Rating.query.get(rating_id)
    
    # Controleer of de beoordeling 
    if not rating:
        abort(404, description="Rating not found")
    
    # Bepaal de rol (aanbieder of zoeker) door te controleren welke id ingevuld is
    if rating.klusaanbieder_id:
        rol = 'aanbieder'  # Beoordeling door de klusaanbieder
    elif rating.kluszoeker_id:
        rol = 'zoeker'  # Beoordeling door de kluszoeker
    else:
        rol = 'onbekend'  # Als er geen geldig id is, kun je dit als fallback gebruiken
    
    back_url = url_for('main.ratings', rol=rol, idnummer=rating.klusaanbieder_id)

    # Render de detailpagina
    return render_template(
        'ratings_detail.html',
        rating=rating,
        rol=rol,
        back_url=back_url
    )


@main.route('/rating/zoeker/<int:rating_id>', methods=['GET'])
def ratings_detail_zoeker(rating_id):
    # Zoek de beoordeling op in de database
    rating = Rating.query.get(rating_id)
    
    # Controleer of de beoordeling bestaat
    if not rating:
        abort(404, description="Rating not found")
    
    # Bepaal de rol (zoeker of aanbieder) door te controleren welke id ingevuld is
    if rating.kluszoeker_id:
        rol = 'zoeker'  # Beoordeling door de kluszoeker
    elif rating.klusaanbieder_id:
        rol = 'aanbieder'  # Beoordeling door de klusaanbieder
    else:
        rol = 'onbekend'  # Fallback als er geen geldig id is
    
    back_url = url_for('main.beoordelingen_kluszoeker', rol=rol, idnummer=rating.kluszoeker_id, klusnummer=rating.klusnummer)

    # Render de detailpagina voor de zoeker
    return render_template(
        'ratings_detail_zoeker.html',
        rating=rating,
        rol=rol,
        back_url=back_url
    )


@main.route('/notificaties', methods=['GET'])
@login_required
def notificaties():
    gebruiker_id = session.get('user_id')
    notificaties = Notificatie.query.filter_by(gebruiker_id=gebruiker_id).order_by(Notificatie.aangemaakt_op.desc()).all()
    return render_template('notificaties.html', notificaties=notificaties)


@main.route('/notificatie/<int:id>/gelezen', methods=['POST'])
def markeer_melding_gelezen(id):
    try:
        notificatie = Notificatie.query.filter_by(id=int(id)).first()
        if notificatie:
            notificatie.gelezen = True
            db.session.commit()
            flash("Melding gemarkeerd als gelezen.", "success")
        else:
            flash("Melding niet gevonden.", "danger")
    except Exception as e:
        db.session.rollback()
        print(f"Fout bij het markeren als gelezen: {e}")
        flash("Er ging iets mis bij het markeren van de melding.", "danger")
    return redirect(url_for('main.alle_meldingen'))


@main.app_context_processor
def inject_notificaties():
    if 'user_id' in session and session['user_id']:
        # Laatste 5 meldingen ophalen
        laatste_vijf_meldingen = Notificatie.query.filter_by(
            gebruiker_id=session['user_id']
        ).order_by(Notificatie.aangemaakt_op.desc()).limit(5).all()

        # Totaal aantal ongelezen meldingen
        aantal_ongelezen = Notificatie.query.filter_by(
            gebruiker_id=session['user_id'], gelezen=False
        ).count()

        return {
            'notificaties': laatste_vijf_meldingen,  # Alleen laatste 5
            'aantal_ongelezen_meldingen': aantal_ongelezen
        }
    return {
        'notificaties': [],
        'aantal_ongelezen_meldingen': 0
    }


@main.route('/klus/<klusnummer>/beoordeel_aanbieder', methods=['POST'])
def beoordeel_aanbieder(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash("Klus niet gevonden.", "danger")
        return redirect(url_for('main.dashboard'))

    form = RatingForm()  # Formulier voor beoordeling
    if form.validate_on_submit():
        # Beoordeling aanmaken
        rating = Rating(
            klusnummer=klusnummer,
            klusaanbieder_id=klus.idnummer,
            kluszoeker_id=session['user_id'],
            vriendelijkheid_aanbieder=form.vriendelijkheid.data,
            gastvrijheid=form.gastvrijheid.data,
            betrouwbaarheid=form.betrouwbaarheid.data,
            communicatie_aanbieder=form.communicatie.data,
            algemene_ervaring_aanbieder=form.algemene_ervaring.data,
            comment=form.algemene_ervaring_comment.data
        )
        db.session.add(rating)
        db.session.commit()

        # Notificatie naar klusaanbieder
        maak_melding(
            gebruiker_id=klus.idnummer,
            bericht=f"Je bent beoordeeld door de kluszoeker voor de klus '{klus.naam}'."
        )

        flash("Beoordeling opgeslagen en melding verstuurd.", "success")
        return redirect(url_for('main.mijn_geschiedenis'))
    return render_template('beoordeel_aanbieder.html', form=form, klus=klus)


@main.route('/klus/<klusnummer>/beoordeel_zoeker', methods=['POST'])
def beoordeel_zoeker(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash("Klus niet gevonden.", "danger")
        return redirect(url_for('main.dashboard'))

    form = RatingFormForZoeker()  # Formulier voor beoordeling
    if form.validate_on_submit():
        # Beoordeling aanmaken
        rating = Rating(
            klusnummer=klusnummer,
            klusaanbieder_id=session['user_id'],
            kluszoeker_id=klus.klussen_zoekers[0].idnummer,  # Stel dat er één zoeker is
            vriendelijkheid_zoeker=form.vriendelijkheid.data,
            tijdigheid=form.tijdigheid.data,
            kwaliteit=form.kwaliteit.data,
            communicatie_zoeker=form.communicatie.data,
            algemene_ervaring_zoeker=form.algemene_ervaring.data,
            comment=form.algemene_ervaring_comment.data
        )
        db.session.add(rating)
        db.session.commit()

        # Notificatie naar kluszoeker
        maak_melding(
            gebruiker_id=klus.klussen_zoekers[0].idnummer,
            bericht=f"Je bent beoordeeld door de klusaanbieder voor de klus '{klus.naam}'."
        )

        flash("Beoordeling opgeslagen en melding verstuurd.", "success")
        return redirect(url_for('main.mijn_geschiedenis'))
    return render_template('beoordeel_zoeker.html', form=form, klus=klus)


@main.route('/meldingen', methods=['GET'])
def alle_meldingen():
    if 'user_id' not in session:
        flash("Je moet ingelogd zijn om meldingen te bekijken.", "warning")
        return redirect(url_for('main.login'))

    # Haal alle meldingen van de gebruiker op
    alle_meldingen = Notificatie.query.filter_by(
        gebruiker_id=session['user_id']
    ).order_by(Notificatie.aangemaakt_op.desc()).all()

    return render_template('alle_meldingen.html', meldingen=alle_meldingen)


@main.route('/beoordelingen/<string:klusnummer>', methods=['GET'])
def beoordelingen_kluszoeker(klusnummer):
    # Haal de klus op aan de hand van klusnummer
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    
    if not klus:
        flash("De gevraagde klus bestaat niet.", "danger")
        return redirect(url_for('main.home'))

    # Haal de eerste kluszoeker op
    kluszoeker = klus.klussen_zoekers[0] if klus.klussen_zoekers else None
    
    if not kluszoeker:
        flash("Er zijn geen kluszoekers gekoppeld aan deze klus.", "warning")
        return redirect(url_for('main.home'))

    # Haal alle beoordelingen voor deze kluszoeker
    ratings = Rating.query.filter_by(kluszoeker_id=kluszoeker.idnummer).order_by(Rating.created_at.desc()).all()

    # Bereken gemiddelde score van de algemene ervaring
    gemiddelde_scores = None
    if ratings:
        gemiddelde_scores = round(sum(r.algemene_ervaring_zoeker for r in ratings if r.algemene_ervaring_zoeker) / len(ratings), 1)

    back_url = request.referrer or url_for('main.dashboard')

    return render_template(
        'beoordelingen_kluszoeker.html',
        klus=klus,
        kluszoeker=kluszoeker,
        ratings=ratings,
        gemiddelde_scores=gemiddelde_scores,
        back_url=back_url
    )
