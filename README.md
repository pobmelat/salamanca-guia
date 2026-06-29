# Salamanca · guía interactiva

Versión 1: paseo de llegada desde Zenit Hall88 hasta la recepción del Colegio Arzobispo Fonseca.

## Plan del Día 1

- **Horario:** 17:00–18:45.
- **Distancia:** 3,45 km; unos 45–50 min andando.
- **Café:** Café Novelty, llegada prevista 17:24 y pausa de unos 20 min.
- **Final:** Colegio Arzobispo Fonseca, C/ Fonseca, 4, entre 18:40 y 18:45.
- **Sin regreso al hotel:** la ruta termina al comenzar la recepción.

Secuencia: Hall88 → Café Novelty → Plaza Mayor → Casa de las Conchas → Universidad/Patio de Escuelas → Palacio de Monterrey → Fonseca.

Puente Romano, ribera del Tormes, Huerto de Calixto y Melibea, Casa Lis, Patio Chico y catedrales se reservan deliberadamente para otro día.

## Contenido

```text
Salamanca/
├── routes/   dia1.gpx, dia1.kml y fuente GeoJSON
├── audio/    un guion conversacional por parada
├── pdf/      guia_dia1.pdf
├── maps/     mapa.png
├── images/   fotografías libres
├── app/      PWA offline con GPS y voz
└── scripts/  generador reproducible
```

## Usar la PWA

La app no necesita instalación: basta abrir `app/index.html` desde un servidor web. Para probarla en el ordenador:

```bash
cd Salamanca
python3 -m http.server 8080
```

Después abre `http://localhost:8080/app/`. Para usarla en el móvil con GPS debe publicarse bajo **HTTPS** (por ejemplo, GitHub Pages, Netlify o un servidor propio). Los navegadores bloquean normalmente la geolocalización en una dirección HTTP de red local.

En la primera visita:

1. abre la app con conexión;
2. pulsa **Activar GPS y audioguía**;
3. concede ubicación;
4. deja que termine de cargar las imágenes.

El service worker guarda la interfaz, el trazado, las fotografías y los textos. La voz es la síntesis de voz del propio dispositivo. Tras el primer toque, cada parada se reproduce al entrar en un radio aproximado de 45 m; también hay un botón manual. iOS/Android pueden imponer restricciones adicionales al audio en segundo plano.

## Regenerar los artefactos

El archivo fuente del trazado es `routes/dia1.geojson`, calculado con perfil peatonal/trekking de BRouter. El generador crea GPX, KML, mapa, iconos, datos de la app y PDF:

```bash
python3 scripts/build.py
```

## Comprobación importante

La ruta presupone que la recepción es en el **Colegio Arzobispo Fonseca, C/ Fonseca, 4**. Conviene verificar el lugar exacto en el programa del congreso antes de salir.

## Fuentes prácticas

- Hotel y dirección: [Zenit Hall88](https://hall88.zenithoteles.com/es/).
- Horario e historia del café: [Café Novelty](https://www.cafenovelty.com/).
- Dirección y uso actual de Fonseca: [Universidad de Salamanca](https://colegiofonseca.usal.es/).
- Datos del trazado: © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright), ruta calculada con [BRouter](https://brouter.de/).

## Fotografías y licencias

- `cafe-novelty.jpg`: Pravdaverita, Wikimedia Commons, CC BY 3.0.
- `plaza-mayor.jpg`: Anual, Wikimedia Commons, CC BY-SA 4.0.
- `casa-conchas.jpg`: Coralma*, Wikimedia Commons, CC0.
- `universidad.jpg`, `monterrey.jpg`, `fonseca.jpg`: Zarateman, Wikimedia Commons, CC0.

Las imágenes se conservan como archivos separados para facilitar su sustitución o ampliación en futuros días.

## Ampliación

La estructura admite `dia2`, `dia3` y rutas gastronómica, universitaria, nocturna o científica. Para cada nueva ruta se recomienda mantener el mismo patrón: GeoJSON fuente → GPX/KML → guiones Markdown → datos PWA → PDF.
