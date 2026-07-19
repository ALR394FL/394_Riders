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
      // FIXED: Read entries directly at the root level to match your automated photos.json
      const categories = Object.entries(data);
      let isFirstImage = true;

      categories.forEach(([slug, photos]) => {
        // Compute a clean human-readable title out of the folder slug name for headings
        let fallbackTitle = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());

        if (photos && photos.length > 0) {
          // 1. Create exactly ONE parent group card per category
          const groupCard = document.createElement("figure");
          
          // Preserves your feature layout toggle rule for the very first group card
          if (isFirstImage) {
            groupCard.className = "gallery-card wide";
            isFirstImage = false;
          } else {
            groupCard.className = "gallery-card";
          }

          // Build the card layout framework with an internal sub-grid to group matching images
          groupCard.innerHTML = `
            <figcaption>
              <strong>${photos[0].title || fallbackTitle}</strong>
              <span>Collection contains ${photos.length} item(s)</span>
            </figcaption>
            <!-- 📦 Inner sub-grid holding only the photos for this specific category card -->
            <div class="photo-stack"></div>
          `;

          galleryGrid.appendChild(groupCard);

          // Locate the photo-stack sub-container we just created inside this card
          const photoStack = groupCard.querySelector(".photo-stack");

          // 2. INNER LOOP: Iterate over all photos inside this specific album array
          photos.forEach(photo => {
            if (!photo.path) return;

            const imgElement = document.createElement("img");
            imgElement.src = photo.path;
            imgElement.alt = photo.caption || fallbackTitle;
            imgElement.title = photo.caption || ""; // Displays caption text cleanly on browser hover
            imgElement.loading = "lazy";

            // Append the picture element directly inside its parent card's stack container
            photoStack.appendChild(imgElement);
          });

        } else {
          // Fallback Block: Maintains your original empty folder logic without breaking changes
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
