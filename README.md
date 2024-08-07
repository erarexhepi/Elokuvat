# Elokuvat 

Elokuvasovellus tarjoaa käyttäjälle mahdollisuuden tutustua erilaisiin elokuviin, lukea niistä arvioita ja antaa omia arvioitaan. Sovelluksen avulla käyttäjä voi löytää uusia elokuvia katseltavaksi, saada inspiraatiota ja suosituksia eri genreistä ja ajankohtaisista elokuvista.

Ominaisuudet käyttäjälle:

- Kirjautuminen sisään ja ulos sekä uuden tunnuksen luonti
- Erilaisten elokuvien ja niiden arvioiden selaaminen
- Elokuvien lisääminen ja poistaminen
- Arvioiden ja kommenttien antaminen elokuville
- Elokuvien lisääminen suosikkeihin tulevaa katselua varten ja niiden poistaminen suosikeista
- Elokuvien lajittelu arvostelujen perusteella (parhaimmasta huonoimpaan), aakkosjärjestyksessä jne.
- Kommentointi olemassa oleviin arvosteluihin ja muiden käyttäjien kommenttien näkeminen
- Muiden käyttäjien kommenttien tykkääminen ja ei-tykkääminen

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

