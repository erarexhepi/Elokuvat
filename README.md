# Elokuvat 

Elokuvasovellus tarjoaa käyttäjälle mahdollisuuden tutustua erilaisiin elokuviin, lukea niistä arvioita ja antaa omia arvioitaan. Sovelluksen avulla käyttäjä voi löytää uusia elokuvia katseltavaksi, saada inspiraatiota ja suosituksia eri genreistä ja ajankohtaisista elokuvista.

Sovelluksen ominaisuuksia ovat:

- Käyttäjä voi kirjautua sisään ja ulos sekä luoda uuden tunnuksen
- Käyttäjä voi selata eri elokuvia ja niiden arviointeja
- Käyttäjä voi poistaa ja lisätä elokuvia
- Käyttäjä voi antaa avostelut ja kommentit elokuviin
- Elokuvat voi listata esim. parhaimmasta arvostelusta huonoimpaan tai aakkoisjärjestyksessä
- Käyttäjät voivat kommentoida jo valmiiseen arvosteluun sekä nähdä muiden kommentit

Sovellus ei ole testattavissa Fly.iossa.

Ohjeet:
Kloonaa tämä repositorio omalle koneellesi ja siirry sen juurikansioon. Luo kansioon .env-tiedosto ja määritä sen sisältö seuraavanlaiseksi:

DATABASE_URL=<tietokannan-paikallinen-osoite>

SECRET_KEY=<salainen-avain>

Seuraavaksi aktivoi virtuaaliympäristö ja asenna sovelluksen riippuvuudet komennoilla:

$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r ./requirements.txt

Määritä vielä tietokannan skeema komennolla

$ psql < schema.sql

Nyt voit käynnistää sovelluksen komennolla

$ flask run

