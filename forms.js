document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("documents-container");
  if (!container) return;

  container.innerHTML = ""; // Clear loader placeholder text

  fetch("documents.json")
    .then(response => {
      if (!response.ok) throw new Error("Document catalog missing or unreadable");
      return response.json();
    })
    .then(data => {
      // ✅ Properly access the object dictionary from your json file structure
      const documentOrder = data.documentOrder || [];
      const archives = data.archives || {};

      documentOrder.forEach(slug => {
        const docs = archives[slug] || [];
        
        // Format folder names neatly for your section headings (e.g., "ride-waivers" -> "Ride Waivers")
        const prettyName = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());

        // Create the primary grouping section element
        const groupSection = document.createElement("section");
        groupSection.className = "document-group";
        groupSection.style.marginBottom = "40px";

        if (docs.length > 0) {
          // Build the section layout with an active grid layout container
          groupSection.innerHTML = `
            <h2 class="group-title" style="font-size: 1.5rem; border-bottom: 2px solid #eaeaea; padding-bottom: 8px; margin: 24px 0 16px 0; color: #333;">
              ${prettyName}
            </h2>
            <div class="thumbnail-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 20px;">
              <!-- Document items will be injected right here -->
            </div>
          `;

          const gridContainer = groupSection.querySelector(".thumbnail-grid");

          // Build thumbnail grids side-by-side
docs.forEach(doc => {
  const itemElement = document.createElement("div");
  itemElement.className = "document-item";
  
  // Clean structural layouts for item cards
  itemElement.style.cssText = "display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 10px;";

           itemElement.innerHTML = `
             <!-- Bounding visual card frame with strict width & aspect ratios -->
             <div style="display: block; width: 130px; height: 170px; border: 1px solid #dcdcdc; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); position: relative; background: #ffffff;">
               
               <!-- 🌟 The Live Inline Document Viewer Engine Embed with strict dimensions -->
               <embed src="${doc.path}#toolbar=0&navpanes=0&scrollbar=0&view=FitH" 
                      type="application/pdf" 
                      width="130" 
                      height="170" 
                      style="width: 100%; height: 100%; border: none; pointer-events: none; display: block;">
               
               <!-- 🔒 Transparent absolute click-catcher layer over the top of the embed box -->
               <a href="${doc.path}" 
                  target="_blank" 
                  download="${doc.title}.${doc.type.toLowerCase()}" 
                  style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 10; display: block; cursor: pointer;"
                  title="Click to view or download ${doc.title}">
               </a>
             </div>
             
             <!-- Document Text Labels underneath the thumbnail box frame -->
             <span style="margin-top: 10px; font-size: 0.85rem; color: #333; word-break: break-word; font-family: sans-serif; font-weight: bold; max-width: 140px;">
               ${doc.title}
             </span>
             <small style="font-size: 0.75rem; color: #888; margin-top: 2px;">
               ${doc.type} • ${doc.label}
             </small>
           `;
         
           gridContainer.appendChild(itemElement);
         });
         
        } else {
          // 🔄 Exact Fallback Row Layout: Keeps your secretarial warning message if folder is empty
          groupSection.innerHTML = `
            <h2 class="group-title" style="font-size: 1.5rem; border-bottom: 2px solid #eaeaea; padding-bottom: 8px; margin: 24px 0 16px 0; color: #aaa;">
              ${prettyName} (Pending)
            </h2>
            <div class="form-row fallback-disabled" style="opacity: 0.6; display: flex; align-items: center; justify-content: space-between; background: #f9f9f9; padding: 15px; border-radius: 6px; border: 1px dashed #ccc;">
              <div>
                <h3 style="margin: 0 0 5px 0; font-size: 1.1rem; color: #666;">${prettyName}</h3>
                <p style="margin: 0 0 5px 0; font-size: 0.9rem; color: #888;">This document category is currently being updated by the chapter secretary.</p>
                <small style="font-size: 0.75rem; color: #999; font-weight: bold;">PENDING • CHECK BACK SOON</small>
              </div>
              <button class="button button-dark" disabled style="cursor: not-allowed; background: #e0e0e0; color: #a0a0a0; border: none; padding: 10px 15px; border-radius: 4px;">Unavailable</button>
            </div>
          `;
        }

        container.appendChild(groupSection);
      });
    })
    .catch(error => {
      console.error("Error generating local document index grid:", error);
      container.innerHTML = `<p style="color: red; text-align: center; font-weight: bold; margin-top: 20px;">Error loading document gallery.</p>`;
    });
});
