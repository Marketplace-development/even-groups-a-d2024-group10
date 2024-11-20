from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Email, Length

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
    idnummer = StringField('IDnummer', validators=[DataRequired()])
    rating = DecimalField('Rating', validators=[DataRequired()])
    categorie = StringField('Categorie', validators=[DataRequired()])  # Bijv. 'Elektronica'
    submit = SubmitField('Toevoegen')


class KluszoekerForm(FlaskForm):
    idnummer = StringField('ID Nummer', validators=[DataRequired()])
    rating = DecimalField('Rating', validators=[DataRequired()])
    aantal_klussen = IntegerField('Aantal Klussen', validators=[DataRequired()])
    categorie = StringField('Categorie', validators=[DataRequired()])
    submit = SubmitField('Toevoegen')


class RegistrationForm(FlaskForm):
    username_or_email = StringField('Gebruikersnaam', validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Registreren')

# Formulier voor inloggen (alleen gebruikersnaam)
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Login')

class KlusForm(FlaskForm):
    titel = StringField('Titel', validators=[DataRequired()])
    omschrijving = StringField('Omschrijving', validators=[DataRequired()])
    categorie = StringField('Categorie', validators=[DataRequired()])
    prijs = DecimalField('Prijs', validators=[DataRequired()])  # Gebruik DecimalField voor prijs
    locatie = StringField('Locatie', validators=[DataRequired()])
    submit = SubmitField('Toevoegen')



