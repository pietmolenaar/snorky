// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

"use strict";

var DataSync = Snorky.DataSync;

describe("ArrayCollection", function() {
  var array, collection;

  beforeEach(function() {
    array = ["red", "blue"];
    collection = new DataSync.ArrayCollection(array);
  });

  it("can insert elements", function() {
    collection.insert("orange");
    expect(array).toEqual(["red", "blue", "orange"]);
  });

  describe("iterator", function() {
    var iter;

    beforeEach(function() {
      iter = collection.getIterator();
    });

    it("can read elements", function() {
      expect(iter.hasNext()).toBe(true);
      expect(iter.next()).toEqual("red");
      expect(iter.hasNext()).toBe(true);
      expect(iter.next()).toEqual("blue");
      expect(iter.hasNext()).toBe(false);
    });

    it("throws if read too far", function() {
      iter.next();
      iter.next();
      expect(iter.hasNext()).toBe(false);

      expect(function() {
        iter.next();
      }).toThrow(new Error("Busted iterator"));
    });

    it("can update elements", function() {
      iter.next();
      iter.update("black")

      expect(array).toEqual(["black", "blue"]);
    });

    it("throws if updated too soon", function() {
      expect(function() {
        iter.update("black");
      }).toThrowError("Iterator not pointing to an item! (call next())");
    });

    it("can delete elements", function() {
      iter.next();
      iter.remove();

      expect(array).toEqual(["blue"]);

      expect(iter.hasNext()).toBe(true);
      expect(iter.next()).toEqual("blue");
      iter.remove();
      expect(array).toEqual([]);
      expect(iter.hasNext()).toBe(false);
    });

    it("throws if deleted too soon", function() {
      expect(function() {
        iter.remove();
      }).toThrowError("Iterator not pointing to an item! (call next())");
    });

    it("throws if deleted twice", function() {
      iter.next();
      iter.remove();
      expect(function() {
        iter.remove();
      }).toThrowError("Iterator pointing to a deleted item! (call next())");
    });

    it("throws if deleted then updated", function() {
      iter.next();
      iter.remove();
      expect(function() {
        iter.update("black");
      }).toThrowError("Iterator pointing to a deleted item! (call next())");
    });
  });
});


describe("SingleItemCollection", function() {
  var collection, value;

  var read = function() {
    return value;
  };
  var update = function(newVal) {
    value = newVal;
  };
  var remove = jasmine.createSpy("remove");

  beforeEach(function() {
    value = "red";
    collection = new DataSync.SingleItemCollection(read, update, remove);

    spyOn(console, "error");
  });

  it("cannot insert elements", function() {
    collection.insert("orange");
    expect(console.error).toHaveBeenCalledWith(
      "Received insert() request in SingleItemCollection");
  });

  describe("iterator", function() {
    var iter;

    beforeEach(function() {
      iter = collection.getIterator();
    });

    it("can read element", function() {
      expect(iter.hasNext()).toBe(true);
      expect(iter.next()).toEqual("red");
      expect(iter.hasNext()).toBe(false);
    });

    it("throws if read too far", function() {
      iter.next();
      expect(iter.hasNext()).toBe(false);

      expect(function() {
        iter.next();
      }).toThrow(new Error("Busted iterator"));
    });

    it("can update elements", function() {
      iter.next();
      iter.update("black")

      expect(value).toEqual("black");
    });

    it("throws if updated too soon", function() {
      expect(function() {
        iter.update("black");
      }).toThrowError("Iterator not pointing to an item! (call next())");
    });

    it("can delete elements", function() {
      iter.next();
      iter.remove();

      expect(remove).toHaveBeenCalled();
      expect(iter.hasNext()).toBe(false);
    });

    it("throws if deleted too soon", function() {
      expect(function() {
        iter.remove();
      }).toThrowError("Iterator not pointing to an item! (call next())");
    });
  });
});



describe("ArrayCollection options", function() {
  // A simple model class which can be used as item transformer
  var Person = function(item) {
    return {
      "name": item.name,
      "whoAmI": function() {
        return "I am " + item.name;
      }
    };
  };
  var array, collection;

  beforeEach(function() {
    array = [Person({ name: "Alice" })];
    collection = new DataSync.ArrayCollection(array, {
      transformItem: Person
    });
  });

  it("adds transformed items", function() {
    collection.insert({ name: "Bob" })

    expect(array.length).toEqual(2);
    expect(array[1].name).toEqual("Bob");
    expect(array[1].whoAmI()).toEqual("I am Bob");
  });

  it("applies transformation on updated items", function() {
    var iter = collection.getIterator();
    iter.next();
    iter.update({ name: "Bob" });

    expect(array.length).toEqual(1);
    expect(array[0].name).toEqual("Bob");
    expect(array[0].whoAmI()).toEqual("I am Bob");
  });
});
