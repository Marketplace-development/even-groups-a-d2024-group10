from datetime import datetime, date
from . import db
import uuid
import requests
from sqlalchemy.orm import validates


def generate_id_number():
    return str(uuid.uuid4().int)[:10]

klus_zoeker = db.Table('klus_zoeker',
    db.Column('klusnummer', db.String(36), db.ForeignKey('klus.klusnummer'), primary_key=True),
    db.Column('idnummer', db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
)

class Persoon(db.Model):
    __tablename__ = 'persoon'

    idnummer = db.Column(db.String(10), primary_key=True, default=generate_id_number)
    voornaam = db.Column(db.String(100), nullable=False)
    achternaam = db.Column(db.String(100))
    geboortedatum = db.Column(db.Date, nullable=False)
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

    @validates('geboortedatum')
    def update_leeftijd(self, key, value):
        today = date.today()
        self.leeftijd = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        return value
    

    def gemiddelde_score_aanbieder(self):
        ratings = Rating.query.filter(
            Rating.klusaanbieder_id == self.idnummer,
            Rating.vriendelijkheid_aanbieder.isnot(None),
            Rating.gastvrijheid.isnot(None),
            Rating.betrouwbaarheid.isnot(None),
            Rating.communicatie_aanbieder.isnot(None),
            Rating.algemene_ervaring_aanbieder.isnot(None)
        ).all()

        if not ratings:
            return 0.0

        totaal_score = 0
        aantal_ratings = 0

        for r in ratings:
            score = sum([
                r.vriendelijkheid_aanbieder,
                r.gastvrijheid,
                r.betrouwbaarheid,
                r.communicatie_aanbieder,
                r.algemene_ervaring_aanbieder
            ]) / 5
            totaal_score += score
            aantal_ratings += 1

        return round(totaal_score / aantal_ratings, 1)



    def gemiddelde_score_zoeker(self):
        ratings = (
            Rating.query
            .filter_by(kluszoeker_id=self.idnummer)
            .filter(Rating.vriendelijkheid_zoeker.isnot(None))
            .all()
        )
        if not ratings:
            return 0.0

        totaal_score = 0
        aantal_ratings = 0

        for r in ratings:
            score = sum([
                r.vriendelijkheid_zoeker or 0,
                r.tijdigheid or 0,
                r.kwaliteit or 0,
                r.communicatie_zoeker or 0,
                r.algemene_ervaring_zoeker or 0
            ]) / 5
            totaal_score += score
            aantal_ratings += 1

        return round(totaal_score / aantal_ratings, 1)



    
class Klusaanbieder(db.Model):
    _tablename_ = 'klusaanbieder'
    
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
    rating = db.Column(db.Numeric(3, 2))
    categorie = db.Column(db.String(50))
    beschikbaarheid = db.Column(db.String(100))
    
    persoon = db.relationship('Persoon', backref='klusaanbieders_rel')

    def __repr__(self):
        return f'<Klusaanbieder {self.idnummer}>'

class Kluszoeker(db.Model):
    _tablename_ = 'kluszoeker'
    
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), primary_key=True)
    rating = db.Column(db.Numeric(3, 2))
    aantal_klussen = db.Column(db.Integer)
    categorie = db.Column(db.String(50))
    
    persoon = db.relationship('Persoon', backref='kluszoekers_rel')

    def __repr__(self):
        return f'<Kluszoeker {self.idnummer}>'

class Klus(db.Model):
    __tablename__ = 'klus'

    klusnummer = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    naam = db.Column(db.String(100), nullable=False)
    beschrijving = db.Column(db.Text, nullable=False)
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=False)
    locatie = db.Column(db.String(200), nullable=False)
    tijd = db.Column(db.Time, nullable=False)
    vergoeding = db.Column(db.Numeric(10, 2), nullable=False)
    datum = db.Column(db.Date, nullable=False)
    verwachte_duur = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default='beschikbaar', nullable=False)
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    voltooid_op = db.Column(db.DateTime, nullable=True)
    
    persoon_aanbieder = db.relationship(
        'Persoon', 
        foreign_keys=[idnummer],
        backref=db.backref('klussen', lazy=True)
    )

    klussen_zoekers = db.relationship(
        'Persoon', 
        secondary=klus_zoeker, 
        backref=db.backref('geinteresseerd_in_klussen', lazy='dynamic')
    )
    
    categorie_ref = db.relationship('Categorie', backref='klussen', lazy=True)

    
    def is_gewaardeerd_door_aanbieder(self):
        return any(r.vriendelijkheid_zoeker is not None for r in self.ratings)

    def is_gewaardeerd_door_zoeker(self):
        return any(r.vriendelijkheid_aanbieder is not None for r in self.ratings)
    
    def __repr__(self):
        return f'<Klus {self.klusnummer} voor {self.locatie}>'
    

