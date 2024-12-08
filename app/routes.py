from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort 
from app import db
from app.models import Persoon, Klusaanbieder, Kluszoeker, Categorie, Rating, klus_zoeker
from app.forms import PersoonForm, KlusaanbiederForm, KluszoekerForm, RegistrationForm, LoginForm, RatingForm
import uuid
from app.models import Klus  # Voeg deze regel toe om de Klus-klasse te importeren
from flask_login import current_user, login_required
from datetime import datetime

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
    if 'user_id' not in session:
        flash('Je moet eerst inloggen om je profiel te bekijken.', 'warning')
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    user = Persoon.query.get(user_id)  # Gebruik user_id om de juiste gebruiker op te halen

    if user:
        return render_template('profile.html', user=user)
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

    user = Persoon.query.filter_by(idnummer=user_id).first()

    if not user:
        flash('Profiel niet gevonden.', 'danger')
        return redirect(url_for('main.profile'))

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
    flash('Je profiel is succesvol verwijderd.', 'success')
    return redirect(url_for('main.home'))


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


@main.route('/klus/<klusnummer>/bevestiging', methods=['GET'])
def bevestiging_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if klus:
        return render_template('bevestiging_klus.html', klus=klus)
    else:
        flash('Deze klus bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))


# Beoordelingen indienen via POST request
@main.route('/submit-rating/<klusnummer>', methods=['GET', 'POST'])
def submit_rating(klusnummer):
    # Haal de klus op
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if not klus:
        flash("Klus niet gevonden.", "danger")
        return redirect(url_for('main.mijn_geschiedenis'))

    # Controleer of de huidige gebruiker de aanbieder is
    is_aangeboden = klus.idnummer == session.get('user_id')

    # Haal de juiste partijen op
    kluszoeker_id = None
    if klus.klussen_zoekers:
        kluszoeker_id = klus.klussen_zoekers[0].idnummer

    klusaanbieder_id = klus.idnummer

    # Controleer of er al een beoordeling bestaat voor deze combinatie
    bestaande_rating = Rating.query.filter_by(
        klusnummer=klusnummer,
        kluszoeker_id=kluszoeker_id if is_aangeboden else session.get('user_id'),
        klusaanbieder_id=klusaanbieder_id if not is_aangeboden else session.get('user_id')
    ).first()

    if bestaande_rating:
        flash("Beoordeling is al ingediend voor deze klus.", "warning")
        return redirect(url_for('main.mijn_geschiedenis'))

    # Formulier instantiëren
    form = RatingForm()

    # Debugging (alleen bij POST-verzoeken)
    if request.method == 'POST':
        print(f"Formulier Data: {form.data}")
        print(f"Validatie Succesvol: {form.validate_on_submit()}")
        if not form.validate_on_submit():
            print(f"Formulier Fouten: {form.errors}")

    # Wanneer het formulier is ingediend
    if form.validate_on_submit():
        try:
            # Maak een nieuwe beoordeling aan
            new_rating = Rating(
                klusnummer=klusnummer,
                kluszoeker_id=kluszoeker_id if is_aangeboden else session.get('user_id'),
                klusaanbieder_id=klusaanbieder_id if not is_aangeboden else session.get('user_id'),
                communicatie=form.communicatie.data,
                betrouwbaarheid=form.betrouwbaarheid.data,
                tijdigheid=form.tijdigheid.data,
                kwaliteit=form.kwaliteit.data,
                algemene_ervaring=form.algemene_ervaring.data,
                comment=f"Communicatie: {form.communicatie_comment.data or 'N.v.t.'}\n"
                        f"Betrouwbaarheid: {form.betrouwbaarheid_comment.data or 'N.v.t.'}\n"
                        f"Tijdigheid: {form.tijdigheid_comment.data or 'N.v.t.'}\n"
                        f"Kwaliteit: {form.kwaliteit_comment.data or 'N.v.t.'}\n"
                        f"Algemene Ervaring: {form.algemene_ervaring_comment.data or 'N.v.t.'}"
            )

            # Sla de beoordeling op
            db.session.add(new_rating)
            db.session.commit()

            flash("Beoordeling succesvol ingediend!", "success")
            return redirect(url_for('main.mijn_geschiedenis'))
        except Exception as e:
            db.session.rollback()
            flash(f"Er is een fout opgetreden bij het opslaan van de beoordeling: {e}", "danger")
            print(f"Database Fout: {e}")

    return render_template('submit_rating.html', form=form, klus=klus, is_aangeboden=is_aangeboden)

# Bedankpagina
@main.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

# Beoordelingen weergeven
@main.route('/ratings/<klusnummer>')
def view_ratings(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if not klus:
        return redirect(url_for('main.index'))  # Als de klus niet bestaat, terug naar de homepage

    ratings = Rating.query.filter_by(klusnummer=klusnummer).all()  # Alle beoordelingen voor de klus

    # Bereken de gemiddelde beoordeling
    average_rating = 'Nog geen beoordelingen'
    if ratings:
        total = sum(r.rating_zoeker + r.rating_aanbieder for r in ratings)  # Som van beoordelingen
        average_rating = round(total / (len(ratings) * 2), 2)  # Gemiddelde beoordeling

    return render_template('ratings.html', ratings=ratings, average_rating=average_rating, klusnummer=klusnummer)


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

@main.route('/beoordelen/<klusnummer>', methods=['GET', 'POST'])
def view_rating(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()

    if not klus or klus.status != 'completed':
        return redirect(url_for('main.mijn_klussen', klusnummer=klusnummer))  # Redirect naar klus als de status niet 'completed' is

    form = RatingForm()  # Je kunt een bestaande RatingForm gebruiken die je eerder hebt gedefinieerd.

    if form.validate_on_submit():
        # Haal de id's van de kluszoeker en klusaanbieder
        kluszoeker_id = klus.klussen_zoekers[0].idnummer  # Dit kan afhangen van de logica van je relatie
        klusaanbieder_id = klus.persoon_aanbieder.idnummer

        # Maak de beoordeling aan
        new_rating = Rating(
            klusnummer=klusnummer,
            kluszoeker_id=kluszoeker_id,
            klusaanbieder_id=klusaanbieder_id,
            rating_zoeker=form.rating_zoeker.data,  # Rating voor de kluszoeker
            rating_aanbieder=form.rating_aanbieder.data,  # Rating voor de klusaanbieder
            comment_zoeker=form.comment_zoeker.data,  # Commentaar voor de kluszoeker
            comment_aanbieder=form.comment_aanbieder.data,  # Commentaar voor de klusaanbieder
            created_at=datetime.now()
        )

        # Sla de beoordeling op in de database
        db.session.add(new_rating)
        db.session.commit()

        return redirect(url_for('thank_you'))  # Redirect naar een bedankpagina of een andere pagina

    return render_template('submit_ratings.html', form=form, klusnummer=klusnummer)

@main.route('/mijn_klussen_selectie', methods=['GET'])
def mijn_klussen_selectie():
    return render_template('mijn_klussen_selectie.html')

@main.route('/mijn_aangeboden_klussen', methods=['GET', 'POST'])
def mijn_aangeboden_klussen():
    user_id = session.get('user_id')  # Haal de ingelogde gebruiker op uit de sessie
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    # Query voor klussen aangeboden door de ingelogde gebruiker, gesorteerd op datum (meest recent eerst)
    klussen = Klus.query.filter_by(idnummer=user_id).order_by(Klus.datum.desc()).all()

    # Verwerk de klussen voor de weergave
    klussen_info = []
    for klus in klussen:
        klussen_info.append({
            'id': klus.klusnummer,  # Gebruik 'klusnummer' als unieke ID
            'naam': klus.naam,
            'datum': klus.datum.strftime('%d-%m-%Y') if klus.datum else 'Onbekend',  # Controleer op None
            'status': klus.status,  # Gebruik de werkelijke status
        })

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

    # Haal klussen op waar de gebruiker geaccepteerd is
    gezochte_klussen = Klus.query.filter(
        Klus.status == 'geaccepteerd',
        Klus.klussen_zoekers.any(Persoon.idnummer == user_id)
    ).order_by(Klus.created_at.desc()).all()

    print(f"Gezochte klussen gevonden: {[klus.naam for klus in gezochte_klussen]}")
    
    return render_template('mijn_gezochte_klussen.html', gezochte_klussen=gezochte_klussen)

@main.route('/leave_klus/<string:klusnummer>', methods=['POST'])
def leave_klus(klusnummer):
    # Haal de klus op aan de hand van het klusnummer
    klus = Klus.query.get_or_404(klusnummer)

    # Controleer of de gebruiker is gekoppeld als zoeker
    zoeker = next((zoeker for zoeker in klus.klussen_zoekers if zoeker.idnummer == current_user.idnummer), None)
    if not zoeker:
        flash('Je bent niet gekoppeld aan deze klus.', 'danger')
        return redirect(url_for('main.mijn_gezochte_klussen'))

    # Verwijder de gebruiker als zoeker
    klus.klussen_zoekers.remove(zoeker)
    db.session.commit()
    flash('Je bent succesvol uitgeschreven van deze klus.', 'success')
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

    # Aangeboden klussen: Klussen die de gebruiker heeft aangeboden, gesorteerd op voltooiingstijd
    aangeboden_klussen = Klus.query.filter_by(idnummer=user_id, status='voltooid').order_by(Klus.voltooid_op.desc()).all()

    # Gezochte klussen: Klussen waarbij de gebruiker een van de zoekers is, gesorteerd op voltooiingstijd
    gezochte_klussen = Klus.query.join(Klus.klussen_zoekers).filter(
        Persoon.idnummer == user_id,
        Klus.status == 'voltooid'
    ).order_by(Klus.voltooid_op.desc()).all()

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

    # Verplaats de klus naar geschiedenis voor de aanbieder
    flash(f"De klus '{klus.naam}' is gemarkeerd als voltooid en toegevoegd aan je geschiedenis.", 'success')

    # Update geschiedenis voor alle gekoppelde zoekers
    zoekers = klus.klussen_zoekers
    for zoeker in zoekers:
        # Controleer of de klus nog in de gezochte klussen van de zoeker staat
        if klus in zoeker.geinteresseerd_in_klussen:
            zoeker.geinteresseerd_in_klussen.remove(klus)
            db.session.commit()

        flash(f"Klus '{klus.naam}' is verplaatst naar de geschiedenis van zoeker {zoeker.naam}.", 'info')

    return redirect(url_for('main.mijn_geschiedenis'))
