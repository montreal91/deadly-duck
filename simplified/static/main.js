
let socket = io.connect("http://" + document.domain + ":" + location.port + "/tennis/");


Vue.component("player", {
  props: ["player"],
  template: "#dd-template-players",
  computed: {
  },
});

let app = new Vue({
  el: "#dd-app",
  data: {
    context: {},
    message: "A Lannister always pays his debts.",
  },
  methods: {
    NextDay: function() {
      let message = {pk: 1};
      axios.post("/api/next_day/", message)
      .then(() => {
        console.log("/api/next_day/", "OK")
      })
      .catch((error) => {console.log(error)});
    },
    SetContext: function(context) {
      this.context = context;
    },
    StartNewGame: function() {
      let message = {pk: 1};

      axios.post("/api/start_new_game/", message)
      .then(() => {
        console.log("/api/start_new_game/", "OK")
      })
      .catch((error) => {console.log(error)});
    }
  },
});

function Recieve(message) {
  app.SetContext(message);
}

socket.on("context", Recieve);
