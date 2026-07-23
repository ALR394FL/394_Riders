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
      const documentOrder = data.documentOrder || [];
      const archives = data.archives || {};

      documentOrder.forEach(slug => {
        const docs = archives[slug] || [];
        const prettyName = slug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());
        const groupSection = document.createElement("section");

        if (docs.length > 0) {
          groupSection.className = "document-group";
          groupSection.innerHTML = `
            <h2 class="group-title">${prettyName}</h2>
            <div class="thumbnail-grid">
              <!-- Document items will be injected right here -->
            </div>
          `;

          const gridContainer = groupSection.querySelector(".thumbnail-grid");

          docs.forEach(doc => {
            const itemElement = document.createElement("div");
            itemElement.className = "document-item";
            itemElement.innerHTML = `
              <div class="document-preview-box">
                <embed src="${doc.path}#toolbar=0&navpanes=0&scrollbar=0&view=FitH" type="application/pdf">
                <a href="${doc.path}" target="_blank" class="document-click-overlay" title="Click to view ${doc.title}"></a>
              </div>
              <span class="doc-title">${doc.title}</span>
              <small class="doc-meta">${doc.type} • ${doc.label}</small>
            `;
            gridContainer.appendChild(itemElement);
          });

        } else {
          // Fallback Row Layout if category has no active documents
          groupSection.className = "document-group document-group-pending";
          groupSection.innerHTML = `
            <h2 class="group-title">${prettyName} (Pending)</h2>
            <div class="form-row fallback-disabled">
              <div>
                <h3>${prettyName}</h3>
                <p>This document category is currently being updated by the chapter secretary.</p>
                <small>PENDING • CHECK BACK SOON</small>
              </div>
              <button class="button-dark-disabled" disabled>Unavailable</button>
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
