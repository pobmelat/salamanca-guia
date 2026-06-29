#!/usr/bin/env python3
"""Build the Day 1 route artifacts from the routed GeoJSON."""

from __future__ import annotations

import html
import json
import math
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image as RLImage, KeepTogether, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]

STOPS = [
    dict(id=1, time="17:00", name="Zenit Hall88", short="Salida", lat=40.9702112, lon=-5.6766756,
         kind="start", minutes=0, image=None,
         desc="Salida puntual. Observa el cambio del barrio universitario al casco histórico."),
    dict(id=2, time="17:24", name="Café Novelty", short="Café", lat=40.9653616, lon=-5.6636406,
         kind="cafe", minutes=21, image="cafe-novelty.jpg",
         desc="Pausa de 20-25 min en el café histórico fundado en 1905."),
    dict(id=3, time="17:45", name="Plaza Mayor", short="Plaza Mayor", lat=40.9650282, lon=-5.6640558,
         kind="monument", minutes=8, image="plaza-mayor.jpg",
         desc="Primera lectura del gran salón barroco de la ciudad."),
    dict(id=4, time="17:57", name="Casa de las Conchas", short="Conchas", lat=40.9629585, lon=-5.6656516,
         kind="monument", minutes=8, image="casa-conchas.jpg",
         desc="Fachada exterior y diálogo visual con la Clerecía."),
    dict(id=5, time="18:10", name="Universidad - Patio de Escuelas", short="Universidad", lat=40.9614420, lon=-5.6672180,
         kind="monument", minutes=12, image="universidad.jpg",
         desc="Fachada plateresca, Fray Luis de León y el juego de la rana."),
    dict(id=6, time="18:28", name="Palacio de Monterrey", short="Monterrey", lat=40.96445, lon=-5.66859,
         kind="photo", minutes=5, image="monterrey.jpg",
         desc="Pausa fotográfica breve ante la crestería renacentista."),
    dict(id=7, time="18:40", name="Colegio Arzobispo Fonseca", short="Fonseca", lat=40.9652569, lon=-5.6701508,
         kind="finish", minutes=5, image="fonseca.jpg",
         desc="Fin de ruta y entrada a la recepción. Confirmar el lugar en el programa."),
]

PHOTO_CREDITS = {
    "cafe-novelty.jpg": "Pravdaverita / Wikimedia Commons / CC BY 3.0",
    "plaza-mayor.jpg": "Anual / Wikimedia Commons / CC BY-SA 4.0",
    "casa-conchas.jpg": "Coralma* / Wikimedia Commons / CC0",
    "universidad.jpg": "Zarateman / Wikimedia Commons / CC0",
    "monterrey.jpg": "Zarateman / Wikimedia Commons / CC0",
    "fonseca.jpg": "Zarateman / Wikimedia Commons / CC0",
}

PHOTO_TIPS = {
    2: "Interior: estatua de Torrente Ballester. Exterior: soportales hacia E-NE. 17:24.",
    3: "Desde el centro hacia el Ayuntamiento, o usando un arco como marco. 17:45.",
    4: "Desde la Clerecía, diagonal hacia O-SO; mejor para el ritmo de las conchas. 17:57.",
    5: "Fray Luis en primer plano y fachada al oeste. Zoom para los relieves. 18:10.",
    6: "Desde el SE hacia la torre y crestería, orientación NO. 18:28.",
    7: "Desde la acera opuesta, fachada frontal o lateral discreta. 18:40.",
}

FACTS = {
    2: "Novelty abrió en 1905 y conserva la memoria de las tertulias culturales salmantinas.",
    3: "El conjunto barroco se construyó en el siglo XVIII y sus soportales forman una galería de medallones.",
    4: "El palacio, de finales del XV y comienzos del XVI, reúne más de 300 conchas esculpidas.",
    5: "La Universidad remonta su origen a 1218; su fachada plateresca es una lectura en piedra del siglo XVI.",
    6: "Iniciado en 1539, el edificio quedó muy por debajo del proyecto original y aun así creó un estilo.",
    7: "Las obras de Fonseca comenzaron en 1519; hoy sigue ligado a la vida universitaria y cultural.",
}

