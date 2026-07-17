// Centralized Chapter 394 Calendar Stream
const CHAPTER_EVENTS = [
  {
    day: "THU",
    time: "Monthly",
    tag: "MEETING",
    title: "Chapter 394 Riders Meeting",
    details: "Meeting date and time to be confirmed • American Legion Post 394 • Palm Bay"
  },
  {
    day: "SAT",
    time: "TBA",
    tag: "RIDE",
    title: "Chapter Breakfast Ride",
    details: "Meet time and KSU to be announced • Starting point: Post 394"
  },
  {
    day: "SUN",
    time: "TBA",
    tag: "SERVICE",
    title: "Veterans Community Service Day",
    details: "Volunteer schedule coming soon • Location to be announced"
  }
];

// Dynamically generate the layout cards instantly upon text processing
document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".event-list");
  if (!container) return;

  // Clear existing static placeholder markers
  container.innerHTML = "";

  // Loop through metrics and insert semantic layout rows safely
  CHAPTER_EVENTS.forEach(item => {
    const row = document.createElement("article");
    row.className = "event-row";
    row.innerHTML = `
      <div class="event-block">
        <span>${item.day}</span>
        <strong>${item.time}</strong>
      </div>
      <div class="event-info">
        <span class="tag">${item.tag}</span>
        <h3>${item.title}</h3>
        <p>${item.details}</p>
      </div>
      <span class="event-arrow">→</span>
    `;
    container.appendChild(row);
  });
});
