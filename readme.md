## Australian Tennis League

*It is temporary location. Soon I'll move this code to the separate repository*

This game will let you manage your own semipro tennis club in a highly configurable tennis league.

Now game allows you to play with 10 fictional clubs (all of them are playable), in one or two divisions and select number of matches between clubs in same division and different.

For now there is no gameplay, just pushing same commands again and again till the end of the regular tournament. Still there is no playoffs at the end of season, but this feature is for another day.

**game.py** runs game in text mode.
Commands:
+ *show* prints a list of today's matches if any;
+ *m* prints a match for managed club if any;
+ *s* selects random player from managed club;
+ *s [player_id]* selects a certain player from managed club if possible;
+ *mp* prints list of players;
+ *n* proceed to the next day (to proceed some player have to be selected)
+ *cs* print current league standings;
+ *cs div* print current division standings;
+ *cs div all* print standings in all divisions;

**main.py** runs the game in graphic mode. Under heavy construction.