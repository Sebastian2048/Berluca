service.create("Tubi TV", "tubi", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://i.mjh.nz/Tubi/mx.m3u8", "video", { title: "Tubi TV México" });