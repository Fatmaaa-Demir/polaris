import pytest

from apps.accounts import permissions as perm
from apps.catalog.selectors import offerings_visible_to

pytestmark = pytest.mark.django_db


def test_selector_agrees_with_rule(actors, offering, other_offering):
    everything = [offering, other_offering]
    for name, user in actors.items():
        via_selector = set(offerings_visible_to(user).values_list("pk", flat=True))
        via_rule = {o.pk for o in everything if perm.can_view_offering(user, o)}
        assert via_selector == via_rule, name
