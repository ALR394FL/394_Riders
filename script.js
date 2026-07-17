document.addEventListener("DOMContentLoaded", () => {
  const mobileMenu = document.querySelector(".mobile-menu");
  
  if (mobileMenu) {
    // Force open/close behavior toggling on link selections
    const menuLinks = mobileMenu.querySelectorAll("nav a");
    menuLinks.forEach(link => {
      link.addEventListener("click", () => {
        mobileMenu.removeAttribute("open");
      });
    });
  }
});
