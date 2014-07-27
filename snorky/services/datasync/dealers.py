import abc
from collections import namedtuple
from functools import wraps
from miau.common.types import PY2, StringTypes, Number, MultiDict, items
from snorky.services.datasync.delta import \
        Delta, InsertionDelta, UpdateDelta, DeletionDelta


class BadQuery(Exception):
    pass


class Dealer(object):
    __metaclass__ = abc.ABCMeta
    __slots__ = tuple()

    @property
    def name(self):
        return self.__class__.__name__

    @abc.abstractmethod
    def add_subscription_item(self, item): pass

    @abc.abstractmethod
    def remove_subscription_item(self, item): pass

    @abc.abstractmethod
    def get_subscription_items_for_model(self, model): pass

    def deliver_delta(self, delta):
        """Receives a delta, computes a set of destination subscriptions
        items and forwards the delta to them.

        Please note that altough InsertionDelta and DeletionDelta will
        always trigger deltas of the same time on the client, UpdateDelta
        may not. To understand this fact, see the next example:

        Suppose our model class composes a player name and a color, i.e.
        'id: 1, name: Alice, color: blue'.

        We may also have a dealer named 'Players with color' that uses the
        `color` attribute to filter players.

        A client maybe subscripted to players with color red, showing them in a
        list. Now, if Alice changes its color to red, this client will receive
        a insertion delta instead of an update one because they had no previous
        knowledge of Alice's model and will have to render it as a new row.

        If then Alice decides to change her player name, the client will
        receive a delta update because they already knew Alice's model.

        And lastly, if Alice changes its color again to other than red the new
        model will no longer satisfy the filter and thus a deletion delta will
        be sent to the client.
        """

        if isinstance(delta, InsertionDelta) or \
           isinstance(delta, DeletionDelta):
            deliver_to = self.get_subscription_items_for_model(delta.data)

            for subscription_item in deliver_to:
                subscription_item.subscription.deliver_delta(delta)

        else:
            # If origin delta is an update
            model = delta.model
            new_data = delta.new_data
            old_data = delta.old_data

            set_old = self.get_subscription_items_for_model(old_data)
            set_new = self.get_subscription_items_for_model(new_data)

            # Prepare every type of destination delta
            insertion_delta = InsertionDelta(model, new_data)
            update_delta = delta
            deletion_delta = DeletionDelta(model, old_data)

            # For the subscription items that do not match the filter with the
            # old data but do with the new data, send a insertion delta.
            for item in set_new - set_old:
                item.subscription.deliver_delta(insertion_delta)

            # For the subscription items that match the filter with both the
            # new and old data, send an update delta.
            for item in set_old.intersection(set_new):
                item.subscription.deliver_delta(update_delta)

            # For the subscription items that match the filter with the old
            # data but do not match with the new data, send a deletion delta.
            for item in set_old - set_new:
                item.subscription.deliver_delta(deletion_delta)


class BroadcastDealer(Dealer):
    name = 'broadcast'
    __slots__ = ('items',)

    def __init__(self):
        super(BroadcastDealer, self).__init__()
        self.items = set()

    def add_subscription_item(self, item):
        self.items.add(item)

    def remove_subscription_item(self, item):
        self.items.remove(item)

    def get_subscription_items_for_model(self, model):
        return self.items


class SimpleDealer(Dealer):
    __slots__ = ('items_by_model_key',)
    # TODO Use MultiDict

    def __init__(self):
        super(SimpleDealer, self).__init__()
        self.items_by_model_key = MultiDict()

    @abc.abstractmethod
    def get_key_for_model(self, model): pass

    def add_subscription_item(self, item):
        self.items_by_model_key.add(item.query, item)

    def remove_subscription_item(self, item):
        self.items_by_model_key.remove(item.query, item)

    def get_subscription_items_for_model(self, model):
        query = self.get_key_for_model(model)

        # Return the set of items with this query, or an empty set if
        # there is none.
        return self.items_by_model_key.get_set(query)


