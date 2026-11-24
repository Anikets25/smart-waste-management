/**
 * script.js
 * ─────────
 * Global JavaScript for the Smart Waste Management System.
 *
 * Covers:
 *   • Mobile nav toggle (all pages)
 *   • Auto-dismiss flash messages
 *   • Active nav link highlighting (fallback for server-side logic)
 */

document.addEventListener("DOMContentLoaded", function () {

  // ── Mobile nav toggle ────────────────────────────────────────────────
  const navToggle = document.getElementById("navToggle");
  const navLinks  = document.getElementById("navLinks");

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      navLinks.classList.toggle("open");
      const isOpen = navLinks.classList.contains("open");
      navToggle.setAttribute("aria-expanded", isOpen);
    });

    // Close nav when any link inside it is clicked (better mobile UX)
    navLinks.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        navLinks.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });

    // Close nav when clicking outside of it
    document.addEventListener("click", function (e) {
      if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }


  // ── Auto-dismiss flash messages after 5 seconds ──────────────────────
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach(function (flash) {
    setTimeout(function () {
      flash.style.transition = "opacity .4s ease";
      flash.style.opacity    = "0";
      setTimeout(function () {
        if (flash.parentNode) flash.remove();
      }, 400);
    }, 5000);
  });


  // ── Active nav link highlight (client-side fallback) ─────────────────
  // The base.html template sets the 'active' class server-side using
  // request.endpoint. This JS handles edge cases where the endpoint name
  // doesn't match a nav link exactly.
  const currentPath = window.location.pathname;
  document.querySelectorAll(".nav-link").forEach(function (link) {
    const href = link.getAttribute("href");
    if (href && href !== "/" && currentPath.startsWith(href)) {
      link.classList.add("active");
    }
  });

});
