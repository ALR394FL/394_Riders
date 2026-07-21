document.addEventListener("DOMContentLoaded", () => {
  // Fetch your dynamic documents payload file
  fetch("documents.json")
    .then(response => {
      if (!response.ok) throw new Error("Failed to load documents dataset");
      return response.json();
    })
    .then(data => {
      renderGroupedDocuments(data);
    })
    .catch(error => {
      console.error("Error building document groups:", error);
      document.getElementById("documents-container").innerHTML = 
        `<p style="color: red; text-align: center;">Error loading document gallery.</p>`;
    });
});

function renderGroupedDocuments(filesArray) {
  const container = document.getElementById("documents-container");
  if (!container) return;
  container.innerHTML = ""; // Clear loader placeholder text

  // 1. Group the files array by their parent subfolder categories
  const groupedData = {};

  filesArray.forEach(file => {
    // Splits "documents/ride-waivers/file.pdf" to isolate "ride-waivers"
    const pathParts = file.path.split('/');
    let category = "uncategorized";
    
    if (pathParts.length > 2) {
      category = pathParts[1]; // Grabs the middle folder name
    }

    if (!groupedData[category]) {
      groupedData[category] = [];
    }
    groupedData[category].push(file);
  });

  // 2. Loop through each folder group and generate structured HTML components
  for (const [categoryName, files] of Object.entries(groupedData)) {
    
    // Format folder names neatly for your display titles (e.g., "ride-waivers" -> "Ride Waivers")
    const displayTitle = categoryName
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');

    // Create the primary grouping section element
    const groupSection = document.createElement("section");
    groupSection.className = "document-group";

    // Build the dynamic grouping elements inner template
    groupSection.innerHTML = `
      <h2 class="group-title" style="font-size: 1.5rem; border-bottom: 2px solid #eaeaea; padding-bottom: 8px; margin: 24px 0 16px 0; color: #333;">
        ${displayTitle}
      </h2>
      <div class="thumbnail-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 20px;">
        <!-- Files will be injected right here -->
      </div>
    `;

    const gridContainer = groupSection.querySelector(".thumbnail-grid");

    // 3. Inject individual card buttons side-by-side into this group's grid container
    files.forEach(file => {
      const itemElement = document.createElement("div");
      itemElement.className = "document-item";
      itemElement.style.cssText = "display: flex; flex-direction: column; align-items: center; text-align: center;";

      // Point thumbnail to your images directory cache matching the base file name
      const fileNameWithoutExt = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
      const thumbnailPath = `images/thumbnails/${fileNameWithoutExt}.jpg`;

      itemElement.innerHTML = `
        <a href="${file.path}" target="_blank" style="display: block; width: 100%; max-width: 130px; aspect-ratio: 3 / 4; border: 1px solid #dcdcdc; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s;">
          <img src="${thumbnailPath}" alt="${file.name} Preview" onerror="this.src='images/thumbnails/default-doc-icon.png';" style="width: 100%; height: 100%; object-fit: cover;">
        </a>
        <span style="margin-top: 8px; font-size: 0.85rem; color: #555; word-break: break-word; font-family: sans-serif;">
          ${fileNameWithoutExt.replace(/[-_]/g, ' ')}
        </span>
      `;

      gridContainer.appendChild(itemElement);
    });

    // Append the completely organized category container group directly onto your target page layout
    container.appendChild(groupSection);
  }
}
