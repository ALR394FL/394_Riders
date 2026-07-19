document.addEventListener("DOMContentLoaded", () => {
    
    // Core function to inject standalone HTML files safely
    function injectComponent(elementId, filePath, callback) {
        const target = document.getElementById(elementId);
        if (!target) return;

        fetch(filePath)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error rendering ${filePath}`);
                return response.text();
            })
            .then(htmlData => {
                target.innerHTML = htmlData;
                // If a follow-up action is needed (like setting active styles), run it now
                if (callback) callback();
            })
            .catch(err => console.error("Component Loader Error:", err));
    }

    // Secondary function to match links with the active browser window address URL
    function highlightActiveLinks() {
        // Fallback to index.html if the path evaluates empty (root folder access)
        const currentPath = window.location.pathname.split("/").pop() || "index.html";
        
        // Find every link across both the mobile and desktop navigation modules
        const navLinks = document.querySelectorAll(".desktop-nav a, .mobile-menu nav a");
        
        navLinks.forEach(link => {
            const linkTarget = link.getAttribute("href");
            if (linkTarget === currentPath) {
                link.classList.add("active");
            } else {
                link.classList.remove("active");
            }
        });
    }

    // Execute layouts smoothly
    injectComponent("header-placeholder", "header.html", highlightActiveLinks);
    injectComponent("footer-placeholder", "footer.html");
});
