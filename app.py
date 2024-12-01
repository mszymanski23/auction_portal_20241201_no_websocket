import random
import threading
import time
from flask import Flask, request, render_template_string, redirect, url_for, session, send_file, flash, get_flashed_messages, jsonify
import os
import datetime


# version 1.3 dodanie odświeżania licznika aukcji co sekundę - jest ok 
#             dodane wiele rund 
#             dodane wyłanianie zwycięzcy przy tej samej ofercie



app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Klucz potrzebny do używania sesji

uzytkownicy = ["Pomarańcza", "Magenta", "Lila", "Zieleniak", "Administrator"]
zalogowani_uzytkownicy = []
produkty = {
    "Blok czekoladowy A": 10,
    "Blok czekoladowy B": 10,
    "Blok czekoladowy C": 10,
    "Blok czekoladowy D": 10,
    "Blok czekoladowy E": 10,
    "Blok czekoladowy F": 10,
    "Bombonierka 800": 10
}
licytacje = {produkt: [] for produkt in produkty}
propozycje = {produkt: {} for produkt in produkty}
wszystkie_oferty = {produkt: [] for produkt in produkty}
max_licytacje_na_uzytkownika = 2
aukcja_aktywny = False
czas_rundy = 60  # Domyślny czas rundy w sekundach
czas_pozostaly = czas_rundy

# Funkcja do generowania wyników aukcji
def generuj_wyniki_aukcji():
    wynik = "Wyniki aukcji:\n\n"
    for produkt, licytujacy in licytacje.items():
        wynik += f"Produkt: {produkt}\n"
        if propozycje[produkt]:
            najwyzsza_oferta = max(propozycje[produkt].values())
            zwyciezcy = [uzytkownik for uzytkownik, oferta in propozycje[produkt].items() if oferta == najwyzsza_oferta]
            if len(zwyciezcy) > 1:
                zwyciezca = random.choice(zwyciezcy)
            else:
                zwyciezca = zwyciezcy[0]
            wynik += f" Finalna cena: {najwyzsza_oferta} zł\n"
            wynik += f" Zwycięzca: {zwyciezca}\n"
            licytacje[produkt].append(zwyciezca)
            produkty[produkt] = najwyzsza_oferta
        else:
            wynik += f" Finalna cena: {produkty[produkt]} zł\n"
            wynik += " Licytujący: Brak\n"
        wynik += "-" * 40 + "\n"
    return wynik

# Funkcja do zapisywania wyników do pliku
def zapisz_wyniki_do_pliku():
    data = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sciezka = os.path.join(os.getcwd(), f"wyniki_aukcji_{data}.txt")
    with open(sciezka, "w", encoding="utf-8") as plik:
        plik.write(generuj_wyniki_aukcji())
    return sciezka

# Funkcja do uruchomienia rundy aukcji
def uruchom_runde_aukcji():
    global aukcja_aktywny, czas_pozostaly
    aukcja_aktywny = True
    while True:
        czas_pozostaly = czas_rundy
        while czas_pozostaly > 0:
            time.sleep(1)
            czas_pozostaly -= 1
        flash("Runda aukcji zakończona. Wyniki zostały ogłoszone.")
        zapisz_wyniki_do_pliku()
        for produkt, oferty in propozycje.items():
            wszystkie_oferty[produkt].extend(oferty.items())
        propozycje.clear()
        if not any(propozycje.values()):
            break
    aukcja_aktywny = False

