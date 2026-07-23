// Centralized Chapter 394 Live Calendar Stream
const API_KEY = 'AIzaSyB9b9rC17BEVuS-YIYLxBn2aYrAnwaVHQc';
const CALENDAR_ID = 'alr394fl@gmail.com';

// Set up the live Google Calendar URL to fetch the next 3 upcoming events
const now = new Date().toISOString();
const url = `https://googleapis.com/${encodeURIComponent(CALENDAR_ID)}/events?key=${API_KEY}&timeMin=${now}&orderBy=startTime&singleEvents=true&maxResults=3`;

// Helper function to extract your specific tag classification rules from event text
function determineEventTag(titleText, detailsText) {
  const checkText = `${titleText} ${detailsText}`.toLowerCase();
  if (checkText.includes('meeting')) return 'MEETING';
  if (checkText.includes('ride') || checkText.includes('escort')) return 'RIDE';
  if (checkText.includes('service') || checkText.includes('volunteer') || checkText.includes('community')) return 'SERVICE';
  if (checkText.includes('fundraiser') || checkText.includes('event')) return 'EVENT';
  return 'EVENT'; // Safe default fallback tag
}

document.addEventListener("DOMContentLoaded", async () => {
  const container = document.querySelector(".event-list");
  if (!container) return;

  // Show a loading feedback block using your native design structure
  container.innerHTML = `
    <article class="event-row" style="opacity: 0.6;">
      <div class="event-info"><h3>🔄 Syncing with Google Calendar...</h3></div>
    </article>
  `;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    const data = await response.json();
    const events = data.items || [];
    
    // Clear out the loading notice
    container.innerHTML = "";

    if (events.length === 0) {
      container.innerHTML = `
        <article class="event-row">
          <div class="event-info"><h3>📅 No upcoming events scheduled at this time.</h3></div>
        </article>
      `;
      return;
    }

    // Map Google API fields directly into your existing card layout structures
    events.forEach(event => {
      const title = event.summary || "Untitled Chapter Event";
      const details = event.description || event.location || "No further details provided.";
      
      // Resolve start parameters cleanly
      const isAllDay = !event.start.dateTime;
      const rawDate = event.start.dateTime || event.start.date;
      const eventDate = new Date(rawDate);

      // 1. Calculate the 3-letter uppercase day shortcode (e.g., "TUE", "SAT")
      const day = eventDate.toLocaleDateString(undefined, { weekday: 'short' }).toUpperCase();

      // 2. Parse the time display string nicely
      let time = "TBA";
      if (isAllDay) {
        time = "All Day";
      } else {
        time = eventDate.toLocaleTimeString(undefined, {
          hour: 'numeric',
          minute: '2-digit',
          hour12: false // Switch to true if you prefer 12-hour AM/PM formats
        });
      }

      // 3. Process dynamic tags
      const tag = determineEventTag(title, details);

      // Create and inject the exact HTML components your CSS styles rely on
      const row = document.createElement("article");
      row.className = "event-row";
      row.innerHTML = `
        <div class="event-block">
          <span>${day}</span>
          <strong>${time}</strong>
        </div>
        <div class="event-info">
          <span class="tag">${tag}</span>
          <h3>${title}</h3>
          <p>${details}</p>
        </div>
        <span class="event-arrow">→</span>
      `;
      container.appendChild(row);
    });

  } catch (error) {
    console.error("Failed to stream live events:", error);
    container.innerHTML = `
      <article class="event-row" style="border-left-color: #ff3333;">
        <div class="event-info">
          <h3 style="color: #ff3333;">⚠️ Error Loading Calendar</h3>
          <p>We're having trouble reaching Google right now. Please try reloading the page.</p>
        </div>
      </article>
    `;
  }
});
