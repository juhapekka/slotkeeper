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

Voit käynnistää sovelluksen näin:

```
$ flask run
```


### edistyminen:

- ✅ Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- ❌ Käyttäjä pystyy lisäämään testikoneita ja muokkaamaan ja poistamaan niitä.
- ❌ Käyttäjä näkee sovellukseen lisätyt testikoneet.
- ❌ Käyttäjä pystyy etsimään testikoneita hakusanalla.
- ❌ Käyttäjäsivu näyttää, onko käyttäjällä voimassa olevia varauksia testikoneille.
- ❌ Käyttäjä pystyy varaamaan testikoneen määräajaksi.
- ❌ Käyttäjä pystyy vapauttamaan varaamansa testikoneen.
- ❌ Käyttäjä pystyy antamaan testikoneelle kommentin. Testikoneesta näytetään kommentit.
