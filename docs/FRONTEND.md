# Frontend Architecture Documentation

## Overview

The frontend folder (`frontend/`) contains all user-facing HTML templates, CSS styling, and client-side JavaScript for the SAFENY web interface.

---

## File Structure

```
frontend/
└── templates/
    ├── index.html              # Upload page
    ├── results.html            # Results dashboard (3 tabs)
    ├── resources.html          # Program information
    ├── driver_details.html     # Individual driver view
    └── error.html              # Error handling page
```

---

## Templates Overview

### `index.html` - Upload Interface

**Purpose:** Main entry point where users upload CSV files

**Key Features:**

1. **File Upload Section**
   - Drag-and-drop file input
   - Click-to-browse fallback
   - File type validation (CSV only)

2. **Data Type Selector**
   ```html
   <select name="file_type">
     <option value="speed_camera">Speed Camera Tickets</option>
     <option value="traffic_violations">Traffic Violations (Officer-Issued)</option>
   </select>
   ```

3. **Animated Loading State**
   - Hourglass emoji: ⏳ (smooth 360° rotation)
   - Blinking dots: `. . .` (sequential fade animation)
   - Disabled submit button during processing

4. **Styling**
   - Stevens Institute branding:
     - Primary red: `#A6192E`
     - Secondary gray: `#54585A`
   - Responsive design (mobile-friendly)
   - Gradient background

5. **Program Information**
   - Super speeder thresholds displayed
   - Link to resources page

**CSS Animations:**
```css
@keyframes flip {
  0% { transform: rotate(0deg); }
  25% { transform: rotate(90deg); }
  50% { transform: rotate(180deg); }
  75% { transform: rotate(270deg); }
  100% { transform: rotate(360deg); }
}

@keyframes blink {
  0%, 20%, 100% { opacity: 0; }
  50% { opacity: 1; }
}
```

**JavaScript:**
- File input change listener
- Drag-and-drop handlers
- Form submission with loading state
- File size display

---

### `results.html` - Results Dashboard

**Purpose:** Display detection results in interactive 3-tab interface

**Architecture: Tabbed Interface**

#### Tab 1: Super Speeders (1,332+ drivers)

**Content:**
- Sortable data table with columns:
  - Driver ID (License Plate)
  - Violation Count (past 12 months)
  - Speed-Related Points
  - Recent Violations
  - Most Recent Date

**Features:**
- Click column headers to sort (ascending/descending indicators ↑↓)
- Color coding: Red (#A6192E) for high-risk drivers
- Badge counter showing total count
- Individual links to driver details

**SQL Query:**
```sql
SELECT driver_id, COUNT(*) as violation_count, ...
FROM fct_violations
WHERE (speed_camera_violations >= 16) OR (points >= 11)
ORDER BY violation_count DESC
```

#### Tab 2: Warning Drivers (227+ drivers)

**Content:**
- Similar table structure, drivers approaching thresholds
- Color coding: Yellow (#F0AD4E) for warning level
- Shows how close to super speeder threshold

**Query Logic:**
```sql
WHERE (12 <= speed_camera_violations < 16)
   OR (8 <= points < 11)
```

#### Tab 3: Analytics & Summary

**Content:**

1. **Summary Cards**
   - Total violations: 145,000+
   - Unique drivers: 77,475
   - Unique license plates: 55,506
   - Date range: Oct 1 - Nov 24, 2025

2. **Charts**
   - Violation distribution by type (bar chart)
   - Violations by source (speed camera vs. officer-issued)
   - Risk score distribution
   - Geographic hotspots (if data available)

3. **Thresholds Visualization**
   - Interactive display of detection criteria
   - Visual representation of 16-ticket and 11-point thresholds

**JavaScript Charting:** Native bars with gradients (no external library)

---

### `resources.html` - Program Information

**Purpose:** Educate visitors about SAFENY and partner organizations

**Sections:**

1. **Header**
   - Program title and description
   - Mission statement

2. **The Problem**
   ```
   Traffic deaths in NYC: 250+/year
   Speeding-involved crashes: 30%
   ```

3. **The Solution**
   - Explanation of super speeder detection
   - Thresholds and ISA device mandate

4. **Community Partners**

   **a) Streets Are For Everyone (S.A.F.E.)**
   - Grassroots organization
   - Vision Zero advocacy
   - Link: https://www.streetsareforeveryone.org/

   **b) Beta NYC**
   - Data-driven public solutions
   - Partners with NYC on initiatives
   - Link: https://www.beta.nyc/

   **c) NYC Data Science for Social Good**
   - Data scientists + nonprofits
   - Traffic safety + criminal justice
   - Link: https://www.nyc-dssg.org/

5. **Call to Action**
   - How to support traffic safety
   - Navigation back to portal

