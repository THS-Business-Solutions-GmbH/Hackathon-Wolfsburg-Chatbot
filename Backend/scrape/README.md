Rohe scrapings sortiert nach domain.

- Slahes ('/') ersetzt durch Underscore ('\_') im Dateinamen
- Die Ending .html ist nicht notwendigerweise im Original

Schritt 1:

```bash
for url in $(cat ../urls.txt); do curl https://www.wolfsburg.de$url > ${url//\//_}.html; sleep 5; done;
```

wobei  `url.txt` die sind, die im Moment schon im scraping von Ruben sind.

Scrhitt 2:

Die habe ich dann einfach alle concatted mit `$ cat wolfsburg.de/* > wolfsburg-all.html` und daraus habe ich dann die Links gezogen mit:

```bash
$ perl -MHTML::TreeBuilder  -le '$/ = undef; my $t = HTML::TreeBuilder->new; $t->parse(<>); print $_->attr("href") for $t->look_down("_tag", "a");' wolfsburg-all.html
```

(das braucht HTML::TreeBuilder, zu installieren mit `sudo apt install libhtml-treebuilder-libxml-perl`)

Aus den Links dadrin kann man dann ziehen:

- "^/" -> intern
- "^/-/" -> intern media pdf
- "^/en-us/" -> intern, englische Version
- "http" -> externe adressen

ACHTUNG: Da ist ein bisschen Beifang den man nicht haben möchte:
  - "mailto:" Mailadressen, aber auch welche ohne
  - "tel:" Telefonnummern,
  - "#..." lokale Hashanker, aber auch URLs mit Anker
  - "/sitecore/service/notfound" - tote links
  - "/www.facebook%20.com" - sus?


Die Version hier hat das 3x mit den _internen, nicht pdf, nicht englishen_ gemacht, enthält also alle internen Links die mit 2 Klicks aus der Übersicht zu erreichen sind.

Schritt 3:

Abschliessender Sanity Check:

- Dateien die kleiner als 1000 byte sind, sind alles 403 redirects, wieder rausgeworfen. Das waren hier:

```
$ find . -type f -size -1000c
./_tourismus_schlafen-und-essen_privatunterkuenfte.html
./_rathaus_staedtischegesellschaften_web_abwasserbeitrag.html
./_wirtschaft_sofortprogramm-perspektive-innenstadt.html
./_tourismus_tourist-information_tourist-information.html
./_tourismus_wolfsburg-erleben_highlights.html
./_tourismus_schlafen-und-essen_gastronomie.html
./_rathaus_politik_wahlen_ausland.html
./_bildung_informationen-fuer-eltern_schule_schulpsychologie.html
./_tourismus_shopping-und-nightlife_shopping.html
./_tourismus_wolfsburg-erleben_veranstaltungen.html
./_bildung_schullandschaft.html
./_rathaus_stadtverwaltung_03-soziales_westhagen.html
./_rathaus_staedtischegesellschaften_web_fremdwasser.html
./_kultur_museen_kunstmuseum.html
./_rathaus_karriere_jobboerse.html
```


Upcoming Schritt 4:

Aus dem Rest noch handverlesen die interessanten Sachen ziehen. Zum Beispiel:

- pdfs aus `/-/media`
- subdomains in wolfsburg.de:
  - anwendungen.wolfsburg.de
  - formserv.stadt.wolfsburg.de
  - rathausonline.stadt.wolfsburg.de
  - ratsinfob.stadt.wolfsburg.de
  - redaktion.wolfsburg.de
  - statistik.stadt.wolfsburg.de
  - klinikum.wolfsburg.de
- wolfsburg-erleben.de
- bildungshaus-wolfsburg.de
- regionalverbund-wolfsburg.de

Unsicher:

- gesetze-im-internet.de
- subdomains von niedersachsen.de:
  - buergerservice.niedersachsen.de
  - amtsgericht-wolfsburg.niedersachsen.de
  - dienstleisterportal.niedersachsen.de
  - lgll.niedersachsen.de (da ist der Kampfmittelbeseitigungsdienst)

Nicht aufnehmen würde ich:

- geoservice (wenig text)
- youtube




Schritt 5: JSON

Das kleine Perlscript `scrape/extract_text.pl` nimmt einen Dateinamen und wirft ein JSON aus, in dem semantisch extrahiert ist:

- headers -> alle h1/h2 header der Seite
- links -> die <link> tags mit denen die seite ihre eigenen sprach alternativen angibt
- blocks -> eine liste von blöcken mit:
  - content -> <p> text block
  - breadcrumbs -> alle subheader auf dem weg zu diesem block

Alle Texte sind:
  - unicode bereinigt von &nbsp; und ähnlichem Müll.
  - trimmed

Die json files sind erzeugt mit:

```
$ for f in $(ls); do perl -l ../extract_data.pl $f > json/${f//html/json}; done
```
