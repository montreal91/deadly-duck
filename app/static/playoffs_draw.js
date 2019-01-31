
var app = new Vue({
  el: "#dd-draw-app",
  data: {
    season: CURRENT_SEASON,
    series: []
  },
  methods: {
    Next: function() {
      this.season++;
      this._GetSeries();
    },

    Previous: function() {
      if (this.season > 1) {
        this.season--;
        this._GetSeries();
      }
    },

    Update: function() {
      this._GetSeries();
    },

    _GetSeries: function() {
      axios.post("/game/playoffs/", {season: this.season}).then(
        (response) => {
          this.series = response.data.series;
        }
      );
    }
  },

  delimiters: ["[[", "]]"],
  created: function() {
    this._GetSeries();
  },

});