@app.route('/get_time')
def get_time():
    return jsonify(czas_pozostaly=czas_pozostaly)

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('choose_user'))
    user = session['user']
    if user == "Administrator":
        return render_template_string('''
        <html>
        <head>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            .highlight {
                background-color: #d4edda;
            }
            .disabled {
                pointer-events: none;
                opacity: 0.6;
            }
            .text-info {
                font-weight: bold;
            }
            .modal-body {
                text-align: center;
                font-size: 16px;
            }
        </style>
        <script>
        function updateTime() {
            fetch('/get_time')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('czas_pozostaly').innerText = data.czas_pozostaly;
                });
        }
        setInterval(updateTime, 1000);
        </script>
        </head>
        <body>
        <h1>Licytacja - Administrator</h1>
        <h2>Aktualne licytacje:</h2>
        <ul>
        {% for product, bidders in licytacje.items() %}
        <li>
        <span class="product">{{ product }}</span>:
        <span class="bidders">{{ bidders }}</span>
        (Aktualna cena: <span class="price">{{ produkty[product] }} zł</span>)
        </li>
        {% endfor %}
        </ul>
        <h2>Wszystkie oferty:</h2>
        <ul>
        {% for product, offers in wszystkie_oferty.items() %}
            <li><strong>{{ product }}</strong></li>
            <ul>
                {% for user, offer in offers %}
                    <li>{{ user }}: {{ offer }} zł</li>
                {% endfor %}
            </ul>
        {% endfor %}
        </ul>
        <h2>Zalogowani użytkownicy:</h2>
        <ul>
        {% for user in zalogowani_uzytkownicy %}
        <li>{{ user }}</li>
        {% endfor %}
        </ul>
        <a href="/logout" class="logout">Zmień użytkownika</a>
        <a href="/reset" class="reset">Resetuj licytacje</a>
        <a href="/export" class="export">Eksportuj wyniki aukcji</a>
        <form action="/start_auction" method="post">
            <label for="czas_rundy">Czas rundy (sekundy):</label>
            <input type="number" id="czas_rundy" name="czas_rundy" value="{{ czas_rundy }}" min="10">
            <input type="submit" value="Uruchom rundę aukcji" class="start-auction">
        </form>
        </body>
        </html>
         ''', produkty=produkty, licytacje=licytacje, wszystkie_oferty=wszystkie_oferty, zalogowani_uzytkownicy=zalogowani_uzytkownicy)
    else:
         user_bids = [product for product, bidders in licytacje.items() if user in bidders]
         return render_template_string('''
         <html>
         <head>
         <style>
         body { font-family: Arial, sans-serif; }
         h1 { color: #333; }
         ul { list-style-type: none; padding: 0; }
         li { margin: 5px 0; }
         .product { font-weight: bold; }
         .price { color: #007BFF; }
         </style>
         <script>
         function updateTime() {
             fetch('/get_time')
                 .then(response => response.json())
                 .then(data => {
                     document.getElementById('czas_pozostaly').innerText = data.czas_pozostaly;
                 });
         }
         setInterval(updateTime, 1000);
         </script>
         </head>
         <body>
         <h1>Licytacja</h1>
         <p>Witaj, {{ user }}!</p>
         <!-- Sekcja komunikatów -->
         {% with messages = get_flashed_messages() %}
         {% if messages %}
         <p style="color: red; font-weight: bold;">
         {{ messages[-1] }}
         </p>
         {% endif %}
         {% endwith %}
         {% if aukcja_aktywny %}
             <p>Pozostały czas rundy: <span id="czas_pozostaly">{{ czas_pozostaly }}</span> sekund</p>
             <form action="/bid" method="post">
             <select name="product">
             {% for product, price in produkty.items() %}
             <option value="{{ product }}">{{ product }} (Cena wywoławcza: {{ price }} zł)</option>
             {% endfor %}
             </select>
             <input type="number" name="bid_amount" placeholder="Twoja oferta" required>
             <input type="submit" value="Złóż ofertę">
             </form>
         {% else %}
             <p>Aukcja nie jest aktywna.</p>
         {% endif %}
         <h2>Aktualne ceny:</h2>
         <ul>
         {% for product, price in produkty.items() %}
         <li>
         <span class="product">{{ product }}</span>:
         <span class="price">{{ price }} zł</span>
         </li>
         {% endfor %}
         </ul>
         <h2>Twoje licytacje:</h2>
         <ul>
         {% for product in user_bids %}
         <li>
         <span class="product">{{ product }}</span>
         (Aktualna cena: <span class="price">{{ produkty[product] }} zł</span>)
         </li>
         {% endfor %}
         </ul>
         <a href="/logout">Zmień użytkownika</a>
         </body>
         </html>
         ''', produkty=produkty, user=user, user_bids=user_bids, aukcja_aktywny=aukcja_aktywny, czas_pozostaly=czas_pozostaly)

