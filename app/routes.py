from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort 
from app import db
from app.models import Persoon, Klus, Rating, klus_zoeker, Bericht, valideer_adres, Notificatie, CategorieStatistiek
from app.forms import KlusaanbiederForm, RegistrationForm, LoginForm, RatingFormForZoeker, RatingFormForAanbieder
import uuid
from flask_login import login_required
from datetime import datetime, date
import requests # type: ignore
from app.chat import get_ongelezen_chats_count
from werkzeug.exceptions import NotFound
from sqlalchemy.sql import func
from app.helpers import utc_to_plus_one
from sqlalchemy import func

def maak_melding(gebruiker_id, bericht):
    notificatie = Notificatie(gebruiker_id=gebruiker_id, bericht=bericht)
    db.session.add(notificatie)
    db.session.commit()

def get_aantal_ongelezen_meldingen(user_id):
    return Bericht.query.filter_by(ontvanger_id=user_id, gelezen=False).count()


main = Blueprint('main', __name__)

def generate_id_number():
    return str(uuid.uuid4().int)[:10]

@main.route('/')
def home():
    return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        print("Formulier is ingediend en geldig!")
        print(f"Gebruikersnaam: {form.username.data}")
        print(f"E-mail: {form.email.data}")
        print(f"Geboortedatum: {form.geboortedatum.data}")

        geboortedatum = form.geboortedatum.data
        today = date.today()
        leeftijd = today.year - geboortedatum.year - ((today.month, today.day) < (geboortedatum.month, geboortedatum.day))

        if leeftijd < 16:
            session['age_error'] = 'Je moet ouder zijn dan 16 jaar om een account aan te maken.'
            return redirect(url_for('main.register'))

        if Persoon.query.filter_by(username=form.username.data).first():
            flash('Deze gebruikersnaam is al in gebruik. Kies een andere.', 'danger')
            return redirect(url_for('main.register'))

        if Persoon.query.filter_by(email=form.email.data).first():
            flash('Dit e-mailadres is al in gebruik. Kies een ander e-mailadres.', 'danger')
            return redirect(url_for('main.register'))

        stad = form.stad.data
        adres = form.adres.data
        volledige_locatie = f"{stad}, {adres}"

        if not valideer_adres(volledige_locatie):
            flash("Het ingevoerde adres is ongeldig of bestaat niet.", 'danger')
            return redirect(url_for('main.register'))

        new_person = Persoon(
            voornaam=form.voornaam.data,
            achternaam=form.achternaam.data,
            geboortedatum=form.geboortedatum.data,
            geslacht=form.gender.data,
            telefoonnummer=form.telefoonnummer.data,
            email=form.email.data,
            adres=volledige_locatie,
            username=form.username.data,
            idnummer=generate_id_number()
        )

        db.session.add(new_person)
        db.session.commit()

        flash('Je bent succesvol geregistreerd!', 'success')

        return redirect(url_for('main.login'))

    age_error = session.pop('age_error', None)
    return render_template('register.html', form=form, age_error=age_error)





@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        user = Persoon.query.filter_by(username=username).first()

        if user:
            session['user_id'] = user.idnummer
            return redirect(url_for('main.dashboard'))
        else:
            flash('Ongeldige gebruikersnaam', 'danger')

    return render_template('login.html', form=form)


@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Je moet eerst inloggen', 'danger')
        return redirect(url_for('main.login'))

    user = Persoon.query.get(session['user_id'])
    if not user:
        flash('Gebruiker niet gevonden', 'danger')
        return redirect(url_for('main.login'))

    geaccepteerde_klussen = Klus.query.filter_by(idnummer=user.idnummer, status='geaccepteerd').all()
    aangeboden_klussen = Klus.query.filter_by(idnummer=user.idnummer).all()
    ongelezen_chats_count = get_ongelezen_chats_count(user)

    return render_template('dashboard.html', 
                           user=user, 
                           geaccepteerde_klussen=geaccepteerde_klussen, 
                           aangeboden_klussen=aangeboden_klussen, 
                           ongelezen_chats_count=ongelezen_chats_count)

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
    session.clear()
    flash('Je bent succesvol uitgelogd.', 'success')
    return redirect(url_for('main.login'))


