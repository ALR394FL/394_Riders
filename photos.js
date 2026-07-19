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
      // TARGET ACCORDING TO YOUR NEW SCHEMATIC: Pull variables straight from the unified JSON structures

																							  
      const categoryOrder = data.categoryOrder || [];
																			   
      const albums = data.albums || {};
			  
																					
						   
	   

      let isFirstImage = true;

      // Loop through your categories in the exact order specified by your array list tracking keys
      categoryOrder.forEach(slug => {
        const photosArray = albums[slug] || [];
        
																																		 
																  
		
														
										   

        // Formats a clean human-readable title out of the folder slug name (e.g. "chapter-rides" -> "Chapter Rides")
        let fallbackTitle = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());

        if (photosArray.length > 0) {
          // 1. Build exactly ONE figure card frame per folder category collection block
          const groupCard = document.createElement("figure");
          
																	 
          if (isFirstImage) {
            groupCard.className = "gallery-card wide";
            isFirstImage = false;
          } else {
            groupCard.className = "gallery-card";
          }

          // FIXED: Use the first item's title property safely, or default cleanly to our formatted fallbackTitle string
          const humanTitle = photosArray[0].title || fallbackTitle;

          groupCard.innerHTML = `
            <figcaption>
              <strong>${humanTitle}</strong>
              <span>Collection contains ${photosArray.length} item(s)</span>
            </figcaption>
            <!-- 📦 Sub-grid placeholder frame to loop matching image blocks safely -->
            <div class="photo-stack"></div>
          `;

          galleryGrid.appendChild(groupCard);

          // Select the inner image frame wrapper we just created inside this specific block
          const photoStack = groupCard.querySelector(".photo-stack");

          // 2. INNER LOOP: Iterate over all photos inside this specific album array block
          photosArray.forEach(photo => {
            if (!photo.path) return;

            const imgElement = document.createElement("img");
            imgElement.src = photo.path;
            // Aligns layout descriptions cleanly to your custom schema keys
            imgElement.alt = photo.caption || humanTitle;
            imgElement.title = photo.caption || ""; // Displays caption text cleanly on browser hover tooltip
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
