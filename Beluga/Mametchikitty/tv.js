service.create("Mametchikitty", "mametchikitty", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://raw.githubusercontent.com/mametchikitty/IPTV/main/lista.m3u", "video", { title: "Mametchikitty Lista" });