@main.route('/profiel_bewerken', methods=['GET', 'POST'])
def profiel_bewerken():
    user_id = session.get('user_id')
    
    if not user_id:
        flash('Je moet ingelogd zijn om je profiel te bewerken.', 'danger')
        return redirect(url_for('main.login'))

    user = Persoon.query.get(user_id)
    if not user:
        raise NotFound("Gebruiker niet gevonden.")
    
    if request.method == 'POST':
        geboortedatum = datetime.strptime(request.form['geboortedatum'], '%Y-%m-%d').date()

        today = date.today()
        leeftijd = today.year - geboortedatum.year - ((today.month, today.day) < (geboortedatum.month, geboortedatum.day))

        if leeftijd < 16:
            flash('Je moet ouder zijn dan 16 jaar.', 'danger')
            return redirect(url_for('main.profiel_bewerken'))

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

            db.session.execute(
                klus_zoeker.delete().where(
                    klus_zoeker.c.idnummer == user_id
                )
            )

            Bericht.query.filter_by(afzender_id=user_id).delete()
            Bericht.query.filter_by(ontvanger_id=user_id).delete()

            Rating.query.filter_by(klusaanbieder_id=user_id).delete()
            Rating.query.filter_by(kluszoeker_id=user_id).delete()

            klussen = Klus.query.filter_by(idnummer=user_id).all()
            for klus in klussen:
                db.session.execute(
                    klus_zoeker.delete().where(
                        klus_zoeker.c.klusnummer == klus.klusnummer
                    )
                )
                db.session.delete(klus)

            Notificatie.query.filter_by(gebruiker_id=user_id).delete()

            CategorieStatistiek.query.filter_by(idnummer=user_id).delete()

            db.session.delete(user)
            db.session.commit()

            session.clear()
            flash('Je profiel en gekoppelde gegevens zijn succesvol verwijderd. Beoordelingen die je hebt gemaakt zijn behouden.', 'success')
            return redirect(url_for('main.home'))

        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Fout bij het verwijderen van het profiel: {e}")
            flash('Er is een fout opgetreden bij het verwijderen van je profiel. Probeer het opnieuw.', 'danger')
            return redirect(url_for('main.profile'))

    return render_template('bevestig_verwijdering.html')

@main.route('/add_klusaanbieder', methods=['GET', 'POST'])
def add_klusaanbieder():
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze actie uit te voeren', 'danger')
        return redirect(url_for('main.login'))

    persoon = Persoon.query.get(session['user_id'])

    if not persoon:
        flash('Persoon niet gevonden', 'danger')
        return redirect(url_for('main.dashboard'))

    form = KlusaanbiederForm()

    if form.validate_on_submit():
        try:
            tijd_uren = int(form.uren.data)
            tijd_minuten = int(form.minuten.data)

            tijd = f"{tijd_uren:02}:{tijd_minuten:02}"

            verwachte_duur_uren = int(form.verwachte_duur_uren.data)
            verwachte_duur_minuten = int(form.verwachte_duur_minuten.data)

            verwachte_duur = f"{verwachte_duur_uren:01} u {verwachte_duur_minuten:02} min"

            stad = form.stad.data
            adres = form.adres.data

            volledige_locatie = f"{stad}, {adres}"
            if not valideer_adres(volledige_locatie):
                flash("Het ingevoerde adres is ongeldig of bestaat niet.", 'danger')
                return redirect(url_for('main.add_klusaanbieder'))

            nieuwe_klus = Klus(
                naam=form.naam.data,
                locatie=volledige_locatie,
                tijd=tijd,
                beschrijving=form.beschrijving.data,
                vergoeding=form.vergoeding.data,
                categorie=form.categorie.data,
                datum=form.datum.data,
                verwachte_duur=verwachte_duur,
                idnummer=persoon.idnummer
            )
            db.session.add(nieuwe_klus)
            db.session.commit()

            flash('Klus succesvol toegevoegd!', 'success')
            return redirect(url_for('main.mijn_aangeboden_klussen'))
        except Exception as e:
            db.session.rollback()
            flash(f'Er is een fout opgetreden bij het opslaan: {e}', 'danger')
            return redirect(url_for('main.add_klusaanbieder'))
    else:
        if form.errors:
            flash(f'Formulierfout: {form.errors}', 'danger')

    return render_template('add_klusaanbieder.html', form=form)

