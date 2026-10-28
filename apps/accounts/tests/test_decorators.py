import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.test import RequestFactory

from apps.accounts.decorators import require_offering_access, require_role

pytestmark = pytest.mark.django_db


@require_role("head")
def head_view(request):
    return HttpResponse("ok")


@require_offering_access(edit=True)
def edit_view(request, offering, perms_for):
    return HttpResponse(f"{offering.pk}:{perms_for.can_edit}")


def request_for(user):
    request = RequestFactory().get("/x/")
    request.user = user
    return request


def test_require_role_redirects_anonymous():
    from django.contrib.auth.models import AnonymousUser

    response = head_view(request_for(AnonymousUser()))
    assert response.status_code == 302


def test_require_role_404_for_wrong_role(outsider):
    with pytest.raises(Http404):
        head_view(request_for(outsider))


def test_require_role_allows_head_and_superuser(head, superuser):
    assert head_view(request_for(head)).status_code == 200
    assert head_view(request_for(superuser)).status_code == 200


def test_offering_access_passes_offering_and_permissions(instructor, offering):
    response = edit_view(request_for(instructor), offering_id=offering.pk)
    assert response.content == f"{offering.pk}:True".encode()


def test_offering_access_404_for_foreign_offering(outsider, offering):
    with pytest.raises(Http404):
        edit_view(request_for(outsider), offering_id=offering.pk)


def test_offering_access_404_for_missing_offering(superuser):
    with pytest.raises(Http404):
        edit_view(request_for(superuser), offering_id=999999)


def test_offering_access_403_when_term_is_closed(instructor, offering):
    from apps.catalog.models import Term

    offering.term.status = Term.Status.CLOSED
    offering.term.save()

    with pytest.raises(PermissionDenied):
        edit_view(request_for(instructor), offering_id=offering.pk)
