document.addEventListener("DOMContentLoaded", () => {
  const foldersContainer = document.getElementById("album-folders-container");
  if (!foldersContainer) return;
  foldersContainer.innerHTML = "";

  fetch("photos.json")
    .then(response => {
      if (!response.ok) throw new Error("Catalog index file corrupt or missing");
      return response.json();
    })
    .then(data => {
      const categoryOrder = data.categoryOrder || [];
      const albums = data.albums || {};

      categoryOrder.forEach(slug => {
        const photosArray = albums[slug] || [];
        let fallbackTitle = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());

        // Create a stylized Folder Card component for every category directory
        const folderCard = document.createElement("a");
        folderCard.className = "folder-card";
        // 🌟 Passing the folder slug dynamically straight into the sub-page link parameters URL string
        folderCard.href = `album.html?slug=${slug}`;

        if (photosArray.length > 0) {
          const firstPhoto = photosArray[0];
          const humanTitle = firstPhoto.title || fallbackTitle;

          // Builds out the exact semantic structure required by your master stylesheet
          folderCard.innerHTML = `
            <div class="folder-cover">
              <!-- Folder Tab overlay label built from master file styles -->
              <div class="folder-tab">${photosArray.length} Photos</div>
              <img src="${firstPhoto.path}" alt="${humanTitle} Cover" onerror="this.style.display='none'; this.nextElementSibling.style.display='grid';">
              <div class="folder-placeholder" style="display: none;"><span>ALR</span></div>
            </div>
            <div class="folder-info">
              <h2>${humanTitle}</h2>
              <p>Click to open this collection album and browse all archived media assets captured on the road.</p>
              <strong>View Album<span>&rarr;</span></strong>
            </div>
          `;
        } else {
          // Empty album fallback card structure
          folderCard.innerHTML = `
            <div class="folder-cover">
              <div class="folder-placeholder"><span>394</span></div>
            </div>
            <div class="folder-info">
              <h2>${fallbackTitle}</h2>
              <p>Photos coming soon. This gallery directory is currently being updated by the chapter layout team.</p>
              <strong style="color: var(--muted);">Pending<span>&minus;</span></strong>
            </div>
          `;
        }

        foldersContainer.appendChild(folderCard);
      });
    })
    .catch(error => {
      console.error("Error drawing structured folder cards:", error);
      foldersContainer.innerHTML = `<p style="color: red; text-align: center;">Error loading dynamic galleries index.</p>`;
    });
});