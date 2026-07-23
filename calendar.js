// Centralized Chapter 394 Local Cache Calendar Stream
// Note: No API Keys or tokens are required here since we load a local tracking file!
const CALENDAR_DATA_URL = './calendar.json';

/**
 * Evaluates the title and details text to assign an operational tag.
 * Automatically aligns with your existing stylesheet layout targets.
 */
function determineEventTag(titleText, detailsText) {
  const checkText = `${titleText} ${detailsText}`.toLowerCase();
  if (checkText.includes('meeting')) return 'MEETING';
  if (checkText.includes('ride') || checkText.includes('escort')) return 'RIDE';
  if (checkText.includes('service') || checkText.includes('volunteer') || checkText.includes('community')) return 'SERVICE';
  if (checkText.includes('fundraiser') || checkText.includes('event')) return 'EVENT';
  return 'EVENT'; // Fallback default
}

document.addEventListener("DOMContentLoaded", async () => {
  const container = document.querySelector(".event-list");
  if (!container) return;

  // Render a clean placeholder matching your structural spacing rules while loading files
  container.innerHTML = `
    <article class="event-row" style="opacity: 0.65;">
      <div class="event-info"><h3>🔄 Fetching upcoming scheduled activities...</h3></div>
    </article>
  `;

  try {
    const response = await fetch(CALENDAR_DATA_URL);
    if (!response.ok) throw new Error(`HTTP data error! status: ${response.status}`);
    
    const data = await response.json();
    const events = data.items || [];
    
    // Clear out the loading notice
    container.innerHTML = "";

    // Fallback if your calendar timeline is currently completely empty
    if (events.length === 0) {
      container.innerHTML = `
        <article class="event-row">
          <div class="event-info"><h3>📅 No upcoming events scheduled at this time.</h3></div>
        </article>
      `;
      return;
    }

    // Process and inject the next 3 events dynamically
    events.forEach(event => {
      const title = event.summary || "Untitled Chapter Event";
      const details = event.description || event.location || "No further details provided.";
      
      // Resolve multi-day vs exact timezone hour fields
      const isAllDay = !event.start.dateTime;
      const rawDate = event.start.dateTime || event.start.date;
      const eventDate = new Date(rawDate);

      // 1. Generate the 3-letter capital shortcode (e.g., "TUE", "SAT")
      const day = eventDate.toLocaleDateString(undefined, { weekday: 'short' }).toUpperCase();

      // 2. Format hours into a clear, unified 24h or 12h display string
      let time = "TBA";
      if (isAllDay) {
        time = "All Day";
      } else {
        time = eventDate.toLocaleTimeString(undefined, {
          hour: 'numeric',
          minute: '2-digit',
          hour12: false // Toggle to true if you want 'PM/AM' syntax flags
        });
      }

      // 3. Process keyword tracking tag markers
      const tag = determineEventTag(title, details);

      // Create the article row matching your exact existing frontend design block
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
    console.error("CORS Bypass local execution block broken:", error);
    container.innerHTML = `
      <article class="event-row" style="border-left-color: #ff3333;">
        <div class="event-info">
          <h3 style="color: #ff3333;">⚠️ Schedule Sync Initializing</h3>
          <p>The events catalog is being prepared by our automated runner. Please refresh the page in a few minutes.</p>
        </div>
      </article>
    `;
  }
});
