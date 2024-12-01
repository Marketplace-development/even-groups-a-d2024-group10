from datetime import datetime
from . import db  # Gebruik de geïmporteerde instantie van SQLAlchemy
import uuid
from flask_login import current_user
from sqlalchemy import CheckConstraint

# Functie om een ID-nummer te genereren
def generate_id_number():
    return str(uuid.uuid4().int)[:10]  # 10 cijfers van een UUID

# Tussenliggende tabel voor de veel-op-veel-relatie tussen Klus en Persoon (Kluszoeker)
klus_zoeker = db.Table('klus_zoeker',
    db.Column('klusnummer', db.String(36), db.ForeignKey('klus.klusnummer'), primary_key=True),
    db.Column('idnummer', db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
)

# Persoon Model
class Persoon(db.Model):
    __tablename__ = 'persoon'
    
    idnummer = db.Column(db.String(10), primary_key=True, default=generate_id_number)
    voornaam = db.Column(db.String(100), nullable=False)
    achternaam = db.Column(db.String(100))
    leeftijd = db.Column(db.SmallInteger)
    geslacht = db.Column(db.String(10))
    adres = db.Column(db.String(255))
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    telefoonnummer = db.Column(db.String(15))
    username = db.Column(db.String(20), nullable=False, unique=True, index=True)
    
    voorkeur_categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    voorkeur_categorie_rel = db.relationship('Categorie', backref='personen', lazy=True)

    klusaanbieders = db.relationship('Klusaanbieder', backref='persoon_aanbieder', lazy='joined')
    kluszoekers = db.relationship('Kluszoeker', backref='persoon_zoeker', lazy='joined')

    def __repr__(self):
        return f'<Persoon {self.voornaam} {self.achternaam}>'

# Klusaanbieder Model
class Klusaanbieder(db.Model):
    __tablename__ = 'klusaanbieder'
    
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
    rating = db.Column(db.Numeric(3, 2))
    categorie = db.Column(db.String(50))
    beschikbaarheid = db.Column(db.String(100))
    
    persoon = db.relationship('Persoon', backref='klusaanbieders_rel')

    def __repr__(self):
        return f'<Klusaanbieder {self.idnummer}>'


# Kluszoeker Model
class Kluszoeker(db.Model):
    __tablename__ = 'kluszoeker'
    
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
    rating = db.Column(db.Numeric(3, 2))
    aantal_klussen = db.Column(db.Integer)
    categorie = db.Column(db.String(50))
    
    persoon = db.relationship('Persoon', backref='kluszoekers_rel')

    def __repr__(self):
        return f'<Kluszoeker {self.idnummer}>'

# Klus Model
class Klus(db.Model):
    __tablename__ = 'klus'
    
    klusnummer = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # automatisch UUID
    naam = db.Column(db.String(100), nullable=False)  # Voeg de naam kolom toe, dit is de titel van de klus
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie', ondelete="SET NULL"), nullable=True)
    locatie = db.Column(db.String(100))  # Locatie van de klus
    tijd = db.Column(db.String(50))  # Verwachte tijd
    beschrijving = db.Column(db.Text)  # Beschrijving van de klus
    vergoeding = db.Column(db.Numeric(10, 2))  # Vergoeding in € (numeriek)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)  # Tijdstip van toevoegen
    status = db.Column(db.String(20), default='beschikbaar')  # Status van de klus (beschikbaar, bekeken, geaccepteerd)
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)  # Verwijzing naar de aanbieder
    datum = db.Column(db.Date)  # Datum van de klus
    verwachte_duur = db.Column(db.Integer)  # Verwachte duur in uren

    persoon_aanbieder = db.relationship('Persoon', backref=db.backref('klussen', lazy=True))
    klussen_zoekers = db.relationship('Persoon', secondary=klus_zoeker, backref=db.backref('geinteresseerd_in_klussen', lazy='dynamic'))
    categorie_ref = db.relationship('Categorie', backref='klussen', lazy=True)

    def __repr__(self):
        return f'<Klus {self.naam} voor {self.locatie}>'


# Categorie Model
class Categorie(db.Model):
    __tablename__ = 'categorie'
    
    categorie = db.Column(db.String(50), primary_key=True)
    naam = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Categorie {self.categorie}>'
