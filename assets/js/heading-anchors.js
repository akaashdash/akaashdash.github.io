// Add clickable anchor links to all headings in post content
document.addEventListener("DOMContentLoaded", function () {
  const content = document.getElementById("markdown-content");
  if (!content) return;

  content.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach(function (heading) {
    if (!heading.id) return;
    const anchor = document.createElement("a");
    anchor.className = "heading-anchor";
    anchor.href = "#" + heading.id;
    anchor.setAttribute("aria-label", "Link to this section");
    anchor.innerHTML = "#";

    // Scroll manually so heading sits just below the navbar (not 80px too low)
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const navbar = document.getElementById("navbar");
      const offset = navbar ? navbar.offsetHeight + 8 : 0;
      const top = heading.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top: top, behavior: "smooth" });
      history.pushState(null, "", "#" + heading.id);
    });

    heading.appendChild(anchor);
  });
});
