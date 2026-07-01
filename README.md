# Salamanca Guide

Salamancako gida kulturala, oinez erabiltzeko pentsatua.

Filosofia sinplea da:

- Google Maps-ek oinak gidatzen ditu.
- PWAk begirada gidatzen du.

Horrek esan nahi du web aplikazioak ez duela nabigazioa egiten. Ez dago GPS jarraipenik, ez GPXrik, ez KMLrik, ezta audio automatiko sortzerik ere. Aplikazioak ibilbide bakoitzeko edukia eskaintzen du: testuak, irudiak, bideoak baldin badaude, eta Google Maps-era salto egiteko estekak.

## Egitura

```text
Salamanca/
├── app/                  PWA sinplifikatua
├── content/
│   └── eu/
│       ├── dia1/
│       ├── dia2_goiza/
│       └── dia3_goiza/
├── data/
│   └── routes/
│       ├── dia1.yaml
│       ├── dia2_goiza.yaml
│       └── dia3_goiza.yaml
├── public/
│   ├── images/
│   └── media/
│       ├── dia1/
│       ├── dia2_goiza/
│       └── dia3_goiza/
└── scripts/
    └── build.py
```

## Datu-iturri bakarra

Ibilbide bakoitzak YAML fitxategi bakarra du `data/routes/` barruan. Han daude:

- metadatu nagusiak;
- geldialdien ordena;
- denbora erlatiboak;
- koordenatuak;
- Google Maps-eko jatorria, helmuga eta waypointak;
- irudiaren izena;
- pantailan agertuko diren laburpenak eta oharrak.

Gidoi luzea, berriz, `content/eu/<ibilbidea>/paradaXX.md` fitxategietan dago.

## Bideoak nola gehitu

PWAk bideoa erakutsiko du fitxategia existitzen bada:

```text
public/media/dia2_goiza/parada01.mp4
public/media/dia2_goiza/parada02.mp4
...
```

Fitxategia ez badago, txartelak testua bakarrik erakutsiko du.

## Eraikuntza

`build.py` scriptak YAML eta Markdown edukietatik `app/data.js` eta `app/sw.js` eguneratzen ditu:

```bash
cd Salamanca
python3 scripts/build.py
```

## Tokian probatzea

```bash
cd Salamanca
python3 -m http.server 8080
```

Ondoren ireki:

- [http://localhost:8080/app/](http://localhost:8080/app/)

## Offline

Konexiorik gabe erabilgarri geratzen dira:

- interfazea;
- ibilbideen testuak;
- irudiak;
- lehendik cachean gelditu diren bideoak.

Google Maps, berriz, kanpoko zerbitzua da eta sare-konexioa behar du.

## Une honetan dauden ibilbideak

- `dia1`: lehen arratsaldeko paseo lasaia, hotelatik Fonsecaraino.
- `dia2_goiza`: ordubeteko goizeko paseo lasaia, hotelatik abiatu eta hotelera itzultzen dena.
- `dia3_goiza`: goiz luzeko ibilbidea, katedrala hirian zehar nola aldatzen den ulertzeko, gosariarekin eta amaiera Fonsecan.

## Berrerabilgarritasuna

Egitura hau erraz eramateko diseinatuta dago:

- `Budapest/`
- `Biarritz/`
- `Donostia/`
- `Lyon/`
- `Praga/`

Hiria aldatzeko, nahikoa da:

1. YAML berriak sortzea `data/routes/` barruan.
2. Gidoiak `content/eu/` barruan jartzea.
3. Irudiak eta bideoak `public/` barruan gehitzea.
4. `python3 scripts/build.py` berriz exekutatzea.
