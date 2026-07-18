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
      // Extract both variables directly from the dynamic JSON layout
      const categoryOrder = data.categoryOrder || [];
      const albums = data.albums || {};
      
      let isFirstImage = true;

      categoryOrder.forEach(slug => {
        // Read directly from the albums sub-object
        const photos = albums[slug] || [];

        if (photos.length > 0) {
          photos.forEach(photo => {
            const card = document.createElement("figure");
            
            if (isFirstImage) {
              card.className = "gallery-card wide";
              isFirstImage = false;
            } else {
              card.className = "gallery-card";
            }

            card.innerHTML = `
              <img src="${photo.path}" alt="${photo.title}" loading="lazy"/>
              <figcaption>
                <strong>${photo.title}</strong>
                <span>${photo.caption}</span>
              </figcaption>
            `;
            galleryGrid.appendChild(card);
          });
        } else {
          // Fallback Block: Auto-converts slugs to Title Case text titles
          let fallbackTitle = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());
          const card = document.createElement("figure");
          card.className = "gallery-card";
          card.innerHTML = `
            <div class="photo-placeholder">
              <span>394</span>
              <small>Photo placeholder</small>
            </div>
            <figcaption>
              <strong>${fallbackTitle}</strong>
              <span>Photo coming soon</span>
            </figcaption>
          `;
          galleryGrid.appendChild(card);
        }
      });
    })
    .catch(error => {
      console.error("Error drawing structured grid array layout elements:", error);
    });
});
