// 📸 THE PHOTO PLAYLIST: Add your new photos right here!
const CHAPTER_PHOTOS = [
  {
    filename: "coastal-ride.png",
    title: "Chapter Rides",
    caption: "Morning ride down the coast"
  },
  {
    filename: "community-service.png",
    title: "Community Service",
    caption: "Serving our neighbors in Palm Bay"
  },
  {
    filename: "hero-road.png",
    title: "The Open Road",
    caption: "Riding with purpose"
  }
];

// 🤖 THE PLAYER: This loop automatically builds your webpage gallery
document.addEventListener("DOMContentLoaded", () => {
  const galleryGrid = document.querySelector(".gallery-grid");
  if (!galleryGrid) return;

  // Clear out any old photos sitting on the page
  galleryGrid.innerHTML = "";

  // The Loop: Go through the playlist item by item
  CHAPTER_PHOTOS.forEach(photo => {
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
});
