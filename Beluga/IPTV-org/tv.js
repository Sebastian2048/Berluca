service.create("IPTV-org", "iptvorg", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://iptv-org.github.io/iptv/languages/es.m3u", "video", { title: "IPTV-org Español" });