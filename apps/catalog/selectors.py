"""Read-only queries for the catalog. Lower layers handle PO-set resolution (spec §4.8)."""

from apps.accounts.models import ProgramMembership
from .models import ProgramOutcomeSet


def active_po_set(program):
    """The program's active PO set. The partial unique index guarantees at most one."""
    return ProgramOutcomeSet.objects.get(program=program, is_active=True)


def po_set_ids_for_students(student_ids, program):
    """Policy P13 for many students at once, in two queries: {student_id: po_set_id}."""
    sets = list(
        ProgramOutcomeSet.objects.filter(program=program)
        .order_by("-effective_from_year", "-id")
        .values_list("id", "effective_from_year", "is_active")
    )
    active_ids = [set_id for set_id, _, is_active in sets if is_active]
    if not active_ids:
        raise ProgramOutcomeSet.DoesNotExist(f"{program} has no active PO set")
    
    cohorts = dict(
        ProgramMembership.objects.filter(
            user_id__in=student_ids, program=program, role=ProgramMembership.Role.STUDENT
        ).values_list("user_id", "cohort_year")
    )

    def pick(cohort_year):
        if cohort_year is not None:
            for set_id, year, _ in sets:
                if year <= cohort_year:
                    return set_id
        return active_ids[0]

    return {student_id: pick(cohorts.get(student_id)) for student_id in student_ids}


def po_set_for_student(student, program):
    """The PO set one student's profile is shown against (P13)."""
    set_id = po_set_ids_for_students([student.id], program)[student.id]
    return ProgramOutcomeSet.objects.get(pk=set_id)