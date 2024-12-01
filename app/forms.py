from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, DecimalField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, NumberRange, InputRequired
import random
import string

# Functie om een 10-cijferig ID-nummer te genereren
def generate_id_number():
    return ''.join(random.choices(string.digits, k=10))

class PersoonForm(FlaskForm):
    voornaam = StringField('Voornaam', validators=[DataRequired()])
    achternaam = StringField('Achternaam', validators=[DataRequired()])
    leeftijd = IntegerField('Leeftijd', validators=[DataRequired()])
    adres = StringField('Adres', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    tel_nr = StringField('Telefoonnummer', validators=[DataRequired(), Length(max=15)])
    voorkeur_categorie = StringField('Voorkeur Categorie', validators=[DataRequired()])
    submit = SubmitField('Toevoegen')

class KlusaanbiederForm(FlaskForm):
    naam = StringField('Naam van de klus', validators=[DataRequired()])
    
    # Categorie selectie
    categorie = SelectField('Categorie', choices=[('buitenshuis', 'Buitenshuis'), 
                                                  ('binnenshuis', 'Binnenshuis'),
                                                  ('tuin', 'Tuin'),
                                                  ('techniek', 'Techniek')], 
                            validators=[DataRequired()])
    
    # Tijd: bijvoorbeeld van 09:00 tot 12:00
    tijd = StringField('Verwachte tijd (bijv. 09:00 - 12:00)', validators=[DataRequired()])
    
    # Locatie: meer specifiek een adres
    locatie = StringField('Locatie', validators=[DataRequired()])
    
    beschrijving = TextAreaField('Beschrijving', validators=[DataRequired()])
    vergoeding = DecimalField('Vergoeding', places=2, rounding=None, validators=[DataRequired()])
    
    # Nieuwe velden
    datum = DateField('Datum van de klus', validators=[DataRequired()])
    verwachte_duur = IntegerField('Verwachte tijdsduur in uren', validators=[DataRequired()])


class KluszoekerForm(FlaskForm):
    idnummer = StringField('ID Nummer', validators=[DataRequired()])
    rating = DecimalField('Rating', validators=[DataRequired()])
    aantal_klussen = IntegerField('Aantal Klussen', validators=[DataRequired()])
    categorie = StringField('Categorie', validators=[DataRequired()])
    submit = SubmitField('Toevoegen')

class RegistrationForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    voornaam = StringField('Voornaam', validators=[DataRequired()])
    achternaam = StringField('Achternaam', validators=[DataRequired()])
    leeftijd = IntegerField('Leeftijd', validators=[InputRequired(), NumberRange(min=18, max=100)])
    gender = StringField('Geslacht')
    telefoonnummer = StringField('Telefoonnummer')
    adres = StringField('Adres')
    submit = SubmitField('Registeren')

# Formulier voor inloggen (alleen gebruikersnaam)
class LoginForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators=[DataRequired()])
    submit = SubmitField('Login')

class KlusForm(FlaskForm):
    naam = StringField('Naam van de klus', validators=[DataRequired()])  # Nieuw veld voor de naam van de klus
    beschrijving = StringField('Behrijving', validators=[DataRequired()])
    categorie = StringField('Categorie', validators=[DataRequired()])
    prijs = DecimalField('Prijs', validators=[DataRequired()])  # Gebruik DecimalField voor prijs
    locatie = StringField('Locatie', validators=[DataRequired()])
    tijd = StringField('Tijd', validators=[DataRequired()])  # Nieuw veld voor tijd
    vergoeding = StringField('Vergoeding', validators=[DataRequired()])
    submit = SubmitField('Toevoegen')
