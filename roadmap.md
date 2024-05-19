# Teh Roadmap

## Console App Publication (The First Prototype)
What I already did is quite a good start.

I want to write a post(s) to introduce new players to my game and ask them to share their emotions.

### Must-haves
1. **Separation of the client and the core *(in process)***
2. Adequate dates;
3. Game Actions API; *(this will induce a lot of refactoring)*;
4. Game AI API and rudimental implementation; *(this too)*;
5. Remove surfaces and specializations;
6. Write a compelling blog post;

### Good Ideas
1. Improve the game balance; *(but it's hard to understand what is a good balance, maybe it's already good enough)*
2. Better name generation;
   
## Kivy App Publication (MVP)
### Must-Haves
1. Graphical User Interface of minimum viable quality;
2. Save full match history;
3. Ports and Adapters architecture;
4. New players' skillset (serve, receive, racquet work, footwork, strength, dexterity, endurance) and point-by-point match emulation;
5. Match intensity, training session intensity;
6. Salary Cap, Limited Budgets, Contracts, RFAs and UFAs negotiation process;
7. Trainers' contracts;
8. Trade rules;
9. Farm clubs;
10. Manager contracts;
11. Trophies (Regular season, playoffs, regular season MVP, playoffs MVP, best server, best serve breaker, etc) with full history lookup;
12. "Quests engine";

### Good Ideas
1. Utilise SQLite to save data;
2. Multiple leagues (France/Britain/USA);
12. Backpack-problem-based cyber-augmentations; (if set in Cyberpunk 2077 universe, cyber-psychosis);

## Steam Release
### Must-Haves
1. Functional UI;
2. Beautiful UI;
3. Soundtrack (and/or integration with Spotify);
4. Strong story-telling;
5. Modding and functional in-game tools mod management;

## Gaps
* _What is the timeline for completing the must-have features for both the console and Kivy app publications?_
  * Who knows? Step by step I'll make my game somewhat interesting.
* _What specific improvements are planned for the game balance and name generation?_
  * Speaking of name generation, I'll split names and surnames into groups based on ethnicity.
    The generator will pick ethnicity first and then pick random names and surnames.
  * Speaking of game balance, I don't know. Maybe, it's a good idea to freeze the feature set first and do balancing later. 
* _How will the utilization of SQLite for data storage be implemented in the Kivy app?_
  * This doesn't matter because the Kivy app will be just a client, the same as the console application.
