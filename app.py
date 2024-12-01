
from flask import Flask, request, render_template_string, redirect, url_for, session

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
max_licytacje_na_uzytkownika = 2
max_licytujacych = 4

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('choose_user'))
    user = session['user']
    if user == "Administrator":
        return render_template_string('''
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    h1 { color: #333; }
                    ul { list-style-type: none; padding: 0; }
                    li { margin: 5px 0; }
                    .product { font-weight: bold; }
                    .bidders { color: #555; }
                    .price { color: #007BFF; }
                    .logout { margin-top: 20px; display: inline-block; }
                </style>
            </head>
            <body>
                <h1>Licytacja - Administrator</h1>
                <p>Witaj, {{ user }}!</p>
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
                <a href="/logout" class="logout">Zmień użytkownika</a>
            </body>
            </html>
        ''', user=user, produkty=produkty, licytacje=licytacje)
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
                    .logout { margin-top: 20px; display: inline-block; }
                </style>
            </head>
            <body>
                <h1>Licytacja</h1>
                <p>Witaj, {{ user }}!</p>
                <form action="/bid" method="post">
                    <select name="product">
                        {% for product, price in produkty.items() %}
                            <option value="{{ product }}">{{ product }} (Cena wywoławcza: {{ price }} zł)</option>
                        {% endfor %}
                    </select>
                    <input type="submit" value="Licytuj">
                </form>
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
                <a href="/logout" class="logout">Zmień użytkownika</a>
            </body>
            </html>
        ''', user=user, produkty=produkty, user_bids=user_bids)

@app.route('/choose_user', methods=['GET', 'POST'])
def choose_user():
    if request.method == 'POST':
        user = request.form.get('user')
        if user in uzytkownicy and user not in zalogowani_uzytkownicy:
            session['user'] = user
            zalogowani_uzytkownicy.append(user)
            return redirect(url_for('index'))
        else:
            return render_template_string('''
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        h1 { color: #333; }
                        .user-button { margin: 5px; padding: 10px 20px; background-color: #007BFF; color: white; border: none; cursor: pointer; }
                        .user-button:disabled { background-color: #ccc; cursor: not-allowed; }
                        .back-button { margin-top: 20px; display: inline-block; padding: 10px 20px; background-color: #007BFF; color: white; text-decoration: none; }
                    </style>
                </head>
                <body>
                    <h1>Aukcja testowa bloków czekoladowych</h1>
                    <h2>Ten użytkownik jest już zalogowany. Wybierz innego użytkownika.</h2>
                    <form method="post">
                        {% for user in uzytkownicy %}
                            <button type="submit" name="user" value="{{ user }}" class="user-button" {% if user in zalogowani_uzytkownicy %}disabled{% endif %}>
                                {{ user }}
                            </button>
                        {% endfor %}
                    </form>
                    <a href="{{ url_for('choose_user') }}" class="back-button">Powrót</a>
                </body>
                </html>
            ''', uzytkownicy=uzytkownicy, zalogowani_uzytkownicy=zalogowani_uzytkownicy)
    return render_template_string('''
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                h1 { color: #333; }
                .user-button { margin: 5px; padding: 10px 20px; background-color: #007BFF; color: white; border: none; cursor: pointer; }
                .user-button:disabled { background-color: #ccc; cursor: not-allowed; }
            </style>
        </head>
        <body>
            <h1>Aukcja testowa bloków czekoladowych</h1>
            <h2>Wybierz użytkownika</h2>
            <form method="post">
                {% for user in uzytkownicy %}
                    <button type="submit" name="user" value="{{ user }}" class="user-button" {% if user in zalogowani_uzytkownicy %}disabled{% endif %}>
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

    if user and product:
        user_bids = sum([1 for bids in licytacje.values() if user in bids])
        if user_bids < max_licytacje_na_uzytkownika and len(licytacje[product]) < max_licytujacych:
            licytacje[product].append(user)
            produkty[product] += 5  # Przebicie ceny o 5 zł
        else:
            return "Nie możesz licytować więcej produktów lub produkt osiągnął maksymalną liczbę licytujących."

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    user = session.pop('user', None)
    if user in zalogowani_uzytkownicy:
        zalogowani_uzytkownicy.remove(user)
    return redirect(url_for('choose_user'))

if __name__ == '__main__':
    app.run(debug=True)
