from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify, g
from flask_mail import Mail, Message
from flask_babel import Babel
from config import Config
from models import db, Appointment, ContactMessage
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)
babel = Babel(app)

ADMIN_PASSWORD = 'parenthese2024'

def get_locale():
    lang = session.get('lang')
    if lang and lang in app.config['BABEL_SUPPORTED_LOCALES']:
        return lang
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

babel.init_app(app, locale_selector=get_locale)

@app.before_request
def before_request():
    g.lang = get_locale() or 'fr'

@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

SERVICES = [
    {"id": "andulation", "title": {"fr": "Andulation Therapie", "de": "Andullationstherapie", "en": "Andulation Therapy"}, "description": {"fr": "Therapie biophysique vasculaire avec stimulation des tissus profonds.", "de": "Biophysikalische Gefaesstherapie mit Tiefengewebestimulation.", "en": "Biophysical vascular therapy with deep tissue stimulation."}, "icon": "🔬", "duration": 45, "price": "CHF 90.-"},
    {"id": "massage-classique", "title": {"fr": "Massage Classique (Suedois)", "de": "Klassische Massage (Schwedisch)", "en": "Classic Massage (Swedish)"}, "description": {"fr": "Technique de massage suedois pour dissoudre les tensions musculaires.", "de": "Schwedische Massagetechnik zur Loesung von Muskelverspannungen.", "en": "Swedish massage technique to dissolve muscle tension."}, "icon": "💆", "duration": 60, "price": "CHF 110.-"},
    {"id": "therapie-manuelle", "title": {"fr": "Therapie Manuelle", "de": "Manuelle Therapie", "en": "Manual Therapy"}, "description": {"fr": "Therapie manuelle pour les problemes articulaires et musculo-squelettiques.", "de": "Manuelle Therapie bei Gelenk- und Muskel-Skelett-Problemen.", "en": "Manual therapy for joint and musculoskeletal problems."}, "icon": "🤲", "duration": 50, "price": "CHF 120.-"},
    {"id": "hijama", "title": {"fr": "Hijama (Cupping Therapy)", "de": "Hijama (Schroepftherapie)", "en": "Hijama (Cupping Therapy)"}, "description": {"fr": "Therapie traditionnelle par ventouses pour la detoxification naturelle.", "de": "Traditionelle Schroepftherapie zur natuerlichen Entgiftung.", "en": "Traditional cupping therapy for natural detoxification."}, "icon": "🩸", "duration": 45, "price": "CHF 100.-"},
    {"id": "roqya", "title": {"fr": "Roqya", "de": "Roqya", "en": "Roqya"}, "description": {"fr": "Seance de guerison spirituelle pour retrouver votre paix interieure.", "de": "Spirituelle Heilungssitzung fuer inneren Frieden.", "en": "Spiritual healing session to restore inner peace."}, "icon": "🕊️", "duration": 60, "price": "Sur demande"}
]

def get_service_localized(service, lang=None):
    if lang is None:
        lang = g.get('lang', 'fr')
    return {"id": service["id"], "title": service["title"].get(lang, service["title"]["fr"]), "description": service["description"].get(lang, service["description"]["fr"]), "icon": service["icon"], "duration": service["duration"], "price": service["price"]}

@app.route('/')
def index():
    lang = g.get('lang', 'fr')
    services = [get_service_localized(s, lang) for s in SERVICES]
    return render_template('index.html', services=services, lang=lang)

@app.route('/services')
def services_page():
    lang = g.get('lang', 'fr')
    services = [get_service_localized(s, lang) for s in SERVICES]
    return render_template('services.html', services=services, lang=lang)

@app.route('/about')
def about():
    return render_template('about.html', lang=g.get('lang', 'fr'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    lang = g.get('lang', 'fr')
    services = [get_service_localized(s, lang) for s in SERVICES]
    if request.method == 'POST':
        contact_msg = ContactMessage(name=request.form.get('name'), email=request.form.get('email'), phone=request.form.get('phone'), subject=request.form.get('subject', ''), message=request.form.get('message'))
        db.session.add(contact_msg)
        db.session.commit()
        flash('Votre message a ete envoye avec succes!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', services=services, lang=lang)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    lang = g.get('lang', 'fr')
    services = [get_service_localized(s, lang) for s in SERVICES]
    if request.method == 'POST':
        service_id = request.form.get('service')
        service_data = next((s for s in SERVICES if s['id'] == service_id), None)
        if service_data:
            appointment = Appointment(client_name=request.form.get('name'), client_email=request.form.get('email'), client_phone=request.form.get('phone'), service_id=service_id, service_name=service_data['title'].get(lang, service_data['title']['fr']), appointment_date=datetime.strptime(f"{request.form.get('date')} {request.form.get('time')}", "%Y-%m-%d %H:%M"), duration_minutes=service_data['duration'], message=request.form.get('message', ''), status='pending')
            db.session.add(appointment)
            db.session.commit()
            try:
                msg = Message('Nouveau RDV: ' + request.form.get('name'), recipients=[app.config['MAIL_USERNAME']])
                msg.html = f"<h2>Nouveau Rendez-vous</h2><p>Client: {request.form.get('name')}</p><p>Email: {request.form.get('email')}</p><p>Tel: {request.form.get('phone')}</p><p>Soin: {service_data['title']['fr']}</p><p>Date: {request.form.get('date')} {request.form.get('time')}</p>"
                mail.send(msg)
            except Exception as e:
                print(f'Email error: {e}')

        flash('Votre rendez-vous a ete reserve!', 'success')
        return redirect(url_for('booking'))
    available_times = [f"{h:02d}:{m:02d}" for h in range(9, 19) for m in (0, 30)]
    min_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    return render_template('booking.html', services=services, available_times=available_times, min_date=min_date, lang=lang, calendly_url=app.config.get('CALENDLY_URL'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        flash('Mot de passe incorrect', 'error')
    return render_template('admin_login.html', lang='fr')

@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    appointments = Appointment.query.order_by(Appointment.appointment_date.desc()).all()
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin.html', appointments=appointments, messages=messages, lang='fr')

@app.route('/admin/confirm/<int:id>')
def admin_confirm(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    apt = Appointment.query.get_or_404(id)
    apt.status = 'confirmed'
    db.session.commit()
    flash('Rendez-vous confirme!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/cancel/<int:id>')
def admin_cancel(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    apt = Appointment.query.get_or_404(id)
    apt.status = 'cancelled'
    db.session.commit()
    flash('Rendez-vous annule', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('js/sw.js')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=8080)
