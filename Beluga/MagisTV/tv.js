service.create("MagisTV", "magistv", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://raw.githubusercontent.com/Sunstar16/MagisTV-AS-A-m3u-PLAYLIST/main/MagisTV%2B.m3u", "video", { title: "MagisTV Principal" });
page.appendItem("https://raw.githubusercontent.com/Sunstar16/FULL-IPTV-CHANNEL-PLAYLIST/main/MagisTV%20(1).m3u", "video", { title: "MagisTV Alternativo" });