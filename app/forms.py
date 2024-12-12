from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, DecimalField, DateField, TextAreaField, SelectField, TimeField
from wtforms.validators import DataRequired, Email, Length, NumberRange, InputRequired, Optional
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

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, DecimalField, DateField, TextAreaField, SelectField, TimeField
from wtforms.validators import DataRequired, Length, NumberRange

class KlusaanbiederForm(FlaskForm):
    naam = StringField('Naam van de klus', validators=[DataRequired()])
    categorie = SelectField('Categorie', choices=[
        ('buitenshuis', 'Buitenshuis'), 
        ('binnenshuis', 'Binnenshuis'),
        ('tuin', 'Tuin'),
        ('techniek', 'Techniek'),
        ('oppassen', 'Oppassen'),
        ('boodschappen', 'Boodschappen doen'),
        ('schoonmaak', 'Schoonmaak'),
        ('verhuis', 'Verhuizen'),
        ('hulp_thuis', 'Hulp thuis'),
        ('administratie', 'Administratie'),
        ('zorg', 'Zorg & Verzorging')
    ], validators=[DataRequired()])
    locatie = StringField('Locatie', validators=[DataRequired(), Length(max=100)])
    uren = SelectField('Uur', choices=[(str(i), f'{i:02}') for i in range(0, 24)], coerce=int, validators=[DataRequired()])
    minuten = SelectField('Minuut', choices=[('00', '00'), ('15', '15'), ('30', '30'), ('45', '45')], validators=[DataRequired()])
    beschrijving = TextAreaField('Beschrijving', validators=[DataRequired()])
    vergoeding = DecimalField('Vergoeding', places=2, validators=[DataRequired()])  # Decimal voor geld
    datum = DateField('Datum', format='%Y-%m-%d', validators=[DataRequired()])  # Datum als DATE
    verwachte_duur = IntegerField('Verwachte duur (in uren)', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Toevoegen')

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
    gender = SelectField('Geslacht', choices=[('', 'Selecteer'), ('Man', 'Man'), ('Vrouw', 'Vrouw'), ('Andere', 'Andere')])
    telefoonnummer = StringField('Telefoonnummer', validators=[
        DataRequired(),
        Length(min=10, max=15, message='Telefoonnummer moet tussen 10 en 15 cijfers zijn.')
    ])
    adres = StringField('Adres', validators=[DataRequired()])
    submit = SubmitField('Registeren')


# Formulier voor inloggen (alleen gebruikersnaam)
class LoginForm(FlaskForm):
    username = StringField('Gebruikersnaam', validators=[DataRequired()])
    submit = SubmitField('Login')


class RatingForm(FlaskForm):
    communicatie = IntegerField('Communicatie', validators=[DataRequired()])
    communicatie_comment = StringField('Commentaar over Communicatie', validators=[Optional()])
    betrouwbaarheid = IntegerField('Betrouwbaarheid', validators=[DataRequired()])
    betrouwbaarheid_comment = StringField('Commentaar over Betrouwbaarheid', validators=[Optional()])
    tijdigheid = IntegerField('Tijdigheid', validators=[DataRequired()])
    tijdigheid_comment = StringField('Commentaar over Tijdigheid', validators=[Optional()])
    kwaliteit = IntegerField('Kwaliteit', validators=[DataRequired()])
    kwaliteit_comment = StringField('Commentaar over Kwaliteit', validators=[Optional()])
    algemene_ervaring = IntegerField('Algemene Ervaring', validators=[DataRequired()])
    algemene_ervaring_comment = StringField('Commentaar over Algemene Ervaring', validators=[Optional()])
    submit = SubmitField('Indienen')


class RatingFormForZoeker(FlaskForm):
    vriendelijkheid = IntegerField('Vriendelijkheid', validators=[DataRequired()])
    vriendelijkheid_comment = StringField('Commentaar over Vriendelijkheid', validators=[Optional()])
    tijdigheid = IntegerField('Tijdigheid', validators=[DataRequired()])
    tijdigheid_comment = StringField('Commentaar over Tijdigheid', validators=[Optional()])
    kwaliteit = IntegerField('Kwaliteit', validators=[DataRequired()])
    kwaliteit_comment = StringField('Commentaar over Kwaliteit', validators=[Optional()])
    communicatie = IntegerField('Communicatie', validators=[DataRequired()])
    communicatie_comment = StringField('Commentaar over Communicatie', validators=[Optional()])
    algemene_ervaring = IntegerField('Algemene Ervaring', validators=[DataRequired()])
    algemene_ervaring_comment = StringField('Commentaar over Algemene Ervaring', validators=[Optional()])
    submit = SubmitField('Indienen')


class RatingFormForAanbieder(FlaskForm):
    vriendelijkheid = IntegerField('Vriendelijkheid', validators=[DataRequired()])
    vriendelijkheid_comment = StringField('Commentaar over Vriendelijkheid', validators=[Optional()])
    gastvrijheid = IntegerField('Gastvrijheid', validators=[DataRequired()])
    gastvrijheid_comment = StringField('Commentaar over Gastvrijheid', validators=[Optional()])
    betrouwbaarheid = IntegerField('Betrouwbaarheid', validators=[DataRequired()])
    betrouwbaarheid_comment = StringField('Commentaar over Betrouwbaarheid', validators=[Optional()])
    communicatie = IntegerField('Communicatie', validators=[DataRequired()])
    communicatie_comment = StringField('Commentaar over Communicatie', validators=[Optional()])
    algemene_ervaring = IntegerField('Algemene Ervaring', validators=[DataRequired()])
    algemene_ervaring_comment = StringField('Commentaar over Algemene Ervaring', validators=[Optional()])
    submit = SubmitField('Indienen')
