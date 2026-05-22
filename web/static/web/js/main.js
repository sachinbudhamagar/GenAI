// Show loading state on form submit so user knows something is happening
document.addEventListener("DOMContentLoaded", () => {
  ["searchForm", "optimizerForm"].forEach(id => {
    const form = document.getElementById(id);
    if (!form) return;
    form.addEventListener("submit", () => {
      const btn     = form.querySelector("button[type=submit]");
      const normal  = btn.querySelector(".btn-text");
      const loading = btn.querySelector(".btn-loading");
      if (normal)  normal.classList.add("hidden");
      if (loading) loading.classList.remove("hidden");
      btn.disabled = true;
    });
  });
});