SPEECH = {
    1: "Empieza sin prisa. Esta tarde no vamos a hacer Salamanca: vamos a aprender a leerla. Camina hacia el centro y observa cómo la piedra dorada va sustituyendo a la ciudad moderna.",
    2: "Has llegado al descanso justo en el momento bueno. Novelty abrió en 1905. Busca dentro a Gonzalo Torrente Ballester, sentado como un cliente más, y reserva unos veinte minutos para el café.",
    3: "Esta vez la Plaza Mayor es la puerta de entrada, no el gran final. Colócate en el centro y gira despacio. Parece un cuadrado perfecto, aunque no lo sea.",
    4: "No mires solo las conchas. Fíjate también en las rejas, la portada y las torres de la Clerecía. La leyenda dice que una de las conchas esconde un tesoro.",
    5: "Ponte cerca de Fray Luis y recorre la fachada de abajo arriba. La rana está sobre una calavera, pero no dejes que el juego te impida mirar el conjunto.",
    6: "Esta es una pausa breve. Mira la crestería, las torres y las chimeneas. El palacio es solo una parte del proyecto original, pero bastó para influir en muchos edificios posteriores.",
    7: "La ruta termina aquí, justo cuando empieza la recepción. Has cruzado desde la Salamanca contemporánea hasta uno de sus antiguos colegios mayores. Antes de entrar, mira la portada sin prisa.",
}


def load_route():
    data = json.loads((ROOT / "routes/dia1.geojson").read_text())
    feature = data["features"][0]
    coords = feature["geometry"]["coordinates"]
    return [(float(p[0]), float(p[1])) for p in coords], feature["properties"]


def haversine(a, b):
    lon1, lat1 = a; lon2, lat2 = b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2-lat1), math.radians(lon2-lon1)
    h = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlambda/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(h), math.sqrt(1-h))


def nearest_route_index(coords, stop):
    target = (stop["lon"], stop["lat"])
    return min(range(len(coords)), key=lambda i: haversine(coords[i], target))


def segment_distances(coords):
    idx = [nearest_route_index(coords, s) for s in STOPS]
    idx[0], idx[-1] = 0, len(coords)-1
    distances = []
    for a, b in zip(idx, idx[1:]):
        if b < a: b = a
        distances.append(sum(haversine(coords[i], coords[i+1]) for i in range(a, b)))
    return distances


def write_gpx(coords):
    ns = "http://www.topografix.com/GPX/1/1"
    register_namespace("", ns)
    gpx = Element(f"{{{ns}}}gpx", version="1.1", creator="Guía Salamanca V1")
    for s in STOPS:
        w = SubElement(gpx, f"{{{ns}}}wpt", lat=str(s["lat"]), lon=str(s["lon"]))
        SubElement(w, f"{{{ns}}}name").text = f'{s["id"]:02d} {s["short"]}'
        SubElement(w, f"{{{ns}}}desc").text = f'{s["time"]} - {s["desc"]}'
        SubElement(w, f"{{{ns}}}sym").text = s["kind"]
    trk = SubElement(gpx, f"{{{ns}}}trk")
    SubElement(trk, f"{{{ns}}}name").text = "Día 1 - Hotel a Fonseca"
    seg = SubElement(trk, f"{{{ns}}}trkseg")
    for lon, lat in coords:
        SubElement(seg, f"{{{ns}}}trkpt", lat=f"{lat:.7f}", lon=f"{lon:.7f}")
    ElementTree(gpx).write(ROOT / "routes/dia1.gpx", encoding="utf-8", xml_declaration=True)


