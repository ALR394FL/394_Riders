document.addEventListener("DOMContentLoaded", () => {
  const galleryGrid = document.querySelector(".gallery-grid");
  if (!galleryGrid) return;

  galleryGrid.innerHTML = "";

  // Order categories are injected sequentially to match your original grid
  const categoryOrder = [
    "chapter-rides",
    "community-service",
    "the-open-road",
    "chapter-meetings",
    "veteran-escorts",
    "fundraisers"
  ];

  fetch("photos.json")
    .then(response => {
      if (!response.ok) throw new Error("Catalog index file corrupt or missing");
      return response.json();
    })
    .then(data => {
      let isFirstImage = true;

      categoryOrder.forEach(slug => {
        const photos = data[slug] || [];

        if (photos.length > 0) {
          // Loop over files found in active folder locations
          photos.forEach(photo => {
            const card = document.createElement("figure");
            
            // Your exact original design rule: force the absolute first image to layout wide
            if (isFirstImage) {
              card.className = "gallery-card wide";
              isFirstImage = false; 
            } else {
              card.className = "gallery-card";
            }

            card.innerHTML = `
              <img src="${photo.path}" alt="${photo.title}"/>
              <figcaption>
                <strong>${photo.title}</strong>
                <span>${photo.caption}</span>
              </figcaption>
            `;
            galleryGrid.appendChild(card);
          });
        } else {
          // Fallback Block: If folder is empty, inject the grey template layout placeholder
          let fallbackTitle = slug.replace("-", " ").replace(/\b\w/g, c => c.toUpperCase());
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
