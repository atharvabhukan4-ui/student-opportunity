/**
 * Student Opportunity Discovery Platform
 * Client-side interactivity: Save toggle, Application tracker modal, Skill pill selector, Filter triggers.
 */

document.addEventListener("DOMContentLoaded", () => {
  initSaveToggles();
  initApplicationModals();
  initSkillTagSelector();
  initMobileNav();
  initDemoCredentials();
});

/**
 * Handles bookmark / save button toggles via REST API
 */
function initSaveToggles() {
  document.querySelectorAll(".btn-save-toggle").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const oppId = btn.getAttribute("data-id");
      if (!oppId) return;

      try {
        const response = await fetch("/api/save", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ opportunity_id: parseInt(oppId) }),
        });

        if (response.status === 401) {
          window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
          return;
        }

        const data = await response.json();
        if (data.status === "success") {
          if (data.is_saved) {
            btn.classList.add("saved");
            btn.setAttribute("title", "Remove from Saved");
            showToast("Opportunity bookmarked to your Saved list!", "success");
          } else {
            btn.classList.remove("saved");
            btn.setAttribute("title", "Save Opportunity");
            showToast("Removed from your Saved list.", "info");

            // If we are on the saved page, smoothly remove the card
            const savedCard = btn.closest(".saved-item-container");
            if (savedCard) {
              savedCard.style.transition = "opacity 0.3s ease, transform 0.3s ease";
              savedCard.style.opacity = "0";
              savedCard.style.transform = "scale(0.95)";
              setTimeout(() => savedCard.remove(), 300);
            }
          }
        }
      } catch (err) {
        console.error("Save error:", err);
        showToast("Error updating bookmark status.", "danger");
      }
    });
  });
}

/**
 * Handles Application Status tracking dialog & updates
 */
function initApplicationModals() {
  const modal = document.getElementById("applicationModal");
  if (!modal) return;

  const closeBtn = modal.querySelector(".modal-close");
  const cancelBtn = modal.querySelector(".modal-cancel");
  const form = document.getElementById("applicationStatusForm");
  const oppIdInput = document.getElementById("appModalOppId");
  const oppTitleElem = document.getElementById("appModalOppTitle");
  const statusSelect = document.getElementById("appModalStatusSelect");
  const notesText = document.getElementById("appModalNotes");

  const closeModal = () => {
    modal.classList.remove("active");
  };

  if (closeBtn) closeBtn.addEventListener("click", closeModal);
  if (cancelBtn) cancelBtn.addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  // Open modal trigger
  document.querySelectorAll(".btn-track-application").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const oppId = btn.getAttribute("data-id");
      const oppTitle = btn.getAttribute("data-title");
      const currentStatus = btn.getAttribute("data-status") || "Applied";

      oppIdInput.value = oppId;
      oppTitleElem.textContent = oppTitle;
      statusSelect.value = currentStatus;
      modal.classList.add("active");
    });
  });

  // Handle Form Submit
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const oppId = oppIdInput.value;
      const status = statusSelect.value;
      const notes = notesText ? notesText.value : "";

      try {
        const response = await fetch("/api/application", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            opportunity_id: parseInt(oppId),
            status: status,
            notes: notes,
          }),
        });

        if (response.status === 401) {
          window.location.href = "/login";
          return;
        }

        const data = await response.json();
        if (data.status === "success") {
          showToast(`Application updated to "${status}"!`, "success");
          closeModal();

          // Update trigger button status badge if visible
          const triggerBtn = document.querySelector(`.btn-track-application[data-id="${oppId}"]`);
          if (triggerBtn) {
            triggerBtn.setAttribute("data-status", status);
            triggerBtn.innerHTML = `<span>${status}</span>`;
          }

          // Reload if on applications or dashboard page to reflect counts
          if (
            window.location.pathname.includes("/applications") ||
            window.location.pathname.includes("/dashboard")
          ) {
            setTimeout(() => window.location.reload(), 600);
          }
        } else {
          showToast(data.message || "Failed to update application", "danger");
        }
      } catch (err) {
        console.error("Application tracking error:", err);
        showToast("Error updating application status.", "danger");
      }
    });
  }
}

/**
 * Click-to-add popular skills chips on Registration & Profile forms
 */
function initSkillTagSelector() {
  const skillsInput = document.getElementById("skillsInput");
  if (!skillsInput) return;

  document.querySelectorAll(".skill-chip-select").forEach((chip) => {
    chip.addEventListener("click", () => {
      const skillName = chip.getAttribute("data-skill");
      let currentSkills = skillsInput.value
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const index = currentSkills.findIndex(
        (s) => s.toLowerCase() === skillName.toLowerCase()
      );

      if (index === -1) {
        // Add skill
        currentSkills.push(skillName);
        chip.classList.add("active");
      } else {
        // Remove skill
        currentSkills.splice(index, 1);
        chip.classList.remove("active");
      }

      skillsInput.value = currentSkills.join(", ");
    });
  });
}

/**
 * Mobile Navigation Menu Drawer
 */
function initMobileNav() {
  const toggleBtn = document.querySelector(".mobile-menu-toggle");
  const navLinks = document.querySelector(".nav-links");

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener("click", () => {
      navLinks.classList.toggle("mobile-open");
    });
  }
}

/**
 * One-click demo credentials population for instant login testing
 */
function initDemoCredentials() {
  const fillStudentBtn = document.getElementById("fillStudentDemo");
  const fillAdminBtn = document.getElementById("fillAdminDemo");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");

  if (fillStudentBtn && emailInput && passwordInput) {
    fillStudentBtn.addEventListener("click", () => {
      emailInput.value = "student@college.edu";
      passwordInput.value = "student123";
    });
  }

  if (fillAdminBtn && emailInput && passwordInput) {
    fillAdminBtn.addEventListener("click", () => {
      emailInput.value = "admin@platform.com";
      passwordInput.value = "admin123";
    });
  }
}

/**
 * Toast Notification Utility
 */
function showToast(message, type = "info") {
  let toastContainer = document.getElementById("toastContainer");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toastContainer";
    toastContainer.style.position = "fixed";
    toastContainer.style.bottom = "24px";
    toastContainer.style.right = "24px";
    toastContainer.style.zIndex = "9999";
    toastContainer.style.display = "flex";
    toastContainer.style.flexDirection = "column";
    toastContainer.style.gap = "8px";
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  toast.className = `alert alert-${type}`;
  toast.style.margin = "0";
  toast.style.minWidth = "280px";
  toast.style.boxShadow = "0 8px 20px rgba(0,0,0,0.15)";
  toast.style.display = "flex";
  toast.style.justifyContent = "space-between";
  toast.style.alignItems = "center";
  toast.style.padding = "0.75rem 1.25rem";
  toast.style.borderRadius = "10px";

  toast.innerHTML = `
    <span>${message}</span>
    <button style="background:none; border:none; color:inherit; font-size:1.1rem; cursor:pointer; margin-left:12px;" onclick="this.parentElement.remove()">&times;</button>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}