def write_kml(coords):
    ns = "http://www.opengis.net/kml/2.2"
    register_namespace("", ns)
    kml = Element(f"{{{ns}}}kml"); doc = SubElement(kml, f"{{{ns}}}Document")
    SubElement(doc, f"{{{ns}}}name").text = "Salamanca - Día 1"
    style_colors = {"start":"ff335c67", "cafe":"ff3565c4", "monument":"ff317c46", "photo":"ff9c5a26", "finish":"ff673ab7", "viewpoint":"ffb56a00"}
    hrefs = {"start":"http://maps.google.com/mapfiles/kml/paddle/wht-circle.png", "cafe":"http://maps.google.com/mapfiles/kml/paddle/orange-circle.png", "monument":"http://maps.google.com/mapfiles/kml/paddle/grn-circle.png", "photo":"http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png", "finish":"http://maps.google.com/mapfiles/kml/paddle/purple-circle.png", "viewpoint":"http://maps.google.com/mapfiles/kml/paddle/blu-circle.png"}
    for kind, color in style_colors.items():
        st = SubElement(doc, f"{{{ns}}}Style", id=kind)
        iconst = SubElement(st, f"{{{ns}}}IconStyle"); SubElement(iconst, f"{{{ns}}}color").text = color
        icon = SubElement(iconst, f"{{{ns}}}Icon"); SubElement(icon, f"{{{ns}}}href").text = hrefs[kind]
    route_style = SubElement(doc, f"{{{ns}}}Style", id="route")
    line = SubElement(route_style, f"{{{ns}}}LineStyle"); SubElement(line, f"{{{ns}}}color").text = "ff6a5634"; SubElement(line, f"{{{ns}}}width").text = "5"
    for s in STOPS:
        pm = SubElement(doc, f"{{{ns}}}Placemark")
        SubElement(pm, f"{{{ns}}}name").text = f'{s["id"]:02d} · {s["name"]}'
        SubElement(pm, f"{{{ns}}}description").text = f'{s["time"]} - {s["desc"]}'
        SubElement(pm, f"{{{ns}}}styleUrl").text = f'#{s["kind"]}'
        point = SubElement(pm, f"{{{ns}}}Point"); SubElement(point, f"{{{ns}}}coordinates").text = f'{s["lon"]},{s["lat"]},0'
    pm = SubElement(doc, f"{{{ns}}}Placemark"); SubElement(pm, f"{{{ns}}}name").text = "Recorrido peatonal"
    SubElement(pm, f"{{{ns}}}styleUrl").text = "#route"; ls = SubElement(pm, f"{{{ns}}}LineString")
    SubElement(ls, f"{{{ns}}}tessellate").text = "1"
    SubElement(ls, f"{{{ns}}}coordinates").text = " ".join(f"{x},{y},0" for x,y in coords)
    ElementTree(kml).write(ROOT / "routes/dia1.kml", encoding="utf-8", xml_declaration=True)


def write_map(coords):
    xs = [p[0] for p in coords]; ys = [p[1] for p in coords]
    W, H, pad = 1800, 1400, 145
    im = Image.new("RGB", (W, H), "#f4efe4"); draw = ImageDraw.Draw(im)
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    bold_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    title_font = ImageFont.truetype(bold_path, 55); sub_font = ImageFont.truetype(font_path, 27)
    label_font = ImageFont.truetype(bold_path, 25); num_font = ImageFont.truetype(bold_path, 24); note_font = ImageFont.truetype(font_path, 20)
    minx, maxx = min(xs)-.0015, max(xs)+.0017; miny, maxy = min(ys)-.0010, max(ys)+.0013
    map_top, map_bottom = 190, H-105
    def pt(lon, lat):
        x = pad + (lon-minx)/(maxx-minx)*(W-2*pad)
        y = map_bottom - (lat-miny)/(maxy-miny)*(map_bottom-map_top)
        return (round(x), round(y))
    points = [pt(x,y) for x,y in coords]
    draw.line(points, fill="#b9aa8d", width=27, joint="curve")
    draw.line(points, fill="#334f49", width=11, joint="curve")
    colors_map = {"start":"#334f49", "cafe":"#c4633b", "monument":"#2e6a54", "photo":"#c28b2c", "finish":"#6a4777"}
    offsets = [(30,18),(30,22),(30,-58),(30,-58),(30,-58),(30,18),(30,18)]
    for s, off in zip(STOPS, offsets):
        x,y = pt(s["lon"],s["lat"]); r=28
        draw.ellipse((x-r-4,y-r-4,x+r+4,y+r+4), fill="white")
        draw.ellipse((x-r,y-r,x+r,y+r), fill=colors_map[s["kind"]])
        t=str(s["id"]); box=draw.textbbox((0,0),t,font=num_font); draw.text((x-(box[2]-box[0])/2,y-(box[3]-box[1])/2-2),t,font=num_font,fill="white")
        label=f'{s["time"]}  {s["short"]}'; lx,ly=x+off[0],y+off[1]
        box=draw.textbbox((lx,ly),label,font=label_font); draw.rounded_rectangle((box[0]-7,box[1]-4,box[2]+7,box[3]+4),radius=7,fill="#f4efe4dd")
        draw.text((lx,ly),label,font=label_font,fill="#25332f")
    draw.text((pad,42),"DÍA 1 · DE HALL88 A FONSECA",font=title_font,fill="#25332f")
    draw.text((pad,112),"17:00–18:45 · 3,45 km · final en la recepción",font=sub_font,fill="#6f6557")
    draw.text((pad,H-52),"Trazado: BRouter/OpenStreetMap. Mapa esquemático; sigue siempre la señalización peatonal.",font=note_font,fill="#776f63")
    im.save(ROOT / "maps/mapa.png", optimize=True)


