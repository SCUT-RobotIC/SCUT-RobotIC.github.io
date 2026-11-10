/* RobotIC site — small, dependency-free interactions */
(function () {
  "use strict";

  document.documentElement.classList.add("js");

  /* ---------- mobile navigation ---------- */
  var nav = document.querySelector(".nav");
  var toggle = document.querySelector(".nav__toggle");

  if (nav && toggle) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    nav.addEventListener("click", function (e) {
      if (e.target.closest(".nav__links a")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- header state on scroll ---------- */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-stuck", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------- reveal on enter ---------- */
  var revealables = document.querySelectorAll("[data-reveal]");
  if (revealables.length) {
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              var el = entry.target;
              var delay = parseInt(el.getAttribute("data-reveal-delay") || "0", 10);
              window.setTimeout(function () {
                el.classList.add("is-in");
              }, delay);
              io.unobserve(el);
            }
          });
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.06 }
      );
      revealables.forEach(function (el) {
        io.observe(el);
      });
    } else {
      revealables.forEach(function (el) {
        el.classList.add("is-in");
      });
    }
  }

  /* ---------- tabs ---------- */
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll(".tab"));
    var panels = Array.prototype.slice.call(document.querySelectorAll("[data-panel]"));

    var select = function (id) {
      tabs.forEach(function (tab) {
        tab.setAttribute("aria-selected", tab.dataset.tab === id ? "true" : "false");
      });
      panels.forEach(function (panel) {
        var match = panel.dataset.panel === id;
        panel.hidden = !match;
        if (match) {
          panel.classList.remove("is-in");
          void panel.offsetWidth;
          panel.classList.add("is-in");
        }
      });
    };

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        select(tab.dataset.tab);
      });
    });

    if (tabs.length) {
      select(tabs[0].dataset.tab);
    }
  });

  /* ---------- lightbox ---------- */
  var lightbox = document.querySelector(".lightbox");
  if (lightbox) {
    var lbImg = lightbox.querySelector("img");
    var closeBtn = lightbox.querySelector(".lightbox__close");

    var close = function () {
      lightbox.classList.remove("is-open");
      document.body.style.overflow = "";
    };

    document.querySelectorAll("[data-lightbox]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        lbImg.src = btn.dataset.lightbox;
        lbImg.alt = btn.dataset.caption || "";
        lightbox.classList.add("is-open");
        document.body.style.overflow = "hidden";
      });
    });

    closeBtn.addEventListener("click", close);
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && lightbox.classList.contains("is-open")) close();
    });
  }

  /* ---------- footer year ---------- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
