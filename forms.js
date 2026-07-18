document.addEventListener("DOMContentLoaded", () => {
  const formsListContainer = document.querySelector(".forms-list");
  if (!formsListContainer) return;

  // Clear out the manual static lines from your template
  formsListContainer.innerHTML = "";

  fetch("documents.json")
    .then(response => {
      if (!response.ok) throw new Error("Document catalog missing or unreadable");
      return response.json();
    })
    .then(data => {
      // Read the sorting path map directly from your master workflow structure
      const documentOrder = data.documentOrder || [];
      const archives = data.archives || {};

      documentOrder.forEach(slug => {
        // Access files nested inside the archives sub-object dictionary
        const docs = archives[slug] || [];

        if (docs.length > 0) {
          // If files exist in the folder, build out the download template rows
          docs.forEach(doc => {
            const row = document.createElement("article");
            row.className = "form-row";
            row.innerHTML = `
              <span class="file-icon">↓</span>
              <div>
                <h3>${doc.title}</h3>
                <p>Official Chapter 394 asset file resource availability.</p>
                <small>${doc.type} • ${doc.label}</small>
              </div>
              <a class="button button-dark" href="${doc.path}" download="${doc.title}.${doc.type.toLowerCase()}">Download</a>
            `;
            formsListContainer.appendChild(row);
          });
        } else {
          // Fallback Row: If a folder is empty, gracefully tell the user it's pending
          let prettyName = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());
          const fallbackRow = document.createElement("article");
          
          fallbackRow.className = "form-row fallback-disabled";
          fallbackRow.style.opacity = "0.6";
          fallbackRow.innerHTML = `
            <span class="file-icon" style="color: var(--muted);">⚠</span>
            <div>
              <h3>${prettyName}</h3>
              <p>This document category is currently being updated by the chapter secretary.</p>
              <small>PENDING • CHECK BACK SOON</small>
            </div>
            <button class="button button-dark" disabled style="cursor: not-allowed; background: #e0e0e0; color: #a0a0a0;">Unavailable</button>
          `;
          formsListContainer.appendChild(fallbackRow);
        }
      });
    })
    .catch(error => {
      console.error("Error generating local document index grid:", error);
    });
});
