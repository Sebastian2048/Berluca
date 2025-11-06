service.create("Pluto TV", "plutotv", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://raw.githubusercontent.com/HelmerLuzo/PlutoTV_HL/main/tv/m3u/PlutoTV_tv_ES.m3u", "video", { title: "Pluto TV España" });
page.appendItem("https://raw.githubusercontent.com/HelmerLuzo/PlutoTV_HL/main/tv/m3u/PlutoTV_tv_MX.m3u", "video", { title: "Pluto TV México" });
page.appendItem("https://raw.githubusercontent.com/davplm/Listas/main/PLUTO%20TV.m3u", "video", { title: "Pluto TV Global" });