@main.route('/klus/<klusnummer>')
def klus_detail(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if klus is None:
        flash('Klus niet gevonden', 'danger')
        return redirect(url_for('main.klussen'))
    
    print(f"Status van de klus: {klus.status}")

    return render_template('klus_detail.html', klus=klus)

@main.route('/eigen_klus/<klusnummer>')
def details_eigen_klus(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if klus is None:
        flash('Klus niet gevonden', 'danger')
        return redirect(url_for('main.klussen'))
    
    return render_template('details_eigen_klus.html', klus=klus)

@main.route('/klussen')
def klussen():
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om klussen te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    user = Persoon.query.get(user_id)

    geselecteerde_categorie = request.args.get('categorie', '')
    geselecteerde_locatie = request.args.get('locatie', '').lower()
    datum_van = request.args.get('datum_van', '')
    datum_tot = request.args.get('datum_tot', '')

    vandaag = datetime.utcnow().date()
    basis_klussen_query = Klus.query.filter(Klus.status == 'beschikbaar', Klus.persoon_aanbieder != user, Klus.datum >= vandaag)

    beschikbare_klussen_query = basis_klussen_query

    if geselecteerde_categorie:
        beschikbare_klussen_query = beschikbare_klussen_query.filter(Klus.categorie == geselecteerde_categorie)

    if geselecteerde_locatie:
        beschikbare_klussen_query = beschikbare_klussen_query.filter(
            func.lower(Klus.locatie).like(f"%{geselecteerde_locatie}%")
        )

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

    beschikbare_klussen = beschikbare_klussen_query.all()

    categorie_statistieken = CategorieStatistiek.query.filter_by(idnummer=user_id).all()

    categorie_rangorde = {
        stat.categorie: stat.aantal_accepteerd for stat in categorie_statistieken
    }

    beschikbare_klussen.sort(
        key=lambda klus: -categorie_rangorde.get(klus.categorie, 0)
    )

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
        return redirect(url_for('main.klussen'))

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
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    user = Persoon.query.get(user_id)
    
    klussen = Klus.query.filter(Klus.idnummer == user.idnummer, Klus.status == 'geaccepteerd').all()

    return render_template('mijn_klussen.html', klussen=klussen)

@main.route('/mijn_klussen_selectie', methods=['GET'])
def mijn_klussen_selectie():
    return render_template('mijn_klussen_selectie.html')

@main.route('/mijn_aangeboden_klussen', methods=['GET', 'POST'])
def mijn_aangeboden_klussen():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    klussen = Klus.query.filter(
        Klus.idnummer == user_id,
        Klus.status != 'voltooid'
    ).order_by(Klus.datum.desc()).all()

    return render_template('mijn_aangeboden_klussen.html', klussen=klussen)

@main.route('/mijn_gezochte_klussen')
def mijn_gezochte_klussen():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    gezochte_klussen = Klus.query.filter(
        Klus.status == 'geaccepteerd',
        Klus.klussen_zoekers.any(Persoon.idnummer == user_id)
    ).order_by(Klus.created_at.desc()).all()

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

    kluszoeker = next((zoeker for zoeker in klus.klussen_zoekers if zoeker.idnummer == user_id), None)
    if kluszoeker:
        klus.klussen_zoekers.remove(kluszoeker)
        klus.status = "beschikbaar"
        db.session.commit()

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
        for zoeker in klus.klussen_zoekers:
            maak_melding(
                gebruiker_id=zoeker.idnummer,
                bericht=f"De klus '{klus.naam}' is verwijderd door de aanbieder."
            )

        maak_melding(
            gebruiker_id=user_id,
            bericht=f"Je hebt de klus '{klus.naam}' succesvol verwijderd."
        )

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
    if 'user_id' not in session:
        flash('Je moet ingelogd zijn om deze klus te accepteren.', 'danger')
        return redirect(url_for('main.klussen'))

    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    if not klus:
        flash('Deze klus bestaat niet.', 'danger')
        return redirect(url_for('main.klussen'))

    if klus.status != 'beschikbaar':
        flash('Deze klus is niet beschikbaar.', 'danger')
        return redirect(url_for('main.klussen'))

    user_id = session['user_id']
    gebruiker = Persoon.query.filter_by(idnummer=user_id).first()

    if not gebruiker:
        flash('Gebruiker niet gevonden.', 'danger')
        return redirect(url_for('main.klussen'))

    try:
        klus.status = 'geaccepteerd'

        if gebruiker not in klus.klussen_zoekers:
            klus.klussen_zoekers.append(gebruiker)
            print(f"Kluszoeker {gebruiker.idnummer} toegevoegd aan klus {klus.klusnummer}")
        else:
            print(f"Kluszoeker {gebruiker.idnummer} was al gekoppeld aan klus {klus.klusnummer}")

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


        maak_melding(
            gebruiker_id=klus.idnummer,
            bericht=f"Je klus '{klus.naam}' is geaccepteerd door {gebruiker.voornaam} {gebruiker.achternaam}."
        )

        db.session.commit()

        flash('Je hebt de klus geaccepteerd!', 'success')
        return redirect(url_for('main.mijn_gezochte_klussen'))
    except Exception as e:
        db.session.rollback()
        flash(f'Er is een fout opgetreden: {e}', 'danger')
        return redirect(url_for('main.klussen'))


@main.route('/mijn_geschiedenis')
def mijn_geschiedenis():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    aangeboden_klussen = Klus.query.filter(
        Klus.idnummer == user_id,
        Klus.status == 'voltooid',
        Klus.voltooid_op.isnot(None)
    ).order_by(Klus.voltooid_op.desc()).all()

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

    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze actie uit te voeren.', 'danger')
        return redirect(url_for('main.login'))
    
    user_id = session.get('user_id')
    if klus.idnummer != user_id:
        flash('Je hebt geen toestemming om deze actie uit te voeren.', 'danger')
        return redirect(url_for('main.mijn_aangeboden_klussen'))

    klus.status = 'voltooid'
    klus.voltooid_op = utc_to_plus_one(datetime.utcnow())
    db.session.commit()

    for zoeker in klus.klussen_zoekers:
        maak_melding(
            gebruiker_id=zoeker.idnummer,
            bericht=f"De klus '{klus.naam}' is gemarkeerd als voltooid. Je kunt nu een beoordeling nalaten."
        )

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

    form = RatingFormForZoeker()
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
            comment=form.comment.data,
            )
        db.session.add(new_rating)
        db.session.commit()

        maak_melding(
            gebruiker_id=klus.klussen_zoekers[0].idnummer,
            bericht=f"Je bent beoordeeld door de klusaanbieder voor de klus '{klus.naam}'."
        )

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

    if not any(zoeker.idnummer == session.get('user_id') for zoeker in klus.klussen_zoekers):
        flash('Je bent niet bevoegd om deze beoordeling te maken.', 'danger')
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
            comment=form.comment.data,
            created_at=utc_to_plus_one(datetime.utcnow())
            )
        db.session.add(new_rating)
        flash('Beoordeling succesvol toegevoegd!', 'success')
        db.session.commit()
        
        maak_melding(
            gebruiker_id=klus.idnummer,
            bericht=f"Je bent beoordeeld door de kluszoeker voor de klus '{klus.naam}'."
        )
        maak_melding(
            gebruiker_id=session.get('user_id'),
            bericht=f"Bedankt voor het achterlaten van een beoordeling voor de klusaanbieder van '{klus.naam}'."
        )

        return redirect(url_for('main.mijn_geschiedenis'))

    return render_template('rate_aanbieder.html', form=form, klus=klus)


