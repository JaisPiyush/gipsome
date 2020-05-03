// The basic js libraries needed by every servie page

export function configure() {
  let head = document.getElementsByTagName("HEAD")[0];
  let axios_script = document.createElement("SCRIPT");
  axios_script.setAttribute("src", "https://unpkg.com/axios/dist/axios.min.js");
  axios_script.innerText = 'import axios from "axios;\n';
  head.appendChild(axios_script);
}
