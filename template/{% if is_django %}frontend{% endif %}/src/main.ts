import "./main.css";
import { flashSwappedContent } from "./flash";

// htmx is vendored and loaded by base.html; here we only react to its events.
document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.target instanceof HTMLElement) {
    flashSwappedContent(event.target);
  }
});
