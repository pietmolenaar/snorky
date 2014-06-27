$(function() {

  var snorky = new Snorky(WebSocket, "ws://localhost:5800/", {
    "messaging": Snorky.Messaging
  }, true);

  var messaging = snorky.services.messaging;

  $("#frmRegister").submit(function(ev) {
    ev.preventDefault();

    messaging.registerParticipant({
      name: $("#txtParticipantName").val()
    }).then(function() {
      $("#statusRegister").text("Successfully registered");
    }, function(err) {
      $("#statusRegister").text("Register error: " + err.message);
    });
  });

  $("#btnUnregister").click(function() {
    messaging.unregisterParticipant({
      name: $("#txtParticipantName").val()
    }).then(function() {
      $("#statusRegister").text("Successfully unregistered");
    }, function(err) {
      $("#statusRegister").text("Unregister error: " + err.message);
    });
  });

  $("#btnListParticipants").click(function() {
    messaging.listParticipants({}).then(function(participants) {
      $("#ulParticipants").empty();
      $.each(participants, function(i, participant) {
        $("#ulParticipants").append($("<li/>", { text: participant }));
      });
      $("#statusParticipants").text("Participants listed");
    }, function(err) {
      $("#ulParticipants").empty();
      $("#statusParticipants").text("Error: " + err.message);
    });
  });

  $("#frmMessages").submit(function(ev) {
    ev.preventDefault();

    messaging.send({
      sender: $("#txtFrom").val(),
      dest: $("#txtTo").val(),
      body: $("#txtMessage").val()
    }).then(function() {
      $("#statusMessages").text("Successfully sent");
    }, function(err) {
      $("#statusMessages").text("Error: " + err.message);
    });
  });

  messaging.onParticipantMessage = function(sender, dest, body) {
    $("#ulMessages").append($("<li/>", {
      text: sender + " to " + dest + ": " + body
    }));
  };

});
