## Deadly Duck Tennis Manager

*It is new location.
Currently I am building web interface for this game.*

This game will let you manage your own semipro tennis club in one of fictional tennis leagues of the world. Unfortunately, currently only the  *Australian Tennis League* is availabe.

Why tennis and not some classic command game like football or hockey? Well, just because me personally clearly understand how to simulate tennis match correctly enough.

For now there is no gameplay, just pushing same commands again and again till the end of the regular tournament. Still there is no playoffs at the end of season, but this feature is for another day.

**game.py** runs game in text mode.
Commands:

- *show* prints a list of today's matches if any;
- *m* prints a match for managed club if any;
- *s* selects random player from managed club;
- *s [player_id]* selects a certain player from managed club if possible;
- *mp* prints list of players;
- *n* proceed to the next day (to proceed some player have to be selected)
- *cs* print current league standings;
- *cs div* print current division standings;
- *cs div all* print standings in all divisions;
