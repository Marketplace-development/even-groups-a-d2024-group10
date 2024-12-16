# app/chat.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import Klus, Persoon, Bericht
from app import db
from flask import Blueprint, jsonify, request, session
from app.models import Klus, Bericht, db
from datetime import datetime
chat = Blueprint('chat', __name__, url_prefix='/chat')
    
@chat.route('/<klusnummer>', methods=['GET', 'POST'])
def chat_page(klusnummer):
    user_id = session.get('user_id')
    if not user_id:
        flash("Je moet ingelogd zijn om deze pagina te bekijken.", "danger")
        return redirect(url_for('main.login'))

    # Haal de klus en berichten op
    klus = Klus.query.get_or_404(klusnummer)
    berichten = Bericht.query.filter_by(klusnummer=klusnummer).order_by(Bericht.verzonden_op).all()

    # Controleer of de gebruiker deel uitmaakt van de klus
    if user_id != klus.idnummer and user_id not in [zoeker.idnummer for zoeker in klus.klussen_zoekers]:
        flash("Je hebt geen toegang tot deze chat.", "danger")
        return redirect(url_for('main.dashboard'))

    # Markeer de berichten als gelezen voor de ingelogde gebruiker
    for bericht in berichten:
        if bericht.ontvanger_id == user_id and not bericht.gelezen:
            bericht.gelezen = True
    db.session.commit()

    # Ontvanger bepalen
    if klus.idnummer == user_id:
        ontvanger = klus.klussen_zoekers[0] if klus.klussen_zoekers else None
    else:
        ontvanger = klus.persoon_aanbieder

    if ontvanger is None:
        flash("Geen ontvanger gevonden voor deze klus.", "danger")
        return redirect(url_for('main.dashboard'))

    # Verwerk POST (nieuw bericht)
    if request.method == 'POST':
        inhoud = request.form.get('inhoud')
        if inhoud:
            nieuw_bericht = Bericht(
                afzender_id=user_id,
                ontvanger_id=ontvanger.idnummer,
                klusnummer=klusnummer,
                inhoud=inhoud
            )
            db.session.add(nieuw_bericht)
            db.session.commit()
            flash("Bericht verzonden!", "success")
            return redirect(url_for('chat.chat_page', klusnummer=klusnummer))

    # Render de chatpagina
    return render_template('chat.html', klus=klus, berichten=berichten, ontvanger=ontvanger)



@chat.route('/mijn_chats', methods=['GET', 'POST'])
def mijn_chats():
    user_id = session.get('user_id')
    if not user_id:
        flash('Je moet ingelogd zijn om deze pagina te bekijken.', 'danger')
        return redirect(url_for('main.login'))

    # Bericht verzenden via POST
    if request.method == 'POST':
        klusnummer = request.form.get('klusnummer')
        inhoud = request.form.get('inhoud')

        if klusnummer and inhoud:
            # Haal de klus op
            klus = Klus.query.filter_by(klusnummer=klusnummer).first()
            if not klus:
                flash('Deze klus bestaat niet.', 'danger')
                return redirect(url_for('main.mijn_chats'))

            # Ontvanger bepalen (afhankelijk van de rol van de gebruiker)
            if klus.idnummer == user_id:  # Jij bent de aanbieder
                if klus.klussen_zoekers:  # Controleer of er zoekers zijn
                    ontvanger_id = klus.klussen_zoekers[0].idnummer
                else:
                    flash('Er is geen zoeker voor deze klus.', 'warning')
                    return redirect(url_for('main.mijn_chats'))
            else:  # Jij bent de zoeker
                ontvanger_id = klus.idnummer

            print(f"DEBUG: Ontvanger ID voor bericht: {ontvanger_id}")

            # Nieuw bericht opslaan
            nieuw_bericht = Bericht(
                klusnummer=klusnummer,
                afzender_id=user_id,
                ontvanger_id=ontvanger_id,
                inhoud=inhoud,
                verzonden_op=datetime.utcnow()
            )
            db.session.add(nieuw_bericht)
            db.session.commit()

            # **Maak een melding voor de ontvanger**
            if ontvanger_id:
                maak_melding(
                    gebruiker_id=ontvanger_id,
                    bericht=f"Je hebt een nieuw bericht ontvangen voor de klus '{klus.naam}'."
                )
                print(f"DEBUG: Melding aangemaakt voor gebruiker {ontvanger_id}")

                flash("Bericht succesvol verzonden! De ontvanger heeft een melding gekregen.", "success")

            return redirect(url_for('main.mijn_chats'))

    # Aangeboden klussen ophalen
    aangeboden_klussen = Klus.query.filter(
        Klus.idnummer == user_id,
        Klus.status.in_(['geaccepteerd', 'voltooid']),
    ).order_by(Klus.voltooid_op.desc()).all()

    # Gezochte klussen ophalen
    gezochte_klussen = Klus.query.filter(
        Klus.klussen_zoekers.any(Persoon.idnummer == user_id),
        Klus.status.in_(['geaccepteerd', 'voltooid']),
    ).order_by(Klus.voltooid_op.desc()).all()

    # Combineer beide lijsten en voeg berichten en namen toe
    klussen_info = []
    for klus in aangeboden_klussen + gezochte_klussen:
        berichten = Bericht.query.filter_by(klusnummer=klus.klusnummer).order_by(Bericht.verzonden_op.desc()).all()

        ontvanger = None
        if klus.idnummer == user_id:  # Jij bent de aanbieder
            if klus.klussen_zoekers:
                ontvanger = Persoon.query.filter_by(idnummer=klus.klussen_zoekers[0].idnummer).first()
        else:
            ontvanger = Persoon.query.filter_by(idnummer=klus.idnummer).first()

        other_person_name = f"{ontvanger.voornaam} {ontvanger.achternaam}" if ontvanger else "Onbekend"

        ongelezen_berichten = [bericht for bericht in berichten if bericht.ontvanger_id == user_id and not bericht.gelezen]


        klussen_info.append({
            'klusnummer': klus.klusnummer,
            'naam': klus.naam,
            'status': klus.status,
            'ongelezen_berichten': len(ongelezen_berichten),
            'berichten': berichten,
            'type': 'aangeboden' if klus.idnummer == user_id else 'gezocht',
            'other_person_name': other_person_name
        })

    klussen_info.sort(key=lambda x: x['berichten'][0].verzonden_op if x['berichten'] else datetime.min, reverse=True)

    return render_template('mijn_chats.html', klussen=klussen_info)