def make_icons():
    for size in (192, 512):
        im = Image.new("RGB", (size, size), "#f4efe4")
        d = ImageDraw.Draw(im)
        pad = size // 8
        d.rounded_rectangle((pad,pad,size-pad,size-pad), radius=size//7, fill="#334f49")
        d.ellipse((size*.31,size*.18,size*.69,size*.56), fill="#c4633b")
        d.polygon([(size*.5,size*.82),(size*.34,size*.48),(size*.66,size*.48)], fill="#c4633b")
        d.ellipse((size*.43,size*.30,size*.57,size*.44), fill="#f4efe4")
        im.save(ROOT / f"app/icon-{size}.png")


def write_app_data(coords):
    payload = {
        "meta": {"title":"Salamanca · Día 1", "distance":"3,45 km", "window":"17:00–18:45", "geofenceMeters":45},
        "route": [[round(lon,7), round(lat,7)] for lon,lat in coords],
        "stops": [{**s, "speech":SPEECH[s["id"]], "image": ("../images/"+s["image"] if s["image"] else None)} for s in STOPS],
    }
    (ROOT / "app/data.js").write_text("window.GUIDE_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")


def footer(canvas, doc):
    canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#d9cfbd")); canvas.line(18*mm, 14*mm, 192*mm, 14*mm)
    canvas.setFont("Helvetica", 7.5); canvas.setFillColor(colors.HexColor("#766f65"))
    canvas.drawString(18*mm, 9*mm, "SALAMANCA · DÍA 1 · 17:00–18:45")
    canvas.drawRightString(192*mm, 9*mm, str(doc.page)); canvas.restoreState()


def write_pdf(distances):
    out = ROOT / "pdf/guia_dia1.pdf"
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=17*mm, bottomMargin=18*mm, title="Guía Salamanca - Día 1")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=footer))
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=29, textColor=colors.HexColor("#25332f"), alignment=TA_LEFT, spaceAfter=7*mm)
    h1 = ParagraphStyle("H1X", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=21, textColor=colors.HexColor("#25332f"), spaceBefore=2*mm, spaceAfter=4*mm)
    h2 = ParagraphStyle("H2X", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.5, leading=15, textColor=colors.HexColor("#7a4b32"), spaceAfter=2*mm)
    body = ParagraphStyle("BodyX", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=13, textColor=colors.HexColor("#34342f"), spaceAfter=2.5*mm)
    small = ParagraphStyle("SmallX", parent=body, fontSize=7.2, leading=9, textColor=colors.HexColor("#6f685d"))
    callout = ParagraphStyle("Callout", parent=body, fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=colors.white, backColor=colors.HexColor("#334f49"), borderPadding=8, spaceBefore=3*mm, spaceAfter=4*mm)
    story = []
    story += [Spacer(1,12*mm), Paragraph("SALAMANCA, SIN PRISA", title), Paragraph("Día 1 · Del hotel a la recepción de Fonseca", h1),
              Paragraph("Una primera lectura de la ciudad: café temprano, piedra dorada y universidad. El paseo termina a las 18:45; no incluye regreso al hotel.", callout),
              RLImage(str(ROOT/"maps/mapa.png"), width=174*mm, height=132*mm), Spacer(1,3*mm),
              Paragraph("3,45 km · 45–50 min andando · 20–25 min de café · cinco pausas cortas", h2),
              Paragraph("Plan de seguridad horaria: si sales después de las 17:05, reduce la Plaza Mayor a una fotografía y omite Monterrey. Fonseca tiene prioridad.", body), PageBreak()]
    story += [Paragraph("Horario recomendado", h1)]
    rows = [["Hora", "Parada", "Pausa", "Siguiente tramo"]]
    for i,s in enumerate(STOPS):
        next_txt = "Fin"
        if i < len(distances):
            mins = max(1, round(distances[i]/75))
            next_txt = f"{distances[i]/1000:.2f} km · {mins} min"
        rows.append([s["time"], s["name"], (f'{s["minutes"]} min' if s["minutes"] else "Salida"), next_txt])
    tab = Table(rows, colWidths=[20*mm,73*mm,25*mm,48*mm], repeatRows=1)
    tab.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#334f49")), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),8.5), ("LEADING",(0,0),(-1,-1),11),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#f6f1e7"),colors.white]),
        ("GRID",(0,0),(-1,-1),0.25,colors.HexColor("#d7cdbb")), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),6), ("RIGHTPADDING",(0,0),(-1,-1),6), ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ])); story += [tab, Spacer(1,6*mm), Paragraph("Dos decisiones deliberadas", h2),
                    Paragraph("El café va al principio (17:24 aprox.), tal como pediste. Puente Romano, Tormes, Huerto, Casa Lis y catedrales quedan fuera: intentar añadirlos rompería la llegada a Fonseca y convertiría el paseo en una carrera.", body),
                    Paragraph("La Plaza Mayor aparece pronto y brevemente. Volver otro día al atardecer permitirá verla como destino, no como cruce.", body),
                    Paragraph("Importante", h2), Paragraph("La guía presupone que la recepción se celebra en el Colegio Arzobispo Fonseca, C/ Fonseca, 4. Confírmalo en el programa del congreso antes de salir.", callout), PageBreak()]
    for s in STOPS[1:]:
        img = ROOT/"images"/s["image"]
        with Image.open(img) as im:
            iw, ih = im.size
        maxw, maxh = 82*mm, 57*mm
        scale = min(maxw/iw, maxh/ih)
        photo = RLImage(str(img), width=iw*scale, height=ih*scale)
        content = [Paragraph(f'{s["time"]} · {html.escape(s["name"])}', h2), Paragraph(FACTS[s["id"]], body),
                   Paragraph("Fotografía", h2), Paragraph(PHOTO_TIPS[s["id"]], body),
                   Paragraph(f'Pausa prevista: {s["minutes"]} min.', small)]
        card = Table([[photo, content]], colWidths=[88*mm,78*mm], hAlign="LEFT")
        card.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(0,0),0),("RIGHTPADDING",(0,0),(0,0),6*mm),
                                       ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#d7cdbb")),("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#fbf8f1")),
                                       ("TOPPADDING",(0,0),(-1,-1),4*mm),("BOTTOMPADDING",(0,0),(-1,-1),4*mm),("RIGHTPADDING",(1,0),(1,0),4*mm)]))
        story += [KeepTogether([card, Paragraph("Foto: "+PHOTO_CREDITS[s["image"]], small), Spacer(1,7*mm)])]
        if s["id"] in (3,5): story.append(PageBreak())
    story += [PageBreak(), Paragraph("Consejos prácticos", h1),
              Paragraph("• Activa la ubicación y el audio de la PWA antes de salir del hotel. Los navegadores suelen exigir un primer toque para permitir sonido automático.", body),
              Paragraph("• Lleva calzado estable: hay adoquines y algún tramo irregular. Cruza las avenidas por pasos señalizados, aunque el GPS sugiera una línea más directa.", body),
              Paragraph("• Si Novelty está lleno, limita la espera a cinco minutos. Un café en barra mantiene el horario; la prioridad es llegar a Fonseca.", body),
              Paragraph("• Descarga la PWA y abre el mapa una vez con conexión. La ruta, textos, imágenes y mapa esquemático quedan disponibles sin red.", body),
              Paragraph("Fuentes y créditos", h1),
              Paragraph("Trazado calculado con BRouter sobre datos OpenStreetMap. Direcciones y datos prácticos contrastados con las webs oficiales de Zenit Hall88, Café Novelty y Universidad de Salamanca/Colegio Fonseca. Fotografías procedentes de Wikimedia Commons; autores y licencias se indican junto a cada imagen.", body),
              Paragraph("Esta guía es orientativa. Obras, eventos y accesos peatonales pueden alterar el recorrido.", small)]
    doc.build(story)


def main():
    coords, props = load_route()
    distances = segment_distances(coords)
    write_gpx(coords); write_kml(coords); write_map(coords); make_icons(); write_app_data(coords); write_pdf(distances)
    print(json.dumps({"route_points":len(coords), "track_m":round(sum(haversine(coords[i],coords[i+1]) for i in range(len(coords)-1))), "segments_m":[round(x) for x in distances]}, ensure_ascii=False))


if __name__ == "__main__": main()
