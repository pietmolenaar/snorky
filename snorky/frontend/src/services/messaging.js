// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

(function() {
  "use strict";

  var Class = Snorky.Class;

  Snorky.Messaging = new Class(Snorky.RPCService, {
    init: function() {
      Snorky.RPCService.prototype.init.call(this);

      this.notificationReceived.add(this.onNotification, this);
      this.messageReceived = new Snorky.Signal();
    },

    onNotification: function(message) {
      if (message.type == "message") {
        this.messageReceived.dispatch(message);
      } else {
        console.error("Unknown message type in messaging service: " +
                      message.type);
      }
    }
  });
  Snorky.Messaging.addRPCMethods([
    "registerParticipant",
    "unregisterParticipant",
    "listParticipants",
    "send"
  ]);

})();
