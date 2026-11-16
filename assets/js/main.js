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
/* ============================================
   Hero 轻量视差
   ============================================ */
(function initHeroParallax() {
  const heroMedia = document.querySelector('.hero__media');
  if (!heroMedia) return;

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isMobile = window.matchMedia('(max-width: 768px)').matches;
  if (prefersReduced || isMobile) return;

  let ticking = false;

  function updateParallax() {
    const scrollY = window.scrollY;
    // 视差幅度：背景图最多上移 50px
    const offset = Math.min(scrollY * 0.15, 50);
    heroMedia.style.transform = `translateY(${offset}px)`;
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(updateParallax);
      ticking = true;
    }
  }, { passive: true });
})();
/* ============================================
   鼠标跟随光晕
   ============================================ */
(function initCursorGlow() {
  const isDesktop = window.matchMedia('(min-width: 1025px)').matches;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!isDesktop || prefersReduced) return;

  const glow = document.createElement('div');
  glow.className = 'cursor-glow';
  document.body.appendChild(glow);

  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;
  let currentX = mouseX;
  let currentY = mouseY;

  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    glow.style.opacity = '1';
  });

  document.addEventListener('mouseleave', () => {
    glow.style.opacity = '0';
  });

  function animate() {
    // 平滑跟随：数值越小越“拖尾”，0.12 是比较克制的跟随感
    currentX += (mouseX - currentX) * 0.12;
    currentY += (mouseY - currentY) * 0.12;
    glow.style.transform = `translate(${currentX}px, ${currentY}px) translate(-50%, -50%)`;
    requestAnimationFrame(animate);
  }

  animate();
})();
