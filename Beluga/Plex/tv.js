service.create("Plex TV", "plex", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://i.mjh.nz/Plex/mx.m3u8", "video", { title: "Plex TV México" });