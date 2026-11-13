const FLASH_CLASSES = ["text-sky-600", "transition-colors", "duration-700"];
const FLASH_MS = 700;

/** Briefly highlight elements marked with `data-flash` after htmx swaps them in. */
export function flashSwappedContent(root: HTMLElement): void {
  const targets = root.matches("[data-flash]")
    ? [root]
    : Array.from(root.querySelectorAll<HTMLElement>("[data-flash]"));
  for (const target of targets) {
    target.classList.add(...FLASH_CLASSES);
    window.setTimeout(() => target.classList.remove("text-sky-600"), FLASH_MS);
  }
}
