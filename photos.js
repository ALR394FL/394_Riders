// ==========================================================================
// 📸 CATEGORIZED GALLERIES: Update text or image files in their specific section
// ==========================================================================

// 1. FEATURED PHOTOS (These cards load extra wide)
const FEATURED_PHOTOS = [
  {
    filename: "coastal-ride.png",
    title: "Chapter rides",
    caption: "Morning ride • Placeholder caption"
  }
];

// 2. STANDARD PHOTOS (Normal sized grids)
const STANDARD_PHOTOS = [
  {
    filename: "community-service.png",
    title: "Community service",
    caption: "Serving our neighbors • Placeholder caption"
  },
  {
    filename: "hero-road.png",
    title: "The open road",
    caption: "Riding with purpose • Placeholder caption"
  }
];

// 3. UPCOMING / EMPTY CATEGORIES (Shows the gray placeholder box with the chapter number)
const UPCOMING_CATEGORIES = [
  { title: "Chapter meetings", footnote: "Photo coming soon" },
  { title: "Veteran escorts", footnote: "Photo coming soon" },
  { title: "Fundraisers", footnote: "Photo coming soon" }
];


// ==========================================================================
// 🤖 THE RUNNER: This part loops through each group separately into the grid
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  const galleryGrid = document.querySelector(".gallery-grid");
  if (!galleryGrid) return;

  // Clear out old content
  galleryGrid.innerHTML = "";

  // Loop 1: Build the Wide Featured Images
  FEATURED_PHOTOS.forEach(photo => {
    const card = document.createElement("figure");
    card.className = "gallery-card wide"; // 'wide' class keeps the structural layout intact
    card.innerHTML = `
      <img src="images/${photo.filename}" alt="${photo.title}"/>
      <figcaption>
        <strong>${photo.title}</strong>
        <span>${photo.caption}</span>
      </figcaption>
    `;
    galleryGrid.appendChild(card);
  });

  // Loop 2: Build the Standard Images
  STANDARD_PHOTOS.forEach(photo => {
    const card = document.createElement("figure");
    card.className = "gallery-card";
    card.innerHTML = `
      <img src="images/${photo.filename}" alt="${photo.title}"/>
      <figcaption>
        <strong>${photo.title}</strong>
        <span>${photo.caption}</span>
      </figcaption>
    `;
    galleryGrid.appendChild(card);
  });

  // Loop 3: Build the Empty Placeholders with the chapter number mark
  UPCOMING_CATEGORIES.forEach(item => {
    const card = document.createElement("figure");
    card.className = "gallery-card";
    card.innerHTML = `
      <div class="photo-placeholder">
        <span>394</span>
        <small>Photo placeholder</small>
      </div>
      <figcaption>
        <strong>${item.title}</strong>
        <span>${item.footnote}</span>
      </figcaption>
    `;
    galleryGrid.appendChild(card);
  });
});
