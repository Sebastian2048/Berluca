import os

# Estructura base
carpetas = [
    "MagisTV", "Mametchikitty", "IPTV-org", "PlutoTV",
    "Tubi", "Plex", "Runtime", "Vix"
]

tvjs_contenido = {
    "MagisTV": '''service.create("MagisTV", "magistv", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://raw.githubusercontent.com/Sunstar16/MagisTV-AS-A-m3u-PLAYLIST/main/MagisTV%2B.m3u", "video", { title: "MagisTV Principal" });
page.appendItem("https://raw.githubusercontent.com/Sunstar16/FULL-IPTV-CHANNEL-PLAYLIST/main/MagisTV%20(1).m3u", "video", { title: "MagisTV Alternativo" });''',

    "Mametchikitty": '''service.create("Mametchikitty", "mametchikitty", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://raw.githubusercontent.com/mametchikitty/IPTV/main/lista.m3u", "video", { title: "Mametchikitty Lista" });''',

    "IPTV-org": '''service.create("IPTV-org", "iptvorg", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://iptv-org.github.io/iptv/languages/es.m3u", "video", { title: "IPTV-org Español" });''',

    "PlutoTV": '''service.create("Pluto TV", "plutotv", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://raw.githubusercontent.com/HelmerLuzo/PlutoTV_HL/main/tv/m3u/PlutoTV_tv_ES.m3u", "video", { title: "Pluto TV España" });
page.appendItem("https://raw.githubusercontent.com/HelmerLuzo/PlutoTV_HL/main/tv/m3u/PlutoTV_tv_MX.m3u", "video", { title: "Pluto TV México" });
page.appendItem("https://raw.githubusercontent.com/davplm/Listas/main/PLUTO%20TV.m3u", "video", { title: "Pluto TV Global" });''',

    "Tubi": '''service.create("Tubi TV", "tubi", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://i.mjh.nz/Tubi/mx.m3u8", "video", { title: "Tubi TV México" });''',

    "Plex": '''service.create("Plex TV", "plex", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://i.mjh.nz/Plex/mx.m3u8", "video", { title: "Plex TV México" });''',

    "Runtime": '''service.create("Runtime TV", "runtime", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://raw.githubusercontent.com/HelmerLuzo/RuntimeTV/main/tv/m3u/RuntimeTV_ES.m3u", "video", { title: "Runtime TV España" });''',

    "Vix": '''service.create("Vix Latino", "vix", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://i.mjh.nz/Vix/mx.m3u8", "video", { title: "Vix Latino" });'''
}

# Crear carpetas y archivos tv.js
os.makedirs("Beluga", exist_ok=True)
for carpeta in carpetas:
    ruta = os.path.join("Beluga", carpeta)
    os.makedirs(ruta, exist_ok=True)
    with open(os.path.join(ruta, "tv.js"), "w", encoding="utf-8") as f:
        f.write(tvjs_contenido[carpeta])

# plugin.json
with open("Beluga/plugin.json", "w", encoding="utf-8") as f:
    f.write('''{
  "id": "beluga.plugin",
  "type": "video",
  "title": "Beluga — Infraestructura de Emisión Autónoma",
  "icon": "plugin.png",
  "author": "Proyecto Beluga",
  "version": "1.0",
  "description": "Plugin educativo que organiza fuentes audiovisuales públicas en español. Este proyecto no aloja ni distribuye contenido, y se ofrece con fines exclusivamente educativos y experimentales.",
  "homepage": ""
}''')

# README.md
with open("Beluga/README.md", "w", encoding="utf-8") as f:
    f.write("## Beluga — Infraestructura de Emisión Autónoma\n\nEste plugin educativo para Movian organiza fuentes audiovisuales públicas en español. No aloja ni distribuye contenido. Uso exclusivamente educativo, técnico y comunitario.\n\nInstalación: https://raw.githubusercontent.com/TU_USUARIO/Beluga/main/plugin.json")

# LICENSE.md
with open("Beluga/LICENSE.md", "w", encoding="utf-8") as f:
    f.write("Licencia CC BY-NC 4.0 — Uso educativo, no comercial. Proyecto Beluga. No se aloja ni distribuye contenido audiovisual.")

# MANIFIESTO.md
with open("Beluga/MANIFIESTO.md", "w", encoding="utf-8") as f:
    f.write("Beluga es una arquitectura simbólica de autonomía audiovisual. Cada carpeta es una puerta. Cada ícono, una declaración de presencia. Uso legítimo para investigación, aprendizaje y desarrollo técnico.")

print("✅ Proyecto Beluga generado con éxito.")