@main.route('/ratings/<rol>/<idnummer>', methods=['GET'])
def ratings(rol, idnummer):
    back_url = request.args.get('back_url', url_for('main.dashboard'))
    
    if rol not in ['aanbieder', 'zoeker']:
        flash('Ongeldige rol opgegeven.', 'error')
        abort(404)

    persoon = Persoon.query.filter_by(idnummer=idnummer).first()
    if not persoon:
        flash('Persoon niet gevonden.', 'error')
        abort(404)

    if rol == 'aanbieder':
        ratings = Rating.query.filter_by(klusaanbieder_id=idnummer).order_by(Rating.created_at.desc()).all()
    elif rol == 'zoeker':
        ratings = Rating.query.filter_by(kluszoeker_id=idnummer).order_by(Rating.created_at.desc()).all()

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
    rating = Rating.query.get(rating_id)
    
    if not rating:
        abort(404, description="Rating not found")
    
    if rating.klusaanbieder_id:
        rol = 'aanbieder'
    elif rating.kluszoeker_id:
        rol = 'zoeker'
    else:
        rol = 'onbekend' 
    
    back_url = url_for('main.ratings', rol=rol, idnummer=rating.klusaanbieder_id)

    return render_template(
        'ratings_detail.html',
        rating=rating,
        rol=rol,
        back_url=back_url
    )


