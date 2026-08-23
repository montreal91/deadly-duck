# Plans

Plans for upcoming versions

## 0.2 (in progress)

* [x] Stable IDs for players and clubs
* [x] Persistence for players and clubs
* [x] Skill selection on level up
* [x] When selecting the club show their location and motto
* [x] Calendar
  * [x] Current date instead of abstract day (big ass competition refactoring)
  * [x] Season starts in February
  * [ ] Upcoming matches widget
  * [ ] Widget for the five last matches of the opponent
* [ ] Contract as first-class relationship
* [ ] Basic resolution sanity pass
  * [ ] Test 1280x720, 1366x768, 1920x1080
  * [ ] Fix only blocking overlap/cutoff issues

## 0.3 (In future)

* [ ] Negotiation MVP (Player evaluates offer using salary + club fame + loyalty + role)
* [ ] Transfers
* [ ] Farm clubs
* [ ] Persistence for matches and history
* [ ] Color codes for win/loss on the results screen
* [ ] Regular Championship → Playoffs transition system

## Later Versions

* [ ] Point-by-point match simulations with serve, receive, groundstrokes, footwork, strength, etc
* [ ] Biotech labs and implants development, neuroplasticity
* [ ] Trophy rooms, for clubs and the players
* [ ] UI that doesn't break under different resolutions
* [ ] Basic UI color palette
* [ ] Club Logos and colors
* [ ] Achievements
* [ ] Juice: the stat of player's inner resource. Very hard or impossible to recover. 
  Once player is not sure if she has enough juice for the next season, she decides to finish  her career.
  * Every player wants to have a farewell match in their home club.
* [ ] Player temperaments (Melancholic, Choleric, Phlegmatic, Sanguine)
  * They do nothing for now, but give a little bit of personality to the players.
* [ ] Bloggers (analytics, lovers, haters, players); expectations before matches and how did it play out.
* [ ] Psychological pressure of matches. Might be individual for the players.

### Achievements
* Leader Leads - Win Playoffs as a top seed
* The Triumph of the Underdog - Win Playoffs as 8th seed

## 0.1 (released)

* [x] Standalone Kivy desktop client
* [x] New story and continue story flows
* [x] Club selection
* [x] SQLite-backed save/load support
* [x] Main game screen
  * [x] Current season/stage/balance display
  * [x] Upcoming match display
  * [x] Championship standings
  * [x] Playoff bracket
* [x] Player selection for upcoming matches
  * [x] Opponent player details
  * [x] Home/away context
* [x] Day results screen
* [x] Practice screen
  * [x] Coach selection for player training
* [x] Roster management screen
  * [x] Hire new players
  * [x] Fire players
  * [x] Sign next-season contracts
  * [x] Retirement-aware contract availability
* [x] Championship and Katelyn Cup Playoffs season loop
* [x] About screen
* [x] Basic PyInstaller release packaging
