import {
    initializeHomePage
}
from "./pages/home.js";

document.addEventListener(
    "DOMContentLoaded",
    async()=>{

        await initializeHomePage();

    }
);