**Styling:**
- Resource cards with hover effects
- Partner logos (where available)
- Consistent Stevens branding
- Responsive card grid

---

### `driver_details.html` - Individual Driver Profile

**Purpose:** Show detailed violation history for a specific driver

**Content:**

1. **Driver Header**
   - Driver ID / License Plate
   - Status badge (Super Speeder / Warning)
   - Violation count summary

2. **Violation Timeline**
   - Chronological list of all violations
   - For each violation:
     - Date, type, violation code
     - Speed (for speed cameras)
     - Points (for traffic violations)
     - Location/precinct

3. **Statistics Panel**
   - Total violations in past 12 months
   - Total points in past 18 months
   - Most recent violation date
   - Data source breakdown (cameras vs. officer)

4. **Risk Assessment**
   - Visual indicator (red/yellow/green)
   - Distance to threshold
   - Recommendation (ISA device yes/no)

**Template Variables (from Flask):**
```python
{
  "driver_id": "ABC1234",
  "violations": [...],
  "status": "SUPER_SPEEDER",
  "violation_count": 18,
  "total_points": 15,
  ...
}
```

---

### `error.html` - Error Handling

**Purpose:** Display user-friendly error messages

**Common Error Scenarios:**

1. **Invalid File Type**
   ```
   Error: Please upload a CSV file
   ```

2. **No File Selected**
   ```
   Error: Please select a file before uploading
   ```

3. **Database Connection Error**
   ```
   Error: Unable to process data at this time
   ```

4. **Empty Dataset**
   ```
   Warning: No violations found in uploaded data
   ```

**Features:**
- Back button to upload page
- Error code and description
- Actionable remediation steps
- Stevens branding consistency

---

## Styling Architecture

### Color Palette

```css
/* Stevens Institute of Technology */
--primary-red: #A6192E;
--secondary-gray: #54585A;

/* Semantic Colors */
--success-green: #22C55E;
--warning-yellow: #F0AD4E;
--danger-red: #A6192E;
--light-bg: #f7fafc;
--text-dark: #2d3748;
--text-light: #718096;
```

### Component Styles

1. **Buttons**
   - Gradient fill (red → gray)
   - Hover: translate up + shadow increase
   - Disabled: gray + no hover

2. **Tables**
   - Header row: dark gray background
   - Rows: alternating white/light gray
   - Sortable headers: pointer cursor + indicator (↑↓)
   - Hover: highlight row

3. **Cards**
   - White background
   - Subtle border (#e2e8f0)
   - Box shadow on hover
   - Border-radius: 10-15px

4. **Tabs**
   - Underline indicator on active tab
   - Badge counter (red background)
   - Smooth transition between tabs

---

## JavaScript Functionality

### Table Sorting

```javascript
function sortTable(columnIndex, isNumeric) {
  // 1. Extract column data
  // 2. Parse as numeric or string
  // 3. Toggle ascending/descending
  // 4. Update visual indicator (↑ ↓)
  // 5. Re-render table rows
}
```

**Behavior:**
- Click column header to sort
- Click again to reverse order
- Only one column sorted at a time

### Tab Switching

```javascript
function switchTab(tabName) {
  // 1. Hide all tab contents
  // 2. Show selected tab
  // 3. Update active tab indicator
  // 4. Highlight active badge
}
```

**Tabs:** Super Speeders | Warning Drivers | Analytics

### Form Handling

```javascript
document.getElementById('uploadForm').addEventListener('submit', function(e) {
  // Update button text with animation
  submitBtn.innerHTML = '<span class="hourglass">⏳</span>Processing<span class="loading-dots">...'
  // Disable further submissions
  submitBtn.disabled = true;
});
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile: < 768px */
.container { width: 90%; }
.table { font-size: 12px; }

/* Tablet: 768px - 1024px */
.container { width: 85%; }

/* Desktop: > 1024px */
.container { max-width: 1200px; }
```

### Mobile Optimizations

1. **Stacked layout** for tabs on small screens
2. **Horizontal scroll** for wide tables
3. **Touch-friendly** button sizes (44px min-height)
4. **Simplified charts** (single metric per card)

---

## Browser Compatibility

- **Modern browsers:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **CSS support:** Flexbox, Grid, CSS Variables
- **JavaScript:** ES6+
- **No external dependencies** for rendering

---

## Future Enhancements

1. **Dark Mode Toggle:** Theme switcher in header
2. **Export Features:** CSV, PDF download of tables
3. **Advanced Filtering:** Date range, violation type filters
4. **Map Visualization:** Geographic distribution of violations
5. **Real-time Updates:** WebSocket for live data feeds
6. **Mobile App:** React Native adaptation
7. **Accessibility:** WCAG 2.1 AA compliance improvements

