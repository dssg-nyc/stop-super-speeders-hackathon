# Stop-Super-Speeders-Hackathon
building a public transportation alert and warning system for New York State and city DMVs to alert super speeders violations.



## Prerequisites: TODOs before the hackathon
- Complete volunteer [registration](http://www.nyc-dssg.org) on DSSG-NYC website
- Join DSSG-NYC [Slack Group](https://join.slack.com/t/nyc-dssg/shared_invite/zt-3fhzyi936-hDjiJn05j9EKY3BH9YjXgQ)
- Review DSSG [Anti-harassment Policy](https://github.com/dssg/hitchhikers-guide/blob/master/sources/dssg-manual/conduct-culture-and-communications/README.md), and [ethical standards](https://dssgfellowship.org/2015/09/18/an-ethical-checklist-for-data-science/)
- Review Family for Safe Streets Problem Statement: https://www.familiesforsafestreets.org/about

Extra dictionary for local, DMV would notify the owner of the driver, and notify the court
## Hacking Deliverables:
This hackathon can have several scoring categories:

### Part 1: Data Management
- Data mobilization of the sample data: taking the schemas and turn into the operational system 
- Data mapping: for county clerk to normalize into the operational schema (columns names mapping, and formating) 
- Privacy guardrails
- Data input system for stake-holders (e.g. courts, DMV, etc) (priority)

### Part 2: Super Speeder Monitori Dashboard - refreshes weekly and send out alerts

> Minimum requirements: Generate a list violators breached the criterias:
> - 16 driver’s license points
> - 11 times for speeding violations

#### Make Two Aggregated data sets that powers the dashboard with summary statistics: 
rolling period of 2 year static data - example data structure:
 
> 1) drivers’ table: 
> - primary key license
> - Type of violation
> - how many violations
> - Violation points
> - county registered
> 2) vehicle table: count
> - primary key
> - primary key license
> - number of violations
> - county where the vehicle is registered

*Alert system Output*:
- Create the email text to send the list of violators to stakeholders:
> 1. The violator
> 2. Vendor 
> 3. DMV


BONUS: 
- Create files for the offenders (bonus)
- Generate new insights for DMV officers
- Deploy as a web app

## On December 6th, 2025 the Day of Hackathon:

***

## Hackathon Day Schedule (10 AM – 6 PM)

### 10:00 – 10:30 AM  
- Registration & Check-In  
- Volunteers at desk
- Coffee & light snack

### 10:30 – 11:00 AM  
- Kickoff & Welcome  
- Intro to schedule, rules, deliverables  
- Quick orientation on data
- Introduce captains, volunteers, and judges  

### 11:00 – 1:00 PM  
- Hacking Session #1: If there is enough participants, Split two teams competing with each other
- Teams brainstorm, form groups (if not pre-formed)  
- Mentors circulate to assist  
- Pacers check on setup 

### 1:00 – 2:00 PM  
- Lunch & Networking  
- Relax and mingle with other participants and mentors  

### 2:00 – 4:30 PM  
- Hacking Session #2  
- Focused development sprint  
- Pacers check teams’ progress and encourage testing  
- Organizers keep reminding about deliverables submission process  

### 4:30 – 5:00 PM  
- Break

### 5:00 – 6:00 PM  
- Submission Deadline Reminder & Final Touches  
- Timekeeper announces countdown (15 min left, 5 min left, final submission call)  
- Collect all project links (Google Form/Devpost/etc.)  

### 6:00 – 6:30 PM  
- Project Demos & Judging  
- Each team presents demo (5 mins each, adjust if many teams)  
- Judges score based on criteria: Innovation, Impact, Functionality, Presentation    
- Winners Announced & Group Thank You  
- Prizes awarded, photos taken, closing remarks  

***

## Celebration

### 6:30 PM – onwards  
- **Happy Hour at local bar**  
- Casual networking, celebration of winners, and socializing after event  

***

***

## Pre-Hackathon Preparations Checklist

### Venue and Logistics
- Confirm venue booking (size large enough for teams, strong Wi-Fi, power supply, breakout areas).  
- Test **internet bandwidth** and ensure guest Wi-Fi credentials.  
- Arrange **tables, seating, and power strips** (at least 1 outlet per participant).  
- Order **A/V equipment**, microphones, projectors, and screens.  
- Prepare **check-in desk** setup: tables, lanyards/badges, pens, markers.  
- Print **signage** for directions (restrooms, food area, hackathon space).  

### Food & Beverages
- Order **meal catering** (breakfast, lunch, dinner if longer event, snacks).  
- Arrange **coffee/tea station** and water refill stations.  
- Consider **dietary needs** (vegetarian, vegan, gluten-free, halal/kosher options).  

### Sponsorship & Budget
- Finalize **sponsors** (API credits, prizes, food, venue).  
- Prepare **budget breakdown**: venue, food, swag, printing, prizes.  
- Order **prizes** (gift cards, tech gadgets, mentorship sessions).  

### Volunteers & Staff
- Recruit **volunteers** for registration, logistics, and team support.  
- Assign **mentors/tech helpers** 
- Designate **judges** (partners, sponsors, technical experts).  
- Train volunteers on **registration flow** and **timekeeping process**.  

### Marketing & Communication
- Launch **event website or registration portal**.  
- Confirm participant registrations and waitlist.  
- Send **pre-event email** with details: schedule, APIs, rules, starter kit links.  
- Create a **Slack server** for participant communication.  

### Judging & Deliverables
- Define **judging criteria** (e.g. Innovation, Functionality, Impact, Technical Implementation, Presentation).  
- Create a **submission form** (Devpost, Google Forms, or GitHub submission guidelines).  
- Prepare **presentation schedule** for final demos.  

***