FilterAssociation = namedtuple('FilterAssociation',
                               ('filter', 'subscription_item'))

"""
Filter syntax
=============

['=', 'color', 'blue']
color is 'blue'

['<', 'age', 21]
age is less than 21

['>=', 'age', 21]
age is greater than or equal to 21

['and', ['=', 'service', 'prosody'], ['>=', 'severity_level', 3]]
service is 'prosody' and severity_level is greater than or equal to 3

['or', ['not', ['=', 'service', 'java']], ['>=', 'severity_level', 3]]
service is not 'java' or severity_level is greater than or equal to 3

['=', 'player.color', 'blue']
color of player is 'blue'
"""

def get_field(model, name):
    """
    Given a dictionary for `model` and a dot separated string for `name`,
    accesses the named properties in model.

    e.g. get_field(model, 'service.name') returns model['service']['name']
    """
    prop = model
    for prop_name in name.split('.'):
        prop = model[prop_name]
    return prop

def false_on_raise(function):
    @wraps(function)
    def _false_on_raise(*args):
        try:
            return function(*args)
        except (KeyError, TypeError):
            # KeyError: missing property
            # TypeError: unorderable types (e.g. compared str with int)
            return False
    return _false_on_raise

def orderable_types(a, b):
    return (isinstance(a, Number) and isinstance(b, Number)) or \
            (isinstance(a, StringTypes) and isinstance(b, StringTypes))

@false_on_raise
def filter_eq(model, field, value):
    return get_field(model, field) == value

@false_on_raise
def filter_lt(model, field, value):
    field_value = get_field(model, field)
    # Python3 does not allow to compare strings with numbers, emulate that.
    if PY2 and not orderable_types(field_value, value):
        raise TypeError
    return field_value < value

@false_on_raise
def filter_lte(model, field, value):
    field_value = get_field(model, field)
    # Python3 does not allow to compare strings with numbers, emulate that.
    if PY2 and not orderable_types(field_value, value):
        raise TypeError
    return field_value <= value

@false_on_raise
def filter_gt(model, field, value):
    field_value = get_field(model, field)
    # Python3 does not allow to compare strings with numbers, emulate that.
    if PY2 and not orderable_types(field_value, value):
        raise TypeError
    return field_value > value

@false_on_raise
def filter_gte(model, field, value):
    field_value = get_field(model, field)
    # Python3 does not allow to compare strings with numbers, emulate that.
    if PY2 and not orderable_types(field_value, value):
        raise TypeError
    return field_value >= value

@false_on_raise
def filter_not(model, expr):
    return not filter_matches(model, expr)

@false_on_raise
def filter_and(model, *expressions):
    return all(filter_matches(model, expr)
               for expr in expressions)

@false_on_raise
def filter_or(model, *expressions):
    return any(filter_matches(model, expr)
               for expr in expressions)

operator_functions = {
    '==': filter_eq,
    '<': filter_lt,
    '<=': filter_lte,
    '>': filter_gt,
    '>=': filter_gte,
    'and': filter_and,
    'or': filter_or,
    'not': filter_not,
}

def filter_matches(model, filter):
    op = filter[0]
    args = filter[1:]
    return operator_functions[op](model, *args)

class FilterDealer(Dealer):
    __slots__ = ('filters_by_item',)

    def __init__(self):
        super(FilterDealer, self).__init__()
        self.filters_by_item = {}

    def add_subscription_item(self, item):
        if not isinstance(item.query, list):
            raise BadQuery

        filter = item.query
        self.filters_by_item[item] = filter

    def remove_subscription_item(self, item):
        del self.filters_by_item[item]

    def get_subscription_items_for_model(self, model):
        for subscription_item, filter in items(self.filters_by_item):
            if filter_matches(model, filter):
                yield subscription_item

