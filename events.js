// Centralized Chapter 394 Local Cache Calendar Stream
const CALENDAR_DATA_URL = './events.json';

function determineEventTag(titleText, detailsText) {
  const checkText = `${titleText} ${detailsText}`.toLowerCase();
  if (checkText.includes('meeting')) return 'MEETING';
  if (checkText.includes('ride') || checkText.includes('escort')) return 'RIDE';
  if (checkText.includes('service') || checkText.includes('volunteer') || checkText.includes('community')) return 'SERVICE';
  if (checkText.includes('fundraiser') || checkText.includes('event')) return 'EVENT';
  return 'EVENT';
}

document.addEventListener("DOMContentLoaded", async () => {
  const container = document.querySelector(".event-grid") || document.querySelector(".event-list");
  const modal = document.getElementById("event-modal");
  const modalContent = document.getElementById("modal-content");
  const modalClose = document.getElementById("modal-close");

  if (!container) return;
  container.className = "event-grid";

  container.innerHTML = `
    <article class="event-card" style="opacity: 0.65; grid-column: 1 / -1; text-align: center;">
      <div class="event-info"><h3>🔄 Fetching upcoming scheduled activities...</h3></div>
    </article>
  `;

  try {
    const response = await fetch(CALENDAR_DATA_URL);
    if (!response.ok) throw new Error(`HTTP data error! status: ${response.status}`);
    const data = await response.json();
    const events = data.items || [];

    container.innerHTML = "";

    if (events.length === 0) {
      container.innerHTML = `
        <article class="event-card" style="grid-column: 1 / -1; text-align: center;">
          <div class="event-info"><h3>📅 No upcoming events scheduled at this time.</h3></div>
        </article>
      `;
      return;
    }

    events.forEach((event, index) => {
      const title = event.summary || "Untitled Chapter Event";
      const details = event.description || "No further details provided.";
      const location = event.location || "Location shared via organizer update.";
      const isAllDay = !event.start.dateTime;
      const rawDate = event.start.dateTime || event.start.date;
      const eventDate = new Date(rawDate);

      const day = eventDate.toLocaleDateString(undefined, { weekday: 'short' }).toUpperCase();
      const dateNum = eventDate.getDate();
      const monthShort = eventDate.toLocaleDateString(undefined, { month: 'short' }).toUpperCase();

      let time = "TBA";
      if (isAllDay) {
        time = "All Day";
      } else {
        time = eventDate.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit', hour12: false });
      }

      const tag = determineEventTag(title, details);

      // Create card element
      const card = document.createElement("article");
      card.className = "event-card";
      card.setAttribute("role", "button");
      card.setAttribute("tabindex", "0");
      
      card.innerHTML = `
        <div class="event-card-header">
          <div class="event-badge">
            <span class="day-text">${day}</span>
            <span class="date-num">${dateNum} ${monthShort}</span>
          </div>
          <span class="tag ${tag.toLowerCase()}">${tag}</span>
        </div>
        <div class="event-info">
          <strong class="time-stamp">⏰ ${time}</strong>
          <h3>${title}</h3>
          <p class="truncate-text">${details}</p>
        </div>
        <div class="card-footer-action">View Full Details →</div>
      `;

      // 💥 THE POP OUT CLICK EVENT
      card.addEventListener("click", () => {
        modalContent.innerHTML = `
          <span class="modal-tag ${tag.toLowerCase()}">${tag}</span>
          <h2 class="modal-title">${title}</h2>
          <div class="modal-meta-grid">
            <div><strong>📅 Date:</strong> ${eventDate.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</div>
            <div><strong>⏰ Time:</strong> ${time}</div>
            <div><strong>📍 Location:</strong> ${location}</div>
          </div>
          <hr class="modal-divider" />
          <div class="modal-description">
            <strong>📋 Description & Details:</strong>
            <p>${details.replace(/\n/g, '<br>')}</p>
          </div>
          ${event.htmlLink ? `<a href="${event.htmlLink}" target="_blank" class="gcal-link-btn">🗓️ Open in Google Calendar</a>` : ''}
        `;
        
        modal.classList.add("modal-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden"; // Lock page background scroll
      });

      container.appendChild(card);
    });

    // Close Modal Functions
    const closeModal = () => {
      modal.classList.remove("modal-open");
      modal.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "auto"; // Restore background scrolling
    };

    modalClose.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && modal.classList.contains("modal-open")) closeModal(); });

  } catch (error) {
    console.error("Calendar operational stream processing failure:", error);
  }
});
