"""Seed the CSE program and its official 11 Program Outcomes (spec Appendix A).

A data migration, not a fixture or seed command, because the POs must exist on every
database from the first deploy: production included. The wording is copied verbatim from
Acıbadem OBS, typos and all ("of of" in PO 8). Do not fix it here.
"""

from decimal import Decimal

from django.db import migrations

PROGRAM_CODE = "CSE"
PO_SET_LABEL = "2023 curriculum"

OUTCOMES = [
    (
        1,
        "Math, science & engineering knowledge",
        "Gain adequate knowledge in mathematics, science and related engineering discipline "
        "subjects; ability to use theoretical and applied knowledge in these fields in complex "
        "engineering problems.",
    ),
    (
        2,
        "Problem solving",
        "Gain ability to identify, formulate and solve complex engineering problems; gain ability "
        "to choose and apply appropriate analysis and modeling methods for this purpose.",
    ),
    (
        3,
        "System design",
        "Gain ability to design a complex system, process, device or product to meet certain "
        "requirements under realistic constraints and Conditions; ability to apply modern design "
        "methods for this purpose.",
    ),
    (
        4,
        "Modern tools & IT",
        "Analyze and create solutions to complex problems encountered in engineering applications "
        "of modern techniques and tools for development, have skills, gain the ability to use "
        "information technology effectively.",
    ),
    (
        5,
        "Experiments & data",
        "Gain ability to design experiments, conduct experiments, collect data, analyze and "
        "interpret results for the study of complex engineering problems or discipline-specific "
        "research topics.",
    ),
    (
        6,
        "Teamwork",
        "Gain ability to work effectively in interdisciplinary and multidisciplinary teams; work "
        "individually.",
    ),
    (
        7,
        "Communication",
        "Gain ability to communicate effectively in Turkish oral and written; knowledge of at "
        "least one foreign language; ability to write effective reports and understand written "
        "report, design and production reports, make effective presentations, give and receive "
        "clear and understandable instructions.",
    ),
    (
        8,
        "Lifelong learning",
        "Gain awareness of of the need for lifelong learning; the ability to access information, "
        "monitor developments in science and technology, and constantly renew oneself.",
    ),
    (
        9,
        "Ethics & standards",
        "Act in accordance with ethical principles, awareness of professional and ethical "
        "responsibility; gain knowledge of standards used in engineering applications",
    ),
    (
        10,
        "Project, risk & change management",
        "Gain knowledge of business practices such as Project Management, risk Management and "
        "change management; gain awareness about entrepreneurship, innovation; have information "
        "about sustainable development.",
    ),
    (
        11,
        "Health, safety, environment & law",
        "Gain knowledge of the effects of engineering practices on health, environment and safety "
        "in Universal and social dimensions and the problems reflected in the field of "
        "engineering of the era; gain awareness of the legal consequences of engineering "
        "solutions.",
    ),
]


def seed(apps, schema_editor):
    Program = apps.get_model("catalog", "Program")
    ProgramOutcomeSet = apps.get_model("catalog", "ProgramOutcomeSet")
    ProgramOutcome = apps.get_model("catalog", "ProgramOutcome")

    program, _ = Program.objects.get_or_create(
        code=PROGRAM_CODE,
        defaults={
            "name": "Computer Science and Engineering",
            "attainment_threshold": Decimal("60"),
        },
    )
    po_set, _ = ProgramOutcomeSet.objects.get_or_create(
        program=program,
        label=PO_SET_LABEL,
        defaults={"effective_from_year": 2023, "is_active": True},
    )
    for number, short_name, description in OUTCOMES:
        ProgramOutcome.objects.update_or_create(
            po_set=po_set,
            number=number,
            defaults={"short_name": short_name, "description": description},
        )


def unseed(apps, schema_editor):
    Program = apps.get_model("catalog", "Program")
    Program.objects.filter(code=PROGRAM_CODE).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]