
//
// Client-side logic for main screen of the game.
//
// Created on Jan 21, 2019
//
// @author: montreal91
//

let app = new Vue({
  el: "#dd-main-screen-app",
  data: {
    away_player: null,
    hello: "Hello",
    match: null,
    players: "Nonez",
    selected: null,
    show_away_player: false,
  },
  computed: {
    //
    // Shows match banner like "Team A versut Team B"
    //
    match_banner: function() {
      if (this.match !== null) {
        return this.match.home_team + " versus " + this.match.away_team;
      }
      return "No matches for today";
    },
  },
  methods: {
    //
    // Returns good presentation of floats.
    //
    FloatToFixed: function(x) {
      return Number.parseFloat(x).toFixed(1);
    },

    //
    // Sends request to the server to start a new day.
    //
    NextDay: function() {
      if (this.selected === null && this.match !== null) {
        // TODO: in this case we should let user know that (s)he needs
        // to choose a player for next match...
        return;
      }

      axios.post("/game/next_day/", {selected_player: this.selected}).then(
        (response) => {
          window.location.href = response.data.new_href;
        }
      ).catch(
        (e) => {
          console.log(e);
        }
      );
    },

    //
    // Returns good representation for player name.
    //
    PlayerName: function(player) {
      return player.first_name + " " + player.last_name;
    },

    //
    // Selects player for the next match.
    //
    SelectPlayer: function(player) {
      this.selected = player.pk;
    },

    //
    // Toggles flag which is responsible for showing data of away player.
    //
    ToggleShowAwayPlayer: function() {
      this.show_away_player = !this.show_away_player;
    },

    _GetPlayers: function() {
      axios.post("/game/api/main_screen_context/", {season: 1}).then(
        (response) => {
          this.away_player = response.data.away_player;
          this.match = response.data.match;
          this.players = response.data.players;
        }
      ).catch(
        (e) => {
          console.log(e)
        }
      );
    },
  },

  created: function() {
    this._GetPlayers();
  },
});
