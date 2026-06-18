(function () {
  const PLATFORM_LABELS = {
    android: "Android",
    ios: "iPhone / iPad",
    windows: "Windows",
    mac: "Mac",
  };

  const overlay = document.getElementById("deviceAddOverlay");
  const overlayTitle = document.getElementById("deviceAddOverlayTitle");

  function loadingMessage(platform) {
    const name = PLATFORM_LABELS[platform] || "устройства";
    if (platform === "android" || platform === "windows") {
      return "Создаём ключ для " + name + "…";
    }
    return "Создаём файл настроек для " + name + "…";
  }

  function showOverlay(message) {
    if (!overlay) return;
    if (overlayTitle) overlayTitle.textContent = message;
    overlay.hidden = false;
    overlay.setAttribute("aria-hidden", "false");
    overlay.classList.add("is-visible");
    document.body.classList.add("device-add-loading");
  }

  document.querySelectorAll(".js-device-add-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const submitter = event.submitter;
      if (!submitter || submitter.name !== "platform") return;

      showOverlay(loadingMessage(submitter.value));
      form.querySelectorAll("button[type='submit']").forEach((btn) => {
        btn.disabled = true;
        btn.classList.add("is-loading");
      });
    });
  });

  document.querySelectorAll(".device-created-banner").forEach((banner) => {
    banner.classList.add("is-entering");
    window.setTimeout(() => banner.classList.remove("is-entering"), 600);
    window.setTimeout(() => {
      banner.classList.add("is-leaving");
      window.setTimeout(() => banner.remove(), 400);
    }, 8000);
  });
})();
