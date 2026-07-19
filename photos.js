document.addEventListener("DOMContentLoaded", () => {
  const galleryGrid = document.querySelector(".gallery-grid");
  if (!galleryGrid) return;
  
  galleryGrid.innerHTML = "";

  fetch("photos.json")
    .then(response => {
      if (!response.ok) throw new Error("Catalog index file corrupt or missing");
      return response.json();
    })
    .then(data => {
      let cleanAlbums = {};

      // 🔍 SMART AUTO-DETECTOR: Check if the JSON is using the old format or the new format
      if (data.albums && data.categoryOrder) {
        // OLD DATA FORMAT: Extract the nested image folder dictionary directly
        cleanAlbums = data.albums;
      } else {
        // NEW AUTOMATED DATA FORMAT: The entire JSON file is already our album list
        cleanAlbums = data;
      }

      let isFirstImage = true;

      // Iterate only through valid photo collections
      Object.entries(cleanAlbums).forEach(([slug, photos]) => {
        
        // 🛡️ CRITICAL SAFETY SKIP: Ignore old system helper keys so they never create blank cards
        if (slug === "categoryOrder" || slug === "albums") return;
        
        // Skip over anything that isn't a list of items
        if (!Array.isArray(photos)) return;

        // Auto-convert folder slug text into clean title text (e.g. "chapter-rides" -> "Chapter Rides")
        let fallbackTitle = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());

        if (photos.length > 0) {
          // 1. Build exactly ONE figure card frame per category collection block
          const groupCard = document.createElement("figure");
          
																					
          if (isFirstImage) {
            groupCard.className = "gallery-card wide";
            isFirstImage = false;
          } else {
            groupCard.className = "gallery-card";
          }

          // Safely target the title property from the first image object, or use our clean fallback string
          const humanTitle = photos[0].title || fallbackTitle;

          groupCard.innerHTML = `
            <figcaption>
              <strong>${humanTitle}</strong>
              <span>Collection contains ${photos.length} item(s)</span>
            </figcaption>
            <!-- 📦 Sub-grid placeholder frame to loop matching image blocks safely -->
            <div class="photo-stack"></div>
          `;

          galleryGrid.appendChild(groupCard);

          // Select the inner image frame wrapper we just created inside this specific block
          const photoStack = groupCard.querySelector(".photo-stack");

          // 2. INNER LOOP: Iterate over all photos inside this specific album array
          photos.forEach(photo => {
            if (!photo.path) return;

            const imgElement = document.createElement("img");
            imgElement.src = photo.path;
            // Gracefully default to the image caption, title layout, or clean folder metadata text
            imgElement.alt = photo.caption || photo.title || fallbackTitle;
            imgElement.title = photo.caption || photo.title || ""; // Browser text tooltip on hover
            imgElement.loading = "lazy";

            // Drop the image item node smoothly inside its parent category card track frame
            photoStack.appendChild(imgElement);
          });

        } else {
          // Fallback Block: Keeps your default placeholder styling active if an album is completely empty
          const groupCard = document.createElement("figure");
          groupCard.className = "gallery-card";
          groupCard.innerHTML = `
            <div class="photo-placeholder">
              <span>394</span>
              <small>Photo placeholder</small>
            </div>
            <figcaption>
              <strong>${fallbackTitle}</strong>
              <span>Photos coming soon</span>
            </figcaption>
          `;
          galleryGrid.appendChild(groupCard);
        }
      });
    })
    .catch(error => {
      console.error("Error drawing structured grid array layout elements:", error);
    });
});
