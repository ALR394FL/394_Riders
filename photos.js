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
      const categoryOrder = data.categoryOrder || [];
      const albums = data.albums || {};
      let isFirstImage = true;

      // Loop through categories in order
      categoryOrder.forEach(slug => {
        const photosArray = albums[slug] || [];
        let fallbackTitle = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());

        const groupCard = document.createElement("figure");
        
        if (photosArray.length > 0) {
          // Check for prominent formatting layout features on item zero
          if (isFirstImage) {
            groupCard.className = "gallery-card wide";
            isFirstImage = false;
          } else {
            groupCard.className = "gallery-card";
          }

          const humanTitle = photosArray[0].title || fallbackTitle;
          groupCard.innerHTML = `
            <figcaption>
              <strong>${humanTitle}</strong>
              <span>Collection contains ${photosArray.length} item(s)</span>
            </figcaption>
            <div class="photo-stack"></div>
          `;
          galleryGrid.appendChild(groupCard);

          const photoStack = groupCard.querySelector(".photo-stack");

          // INNER LOOP: Append individual thumbnail items safely
          photosArray.forEach(photo => {
            if (!photo.path) return;
            const imgElement = document.createElement("img");
            imgElement.src = photo.path;
            imgElement.className = "photo-thumbnail";
            imgElement.setAttribute("data-full", photo.path);
            imgElement.alt = photo.caption || humanTitle;
            imgElement.title = photo.caption || "";
            imgElement.loading = "lazy";
            
            photoStack.appendChild(imgElement);
          });

        } else {
          // Fallback Empty Placeholder Card
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

      // 🌟 CREATE THE SYSTEM LIGHTBOX NODES
      const lightboxModal = document.createElement('div');
      lightboxModal.id = 'lightbox-overlay';
      lightboxModal.innerHTML = `
        <span class="close-btn">&times;</span>
        <img id="lightbox-target-image" src="" alt="Full view preview">
      `;
      document.body.appendChild(lightboxModal);

      // Event delegation handles opening and closing interactions smoothly
      document.addEventListener('click', (event) => {
        const clickedElement = event.target;
        
        if (clickedElement.classList.contains('photo-thumbnail')) {
          const fullResolutionPath = clickedElement.getAttribute('data-full');
          const modalImage = document.getElementById('lightbox-target-image');
          modalImage.src = fullResolutionPath;
          lightboxModal.style.display = 'flex';
          setTimeout(() => { lightboxModal.style.opacity = '1'; }, 10);
          
        } else if (lightboxModal.style.opacity === '1') {
          lightboxModal.style.opacity = '0';
          setTimeout(() => {
            lightboxModal.style.display = 'none';
            document.getElementById('lightbox-target-image').src = '';
          }, 200);
        }
      });
    })
    .catch(error => {
      console.error("Error drawing structured grid array layout elements:", error);
    });
});