@main.route('/rating/zoeker/<int:rating_id>', methods=['GET'])
def ratings_detail_zoeker(rating_id):
    rating = Rating.query.get(rating_id)
    
    if not rating:
        abort(404, description="Rating not found")
    
    if rating.kluszoeker_id:
        rol = 'zoeker'
    elif rating.klusaanbieder_id:
        rol = 'aanbieder'
    else:
        rol = 'onbekend'
    
    back_url = url_for('main.beoordelingen_kluszoeker', rol=rol, idnummer=rating.kluszoeker_id, klusnummer=rating.klusnummer)

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
        laatste_vijf_meldingen = Notificatie.query.filter_by(
            gebruiker_id=session['user_id']
        ).order_by(Notificatie.aangemaakt_op.desc()).limit(5).all()

        aantal_ongelezen = Notificatie.query.filter_by(
            gebruiker_id=session['user_id'], gelezen=False
        ).count()

        return {
            'notificaties': laatste_vijf_meldingen,
            'aantal_ongelezen_meldingen': aantal_ongelezen
        }
    return {
        'notificaties': [],
        'aantal_ongelezen_meldingen': 0
    }




@main.route('/meldingen', methods=['GET'])
def alle_meldingen():
    if 'user_id' not in session:
        flash("Je moet ingelogd zijn om meldingen te bekijken.", "warning")
        return redirect(url_for('main.login'))

    alle_meldingen = Notificatie.query.filter_by(
        gebruiker_id=session['user_id']
    ).order_by(Notificatie.aangemaakt_op.desc()).all()

    return render_template('alle_meldingen.html', meldingen=alle_meldingen)


@main.route('/beoordelingen/<string:klusnummer>', methods=['GET'])
def beoordelingen_kluszoeker(klusnummer):
    klus = Klus.query.filter_by(klusnummer=klusnummer).first()
    
    if not klus:
        flash("De gevraagde klus bestaat niet.", "danger")
        return redirect(url_for('main.home'))

    kluszoeker = klus.klussen_zoekers[0] if klus.klussen_zoekers else None
    
    if not kluszoeker:
        flash("Er zijn geen kluszoekers gekoppeld aan deze klus.", "warning")
        return redirect(url_for('main.home'))

    ratings = Rating.query.filter_by(kluszoeker_id=kluszoeker.idnummer).order_by(Rating.created_at.desc()).all()

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