class Categorie(db.Model):
    __tablename__ = 'categorie'

    categorie = db.Column(db.String(50), primary_key=True)
    naam = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Categorie {self.categorie}>'


class Rating(db.Model):
    __tablename__ = 'rating'

    id = db.Column(db.Integer, primary_key=True)
    klusnummer = db.Column(db.String(36), db.ForeignKey('klus.klusnummer'), nullable=False)
    
    kluszoeker_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=True)
    vriendelijkheid_zoeker = db.Column(db.Integer, nullable=True)
    tijdigheid = db.Column(db.Integer, nullable=True)
    kwaliteit = db.Column(db.Integer, nullable=True)
    communicatie_zoeker = db.Column(db.Integer, nullable=True)
    algemene_ervaring_zoeker = db.Column(db.Integer, nullable=True)

    klusaanbieder_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=True)
    vriendelijkheid_aanbieder = db.Column(db.Integer, nullable=True)
    gastvrijheid = db.Column(db.Integer, nullable=True)
    betrouwbaarheid = db.Column(db.Integer, nullable=True)
    communicatie_aanbieder = db.Column(db.Integer, nullable=True)
    algemene_ervaring_aanbieder = db.Column(db.Integer, nullable=True)

    comment = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    klus = db.relationship('Klus', backref='ratings')
    kluszoeker = db.relationship('Persoon', foreign_keys=[kluszoeker_id], backref='zoeker_ratings')
    klusaanbieder = db.relationship('Persoon', foreign_keys=[klusaanbieder_id], backref='aanbieder_ratings')

    def __repr__(self):
        return f'<Rating {self.id} - Klusnummer {self.klusnummer}>'




class CategorieStatistiek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idnummer = db.Column(db.String(10), db.ForeignKey('persoon.idnummer', ondelete='CASCADE'), nullable=False)
    categorie = db.Column(db.String(50), db.ForeignKey('categorie.categorie'), nullable=False)
    aantal_accepteerd = db.Column(db.Integer, default=0)

    persoon = db.relationship('Persoon', backref='categorie_statistieken', lazy=True)
    categorie_ref = db.relationship('Categorie', backref='gebruikers_statistieken', lazy=True)



class Bericht(db.Model):
    __tablename__ = 'bericht'

    id = db.Column(db.Integer, primary_key=True)
    afzender_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    ontvanger_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    klusnummer = db.Column(db.String(36), db.ForeignKey('klus.klusnummer'), nullable=True)
    inhoud = db.Column(db.Text, nullable=False)
    verzonden_op = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)
    gelezen = db.Column(db.Boolean, default=False)

    afzender = db.relationship('Persoon', foreign_keys=[afzender_id], backref='verzonden_berichten')
    ontvanger = db.relationship('Persoon', foreign_keys=[ontvanger_id], backref='ontvangen_berichten')
    klus = db.relationship('Klus', backref=db.backref('berichten', lazy=True))

    def __repr__(self):
        return f'<Bericht {self.id} van {self.afzender_id} naar {self.ontvanger_id}>'

def valideer_adres(adres):
    key = 'ac72d275a2624c1fb3b6d4fa964d89b7'
    url = f'https://api.opencagedata.com/geocode/v1/json?q={adres}&key={key}'
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        if data['results']:
            return True
        else:
            return False
    else:
        return False


class Notificatie(db.Model):
    __tablename__ = 'notificatie'

    id = db.Column(db.Integer, primary_key=True)
    gebruiker_id = db.Column(db.String(10), db.ForeignKey('persoon.idnummer'), nullable=False)
    bericht = db.Column(db.String(255), nullable=False)
    gelezen = db.Column(db.Boolean, default=False)
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)

    gebruiker = db.relationship('Persoon', backref='notificaties')

    def __repr__(self):
        return f'<Notificatie {self.id} - {self.bericht}>'
