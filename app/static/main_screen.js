
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
    hello: "Hello",
    players: "Nonez",
    selected: null,
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
      if (this.selected === null) {
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

    _GetPlayers: function() {
      axios.post("/game/api/current_user_club_players/", {season: 1}).then(
        (response) => {
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
