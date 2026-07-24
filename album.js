document.addEventListener("DOMContentLoaded", () => {
  const photosGrid = document.getElementById("album-photos-grid");
  if (!photosGrid) return;

  // 1. URL ROUTER MATH: Extract the dynamic "?slug=" variable from the browser location window
  const urlParams = new URLSearchParams(window.location.search);
  const albumSlug = urlParams.get('slug');

  if (!albumSlug) {
    window.location.href = 'gallery.html'; // Redirect safely back to safety if slug is missing
    return;
  }

  fetch("photos.json")
    .then(response => {
      if (!response.ok) throw new Error("Catalog payload dataset missing");
      return response.json();
    })
    .then(data => {
      const albums = data.albums || {};
      const photosArray = albums[albumSlug] || [];

      // Generate neat human readable headings out of our folder slug string
      const prettyTitle = albumSlug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());
      
      // Update our page heading fields inside our hero section on-the-fly
      document.title = `${prettyTitle} Album - American Legion Riders 394`;
      document.getElementById("album-title").textContent = prettyTitle;
      document.getElementById("album-description").textContent = `Viewing all individual photographs captured inside our ${prettyTitle} catalog collection log tracks.`;

      if (photosArray.length === 0) {
        photosGrid.innerHTML = `
          <div class="gallery-empty-note" style="grid-column: 1/-1;">
            <strong>Album Empty</strong>
            <p>There are currently no individual photographs uploaded to this directory branch loop. Check back soon for secretary updates.</p>
          </div>
        `;
        return;
      }

      photosGrid.innerHTML = ""; // Wipe loading text cleanly

      // 2. INNER POPULATOR LOOP: Build each individual asset image item box side-by-side
      photosArray.forEach(photo => {
        const photoFrame = document.createElement("figure");
        photoFrame.className = "gallery-photo";

        // Structured inside standard figure boxes matching your master styles rules parameters
        photoFrame.innerHTML = `
          <img src="${photo.path}" class="photo-thumbnail-trigger" data-full="${photo.path}" alt="${photo.caption || prettyTitle}" style="cursor: pointer;">
          <figcaption>${photo.caption || prettyTitle}</figcaption>
        `;

        photosGrid.appendChild(photoFrame);
      });

      // 3. THE LIGHTBOX OVERLAY POP-UP MODULE REGION
      const lightboxOverlay = document.getElementById("lightbox-overlay");
      const lightboxTargetImg = document.getElementById("lightbox-target-image");

      document.addEventListener("click", (e) => {
        if (e.target.classList.contains("photo-thumbnail-trigger")) {
          const fullPath = e.target.getAttribute("data-full");
          lightboxTargetImg.src = fullPath;
          lightboxOverlay.style.display = "flex";
          setTimeout(() => { lightboxOverlay.style.opacity = "1"; }, 10);
        } 
        else if (lightboxOverlay.style.opacity === "1") {
          lightboxOverlay.style.opacity = "0";
          setTimeout(() => {
            lightboxOverlay.style.display = "none";
            lightboxTargetImg.src = "";
          }, 200);
        }
      });

    })
    .catch(error => {
      console.error("Album view pipeline loader crash failure:", error);
      photosGrid.innerHTML = `<p style="color: red;">Error mounting photo stream grid layers collection.</p>`;
    });
});