@app.route('/choose_user', methods=['GET', 'POST'])
def choose_user():
    if request.method == 'POST':
        user = request.form.get('user')
        if user in uzytkownicy and user not in zalogowani_uzytkownicy:
            session['user'] = user
            zalogowani_uzytkownicy.append(user)
            return redirect(url_for('index'))
        else:
            return "Użytkownik jest już zalogowany.", 400
    return render_template_string('''
    <html>
    <body>
    <h1>Wybierz użytkownika</h1>
    <form method="post">
    {% for user in uzytkownicy %}
    <button type="submit" name="user" value="{{ user }}" {% if user in zalogowani_uzytkownicy %}disabled{% endif %}>
    {{ user }}
    </button>
    {% endfor %}
    </form>
    </body>
    </html>
    ''', uzytkownicy=uzytkownicy, zalogowani_uzytkownicy=zalogowani_uzytkownicy)

@app.route('/bid', methods=['POST'])
def bid():
    user = session.get('user')
    product = request.form.get('product')
    bid_amount = int(request.form.get('bid_amount'))
    if user and product in produkty:
        # Sprawdzenie, czy użytkownik przelicytowuje samego siebie
        if user in propozycje[product]:
            flash(f"Nie możesz przelicytować samego siebie na produkcie {product}.")
            return redirect(url_for('index'))
        # Sprawdzenie limitu liczby licytacji użytkownika
        user_bids = sum([1 for bids in propozycje.values() if user in bids])
        if user_bids >= max_licytacje_na_uzytkownika:
            flash("Osiągnąłeś limit licytacji (maksymalnie 2).")
            return redirect(url_for('index'))
        # Dodanie propozycji
        propozycje[product][user] = bid_amount
        flash(f"Pomyślnie złożono ofertę na produkt {product}. Proponowana cena: {bid_amount} zł.")
    else:
        flash("Nieprawidłowy produkt.")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    user = session.pop('user', None)
    if user in zalogowani_uzytkownicy:
        zalogowani_uzytkownicy.remove(user)
    return redirect(url_for('choose_user'))

@app.route('/reset')
def reset():
    global licytacje, produkty, propozycje, wszystkie_oferty
    licytacje = {produkt: [] for produkt in produkty}
    propozycje = {produkt: {} for produkt in produkty}
    wszystkie_oferty = {produkt: [] for produkt in produkty}
    produkty = {
        "Blok czekoladowy A": 10,
        "Blok czekoladowy B": 10,
        "Blok czekoladowy C": 10,
        "Blok czekoladowy D": 10,
        "Blok czekoladowy E": 10,
        "Blok czekoladowy F": 10,
        "Bombonierka 800": 10
    }
    return redirect(url_for('index'))

@app.route('/export')
def export():
    if session.get('user') != "Administrator":
        return "Brak uprawnień.", 403
    sciezka = zapisz_wyniki_do_pliku()
    return f"Wyniki aukcji zapisano do pliku: {sciezka}"

@app.route('/download')
def download():
    if session.get('user') != "Administrator":
        return "Brak uprawnień.", 403
    sciezka = zapisz_wyniki_do_pliku()
    return send_file(sciezka, as_attachment=True)

@app.route('/start_auction', methods=['POST'])
def start_auction():
    global czas_rundy
    if session.get('user') != "Administrator":
        return "Brak uprawnień.", 403
    czas_rundy = int(request.form.get('czas_rundy', 60))
    threading.Thread(target=uruchom_runde_aukcji).start()
    flash(f"Runda aukcji została uruchomiona na {czas_rundy} sekund.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
