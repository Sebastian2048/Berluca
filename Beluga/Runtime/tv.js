service.create("Runtime TV", "runtime", "video", true);
var page = require("showtime/page");
page.contents = "video";
page.appendItem("https://raw.githubusercontent.com/HelmerLuzo/RuntimeTV/main/tv/m3u/RuntimeTV_ES.m3u", "video", { title: "Runtime TV España" });