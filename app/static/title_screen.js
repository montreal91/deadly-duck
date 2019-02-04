//
// Client-side logic for main screen of the game.
//
// Created on Feb 02, 2019
//
// @author: montreal91
//

// TODO(montreal91) create docstrings for data members and public methods.
let app = new Vue({
  el: "#dd-title-screen-app",
  data: {
    hello: "hello hello",
    clubs: [],
    new_career: false,
    continue_career: false,
  },
  computed: {},
  methods: {
    ContinueCareer: function() {
      this.continue_career = true;
      this.new_career = !this.continue_career;
    },
    NewCareer: function() {
      this.new_career = true;
      this.continue_career = !this.new_career;
      if (this.clubs.length === 0) {
        console.log(0);
        this._GetClubs();
      }
    },
    _GetClubs: function() {
      axios.post("/game/api/clubs/", {}).then(
        (response) => {
          this.clubs = response.data.clubs;
        }
      ).catch(
        (e) => {
          console.log(e);
        }
      );
    },
  },
  created: function() {},
});
