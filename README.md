# slotkeeper

Sovelluksessa käyttäjät pystyvät varaamaan verkossa olevia testikoneita.

- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä pystyy lisäämään testikoneita ja muokkaamaan ja poistamaan niitä.
- Käyttäjä näkee sovellukseen lisätyt testikoneet.
- Käyttäjä pystyy etsimään testikoneita hakusanalla.
- Käyttäjäsivu näyttää, onko käyttäjällä voimassa olevia varauksia testikoneille.
- Käyttäjä pystyy varaamaan testikoneen määräajaksi.
- Käyttäjä pystyy vapauttamaan varaamansa testikoneen.
- Käyttäjä pystyy antamaan testikoneelle kommentin. Testikoneesta näytetään kommentit.

Tässä pääasiallinen tietokohde on testikone ja toissijainen tietokohde on varaustilanne.


## Sovelluksen asennus:
Asenna `flask`-kirjasto:

```
$ pip install flask
```

Luo tietokannan taulut ja lisää alkutiedot:

```
$ sqlite3 database.db < schema.sql
```

Testikäyttöön on mahdollista lisätä testidataa:

```
$ sqlite3 database.db < demo.sql
```

demo.sql lisää testilaitteita, muutaman varauksen ja muutaman kommentin. demo.sql lisää myös käyttäjän 'DemoKäyttäjä' jolla on salasana 'demoni'. demo.sql sisältää carriage return merkkejä commitoitavissa merkkijonoissa mikä voi aiheuttaa ongelmia, testattu toimivaksi MacOS:lla.

Voit käynnistää sovelluksen näin:

```
$ flask run
```
