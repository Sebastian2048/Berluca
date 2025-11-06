service.create("Vix Latino", "vix", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://i.mjh.nz/Vix/mx.m3u8", "video", { title: "Vix Latino" });