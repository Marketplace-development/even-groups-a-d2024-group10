from flask import Blueprint, render_template, redirect, url_for, flash, session
from app import db
from app.models import Persoon, Klusaanbieder, Kluszoeker
from app.forms import PersoonForm, KlusaanbiederForm, KluszoekerForm, RegistrationForm, LoginForm
import os

# Maak een blueprint
main = Blueprint('main', __name__)

# Route voor de startpagina
@main.route('/')
def home():
    return render_template('index.html')  # Zorg ervoor dat dit verwijst naar een daadwerkelijke HTML-pagina

# Route voor registratiepagina
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username_or_email.data
        flash(f'Welkom {username}, je bent succesvol geregistreerd!', 'success')
        
        # Sla de gebruikersnaam op in de sessie
        session['username'] = username
        
        return redirect(url_for('main.dashboard'))  # Gebruiker wordt doorgestuurd naar het dashboard

    return render_template('register.html', form=form)

# Route voor loginpagina
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        flash(f'Inloggen succesvol voor {username}!', 'success')
        session['user'] = username  # Gebruiker opslaan in de sessie
        return redirect(url_for('main.dashboard'))  # Redirect naar dashboard
    return render_template('login.html', form=form)

# Route voor dashboard (na succesvol inloggen)
@main.route('/dashboard')
def dashboard():
    # Controleer of de gebruiker ingelogd is via de sessie
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    username = session['user']
    return render_template('dashboard.html', username=username)


# Route voor het profiel (weergeven van gebruikersgegevens)
@main.route('/profile/<username>')
def profile(username):
    # Controleer of de gebruiker is ingelogd
    if 'user' not in session:
        flash('Je moet eerst inloggen om je profiel te bekijken.', 'warning')
        return redirect(url_for('main.login'))
    
    # Probeer de gegevens van de persoon op te halen
    person = Persoon.query.filter_by(IDnummer=username).first()
    
    if person:
        # Als persoon bestaat, haal dan de klusaanbieder/zoeker op
        klusaanbieder = Klusaanbieder.query.filter_by(IDnummer=username).first()
        kluszoeker = Kluszoeker.query.filter_by(IDnummer=username).first()
        
        return render_template('profile.html', person=person, klusaanbieder=klusaanbieder, kluszoeker=kluszoeker)
    else:
        flash('Profiel niet gevonden.', 'danger')
        return redirect(url_for('main.home'))


# Route voor afmelden (logout)
@main.route('/logout')
def logout():
    # Verwijder de gebruiker uit de sessie
    session.pop('user', None)
    flash('Je bent uitgelogd.', 'success')
    return redirect(url_for('main.home'))

# Route voor het toevoegen van een persoon (voorbeeld)
@main.route('/add_person', methods=['GET', 'POST'])
def add_person():
    form = PersoonForm()
    if form.validate_on_submit():
        new_person = Persoon(
            IDnummer='1234567890',  # Dit kan dynamisch zijn
            Voornaam=form.voornaam.data,
            Achternaam=form.achternaam.data,
            Leeftijd=form.leeftijd.data,
            Adres=form.adres.data,
            Email=form.email.data,
            Tel_nr=form.tel_nr.data,
            Voorkeur_categorie=form.voorkeur_categorie.data
        )
        db.session.add(new_person)
        db.session.commit()
        flash(f'Persoon {new_person.Voornaam} {new_person.Achternaam} is toegevoegd!', 'success')
        return redirect(url_for('main.profile', username=new_person.IDnummer))
    return render_template('add_person.html', form=form)


# Route voor het toevoegen van een klusaanbieder#
@main.route('/add_klusaanbieder', methods=['GET', 'POST'])
def add_klusaanbieder():
    form = KlusaanbiederForm()
    if form.validate_on_submit():
        # Voeg klusaanbieder toe
        new_klusaanbieder = Klusaanbieder(
            IDnummer=form.idnummer.data,
            Rating=form.rating.data,
            categorie=form.categorie.data
        )
        db.session.add(new_klusaanbieder)
        db.session.commit()
        flash(f'Klusaanbieder {new_klusaanbieder.IDnummer} is toegevoegd!', 'success')

        # Redirect naar de klusaanbiedingen pagina waar ze klussen kunnen toevoegen
        return redirect(url_for('main.add_klus', username=new_klusaanbieder.IDnummer))
    
    return render_template('add_klusaanbieder.html', form=form)

# Route voor het toevoegen van een kluszoeker
@main.route('/add_kluszoeker', methods=['GET', 'POST'])
def add_kluszoeker():
    form = KluszoekerForm()
    if form.validate_on_submit():
        new_kluszoeker = Kluszoeker(
            IDnummer=form.idnummer.data,
            Rating=form.rating.data,
            Aantal_klussen=form.aantal_klussen.data,
            categorie=form.categorie.data
        )
        db.session.add(new_kluszoeker)
        db.session.commit()
        return redirect(url_for('main.profile', username=new_kluszoeker.IDnummer))
    
    # Voeg een flash bericht toe als het formulier niet geldig is
    flash('Er is iets mis met het formulier. Controleer je gegevens.', 'danger')
    return render_template('add_kluszoeker.html', form=form)


"hallo"