from datetime import datetime
from . import db  # Gebruik de geïmporteerde instantie van SQLAlchemy
import uuid
from flask_login import current_user
from sqlalchemy import CheckConstraint
from flask_login import UserMixin



# Functie om een ID-nummer te genereren
def generate_id_number():
    return str(uuid.uuid4().int)[:10]  # 10 cijfers van een UUID

# Tussenliggende tabel voor de veel-op-veel-relatie tussen Klus en Persoon (Kluszoeker)
klus_zoeker = db.Table('klus_zoeker',
    db.Column('klusnummer', db.String(36), db.ForeignKey('klus.klusnummer'), primary_key=True),
    db.Column('idnummer', db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
)

# Persoon Model
class Persoon(db.Model, UserMixin):
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
    is_active_flag = db.Column(db.Boolean, default=True)  # Bijvoorbeeld een vlag die aangeeft of een gebruiker actief is

    def get_id(self):
        return str(self.idnummer)

    def is_active(self):
        return self.is_active_flag  # Deze methode moet `True` of `False` teruggeven

    def gemiddelde_score(self):
        ratings = Rating.query.filter(
            (Rating.kluszoeker_id == self.idnummer) | (Rating.klusaanbieder_id == self.idnummer)
        ).all()

        if not ratings:
            return 'Geen beoordelingen'

        total_score = sum(
            r.rating_zoeker + r.rating_aanbieder for r in ratings
        )
        aantal_cijfers = len(ratings) * 2
        return round(total_score / aantal_cijfers, 2)


# Klusaanbieder Model
class Klusaanbieder(db.Model):
    _tablename_ = 'klusaanbieder'
    
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
    rating = db.Column(db.Numeric(3, 2))
    categorie = db.Column(db.String(50))
    beschikbaarheid = db.Column(db.String(100))
    
    persoon = db.relationship('Persoon', backref='klusaanbieders_rel')

    def __repr__(self):
        return f'<Klusaanbieder {self.idnummer}>'

# Kluszoeker Model
class Kluszoeker(db.Model):
    _tablename_ = 'kluszoeker'
    
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
    rating = db.Column(db.Numeric(3, 2))
    aantal_klussen = db.Column(db.Integer)
    categorie = db.Column(db.String(50))
    
    persoon = db.relationship('Persoon', backref='kluszoekers_rel')

    def __repr__(self):
        return f'<Kluszoeker {self.idnummer}>'

# Klus Model
class Klus(db.Model):
    _tablename_ = 'klus'
    
    klusnummer = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    naam = db.Column(db.String(100), nullable=False)
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie', ondelete="SET NULL"), nullable=True)
    locatie = db.Column(db.String(100))
    tijd = db.Column(db.Time, nullable=False)
    beschrijving = db.Column(db.Text)
    vergoeding = db.Column(db.Numeric(10, 2))
    datum = db.Column(db.Date, nullable=False)
    verwachte_duur = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='beschikbaar')  # Status: beschikbaar, geaccepteerd, completed
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)

    persoon_aanbieder = db.relationship('Persoon', backref=db.backref('klussen', lazy=True))
    klussen_zoekers = db.relationship(
        'Persoon', 
        secondary=klus_zoeker, 
        backref=db.backref('geinteresseerd_in_klussen', lazy='dynamic'))
    categorie_ref = db.relationship('Categorie', backref='klussen', lazy=True)

    def __repr__(self):
        return f'<Klus {self.klusnummer} voor {self.locatie}>'

    
    # Relatie met klussenzoekers (via de tussen tabel)
    klussen_zoekers = db.relationship(
        'Persoon', 
        secondary=klus_zoeker, 
        backref=db.backref('geinteresseerd_in_klussen', lazy='dynamic')
    )

    # Relatie naar Categorie (via ForeignKey 'categorie')
    categorie_ref = db.relationship('Categorie', backref='klussen', lazy=True)

    def __repr__(self):
        return f'<Klus {self.klusnummer} voor {self.locatie}>'
    
class Categorie(db.Model):
    __tablename__ = 'categorie'  # Correcte naamgeving

    categorie = db.Column(db.String(50), primary_key=True)  # Unieke identificatie
    naam = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Categorie {self.categorie}>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    klusnummer = db.Column(db.String(36), db.ForeignKey('klus.klusnummer'), nullable=False)
    kluszoeker_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    klusaanbieder_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    communicatie = db.Column(db.Integer, nullable=False)  # Cijfer op 10
    betrouwbaarheid = db.Column(db.Integer, nullable=False)  # Cijfer op 10
    tijdigheid = db.Column(db.Integer, nullable=False)  # Cijfer op 10
    kwaliteit = db.Column(db.Integer, nullable=False)  # Cijfer op 10
    algemene_ervaring = db.Column(db.Integer, nullable=False)  # Cijfer op 10
    comment = db.Column(db.String(500), nullable=True)  # Optioneel commentaar
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relaties
    klus = db.relationship('Klus', backref=db.backref('ratings', lazy=True))
    kluszoeker = db.relationship('Persoon', foreign_keys=[kluszoeker_id])
    klusaanbieder = db.relationship('Persoon', foreign_keys=[klusaanbieder_id])

    def __repr__(self):
        return f'<Rating {self.id}>'



class CategorieStatistiek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer', ondelete='CASCADE'), nullable=False)
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=False)
    aantal_accepteerd = db.Column(db.Integer, default=0)

    persoon = db.relationship('Persoon', backref='categorie_statistieken', lazy=True)
    categorie_ref = db.relationship('Categorie', backref='gebruikers_statistieken', lazy=True)



#chat functie
class Bericht(db.Model):
    __tablename__ = 'bericht'

    id = db.Column(db.Integer, primary_key=True)
    afzender_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    ontvanger_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    klusnummer = db.Column(db.String(36), db.ForeignKey('klus.klusnummer'), nullable=True)
    inhoud = db.Column(db.Text, nullable=False)
    verzonden_op = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    # Relaties
    afzender = db.relationship('Persoon', foreign_keys=[afzender_id], backref='verzonden_berichten')
    ontvanger = db.relationship('Persoon', foreign_keys=[ontvanger_id], backref='ontvangen_berichten')
    klus = db.relationship('Klus', backref=db.backref('berichten', lazy=True))

    def __repr__(self):
        return f'<Bericht {self.id} van {self.afzender_id} naar {self.ontvanger_id}>'
