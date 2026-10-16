# POlaris Build Guide · 00 · Tech Primer

**Read this before Sprint 1.** You already know basic Django from CSE 220: models, function views, templates, `runserver`, SQLite, the admin. This chapter covers everything POlaris adds on top of that. It's the equivalent of FlavorMap's "Django 101" part, one level up.

Each topic has the same five parts:

1. **What it is**, in two or three sentences.
2. **Why we use it.** This is the sentence to say if a grader asks.
3. **What you'll actually type**: the five or so commands or patterns you'll use daily.
4. **A tiny example** you can run.
5. **The common mistake** that costs people an evening.

You don't need to read it in one sitting. Read §1–§4 before writing any code, §5–§7 before your first page with a form, and the rest when your first story touches that tool.

| # | Topic | You need it from |
|---|---|---|
| 1 | uv (Python and packages) | Sprint 0 |
| 2 | PostgreSQL for SQLite users | Sprint 0 |
| 3 | Django features you haven't used | Sprint 1 |
| 4 | Services and selectors (how our code is layered) | Sprint 1 |
| 5 | HTMX 2 | Sprint 2 |
| 6 | Bootstrap 5.3 and dark mode | Sprint 1 |
| 7 | Chart.js 4 | Sprint 3 |
| 8 | pytest, pytest-django, factory_boy, Hypothesis | Sprint 1 |
| 9 | Docker and Docker Compose | Sprint 0 (dev), Sprint 2 (prod) |
| 10 | Celery and Redis | Sprint 5 |
| 11 | GitHub Actions | Sprint 0 |
| 12 | The Claude API call, line by line | Sprint 5 |

---

## 1. uv: Python versions, virtual environments and packages in one tool

**What it is.** uv is a fast Python package and project manager from Astral, the makers of Ruff. One tool replaces `python -m venv`, `pip install`, `pip freeze > requirements.txt` and pyenv. It reads `pyproject.toml` (what we depend on) and writes `uv.lock` (exact versions of everything, including dependencies of dependencies).

**Why we use it.** In CSE 220, "works on my machine" bugs came from different package versions. `uv.lock` is committed, so all three laptops, CI and the production image install byte-identical versions. It is also 10–100× faster than pip, which matters in CI where every minute counts.

**What you'll type**

| Command | What it does |
|---|---|
| `uv sync` | Creates `.venv/` if needed and installs exactly what `uv.lock` says. Run it after every `git pull` that touched `pyproject.toml` or `uv.lock` |
| `uv run <cmd>` | Runs a command inside the project's environment without activating it: `uv run python manage.py runserver`, `uv run pytest` |
| `uv add <pkg>` | Adds a dependency to `pyproject.toml` and updates the lock. `uv add --dev <pkg>` for test and dev tools |
| `uv remove <pkg>` | The opposite |
| `uv lock --upgrade-package django` | Upgrades one package on purpose, in its own PR |

You can still `source .venv/bin/activate` if you prefer typing `python manage.py …` directly. Both work.

**Tiny example**

```bash
uv sync
uv run python -c "import django; print(django.get_version())"   # 6.1.x
uv run python manage.py check
```

**Common mistake.** Running `pip install something` inside the venv. It works on your machine, but the package isn't in `pyproject.toml`, so CI fails with `ModuleNotFoundError`. Always use `uv add`. Second-most common: two people run `uv add` in parallel branches and both change `uv.lock`. Lock files are generated, so don't hand-merge them. Take `develop`'s version, then re-run your `uv add` (see Part 15 gotchas).

---

## 2. PostgreSQL for SQLite users

**What it is.** PostgreSQL ("Postgres") is a client–server database. SQLite was a single file that your Django process opened directly. Postgres is a separate program, running in Docker for us, that Django connects to over a network port (5432) with a username and password.

**Why we use it** (decision D7). Production runs Postgres, and testing on a different database hides real bugs. We also use features SQLite doesn't have or fakes:

- Real `CHECK` constraints.
- Partial unique indexes ("only one *active* PO set per program").
- `SELECT … FOR UPDATE` row locks for publishing.
- Proper transaction isolation levels.
- Materialized views (T2.3).

CSE 321 grades exactly these things.

### 2.1 Constraints: let the database say no

Django validation runs only when you call `full_clean()` or use a form. A management command, a shell session or a bug can skip it. A database constraint can't be skipped. We put the important rules in both places: the form gives a friendly message, and the constraint is the guarantee.

```python
class Meta:
    constraints = [
        models.CheckConstraint(condition=Q(weight__gte=1) & Q(weight__lte=5), name="lo_po_weight_range"),
        models.UniqueConstraint(fields=["learning_outcome", "program_outcome"], name="uniq_lo_po"),
    ]
```

If a write breaks a constraint, Postgres refuses it and Django raises `django.db.IntegrityError`. Note the argument name: Django 6 uses `condition=` (the old `check=` was removed).

### 2.2 Partial unique index

A normal unique constraint says "no two rows have the same X". A partial one says "no two rows *matching this condition* have the same X":

```python
models.UniqueConstraint(fields=["program"], condition=Q(is_active=True),
                        name="one_active_po_set_per_program")
```

Many inactive sets per program are fine; two active ones are impossible. To activate a new set, the service must deactivate the old one first, inside the same transaction. Otherwise the second `UPDATE` violates the index.

### 2.3 Transactions

A transaction is a group of writes that either all happen or none happen.

```python
from django.db import transaction

with transaction.atomic():
    grade.published_score = grade.score
    grade.save()
    record(user, "assessment.publish", assessment)   # if this raises, the grade change is undone too
```

Every service function in POlaris wraps its writes in `transaction.atomic()` (§4.4 of the spec). Tests run each test inside a transaction that is rolled back at the end, which is why tests don't leave data behind.

### 2.4 Isolation levels in one table

Two people working at the same time can see each other's half-finished work unless the database isolates them. Postgres offers three useful levels:

| Level | What you see | Where we use it |
|---|---|---|
| READ COMMITTED (default) | Each *statement* sees data committed before it started | Everything normal |
| REPEATABLE READ | The whole *transaction* sees one snapshot taken at its first query | Department report export (T1.7): all numbers from one moment |
| SERIALIZABLE | As if transactions ran one after another; may fail with a serialization error you must retry | Not used |

### 2.5 `select_for_update()`: row locks

```python
with transaction.atomic():
    assessment = Assessment.objects.select_for_update().get(pk=assessment_id)
    # Another request calling the same line now WAITS here until we commit.
    ...
```

It is used when publishing, so two clicks can't publish half-and-half. It only works inside `transaction.atomic()`; outside one, Django raises `TransactionManagementError`.

### 2.6 psql basics

```bash
docker compose exec db psql -U polaris polaris        # open a SQL prompt in the dev database
```

| In psql | Does |
|---|---|
| `\dt` | List tables (`catalog_course`, `outcomes_lopoweight`, …) |
| `\d outcomes_lopoweight` | Columns, indexes and constraints of one table. Good for checking a migration did what you meant |
| `SELECT count(*) FROM grading_grade WHERE published_score IS NOT NULL;` | Ordinary SQL |
| `EXPLAIN ANALYZE SELECT …;` | Shows the query plan and real timing (CSE 321 material) |
| `\q` | Quit |

Or skip psql: `uv run python manage.py dbshell` opens the same prompt.

**Common mistake.** Testing a constraint with `Model.objects.create(...)` inside a test and expecting a `ValidationError`. The database raises `IntegrityError`, and after it, the test's transaction is broken. Wrap the failing call in its own block:

```python
with pytest.raises(IntegrityError), transaction.atomic():
    LOPOWeightFactory(weight=6)
```

---

## 3. Django features you haven't used yet

### 3.1 A custom user model

**What.** We replace Django's built-in `User` with our own (`apps.accounts.models.User`): login by email, plus a student number.

**Why.** Django can only switch user models **before the first migration**. Afterwards it's a painful manual rewrite. Every serious project defines one on day one, even if it starts as a copy of the default.

**Patterns**

```python
# settings
AUTH_USER_MODEL = "accounts.User"

# anywhere else, NEVER import User directly in a model ForeignKey:
from django.conf import settings
student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

# in code that needs the class:
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user(email="elif@live.acibadem.edu.tr", password="x", first_name="Elif", last_name="Y")
```

**Common mistake.** Running `migrate` before `AUTH_USER_MODEL` is set and the accounts migration exists. The fix in dev is to throw away the database: `docker compose down -v`.

### 3.2 `CheckConstraint` and `UniqueConstraint`

These were covered in §2.1. The one Django-specific detail: after adding a constraint, run `makemigrations`. The constraint lives in a migration like any field. Read the generated migration file in your PR, because it's short and it's how reviewers check you meant it.

### 3.3 Data migrations

**What.** A migration that changes *data*, not schema. We use one to create the CSE program and the 11 official POs (S1-05), so every fresh database (dev, CI, staging, production) has them.

```bash
uv run python manage.py makemigrations catalog --empty --name seed_cse_program
```

```python
from django.db import migrations

def forwards(apps, schema_editor):
    Program = apps.get_model("catalog", "Program")          # historical model, not an import
    Program.objects.get_or_create(code="CSE", defaults={"name": "Computer Science and Engineering"})

def backwards(apps, schema_editor):
    apps.get_model("catalog", "Program").objects.filter(code="CSE").delete()

class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
```

**Common mistake.** Importing the real model (`from apps.catalog.models import Program`) inside a migration. It works today and breaks the day someone adds a field, because the migration runs against the *old* table shape. Always use `apps.get_model`.

### 3.4 Template partials (new in Django 6.0)

**What.** Named fragments inside one template file, which can be rendered on their own:

```django
{# apps/grading/templates/grading/sheet.html #}
<table>
  {% for row in sheet.rows %}
    <tr>
      {% for cell in row.cells %}
        {% partialdef cell inline %}
          <td id="cell-{{ cell.assessment_id }}-{{ cell.enrollment_id }}">{{ cell.value|default:"" }}</td>
        {% endpartialdef %}
      {% endfor %}
    </tr>
  {% endfor %}
</table>
```

```python
# full page
return render(request, "grading/sheet.html", ctx)
# only one cell, for an HTMX response
return render(request, "grading/sheet.html#cell", {"cell": cell})
```

`inline` means "render it here *and* remember it". Without `inline` the fragment is only defined, and you print it with `{% partial cell %}`.

**Why.** HTMX (§5) wants small HTML fragments back from the server. Before partials, each fragment needed its own tiny template file. Now the cell's HTML lives exactly once, next to the table that uses it, and the full page and the HTMX response can never drift apart.

**Common mistake.** The fragment uses a variable from the outer loop (`row`) that the partial-only view doesn't pass. The full page renders fine, but the HTMX response comes back with blanks. Make every partial depend only on variables you pass explicitly (`cell`, not `row.cells.0`).

### 3.5 `transaction.on_commit`

**What.** "Run this function *after* the current transaction commits successfully; if it rolls back, never run it."

```python
with transaction.atomic():
    job = IngestionJob.objects.create(...)
    transaction.on_commit(lambda: run_syllabus_extraction.delay(job.id))
```

**Why.** A Celery worker is a different process. If you call `.delay()` inside the transaction, the worker can start before the commit, look for job 42 and find nothing. With `on_commit`, the job row is guaranteed to exist when the worker looks.

**Common mistake.** Writing `transaction.on_commit(run_syllabus_extraction.delay(job.id))`. That *calls* `delay` immediately and passes its result. Wrap it in a `lambda` (or use `functools.partial`).

### 3.6 Login decorators you'll see everywhere

```python
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import require_offering_access, require_role

@login_required
@require_role("head")
def terms(request): ...

@login_required
@require_offering_access(edit=True)
def mapping(request, offering_id, offering, perms_for): ...
```

`require_offering_access` loads the offering for you, returns 404 if you may not see it, and passes `offering` and `perms_for` into the view. That's why the view signature has them.

---

## 4. Services and selectors: how our code is layered

**What.** In CSE 220 your views did everything: read the form, query, save, render. In POlaris, a view only talks HTTP. The work happens in two kinds of plain Python functions:

| File | Does | Rules |
|---|---|---|
| `services.py` | **Writes.** `publish_assessment(user, assessment)` | Validates, runs inside `transaction.atomic()`, writes an `AuditEvent`, enqueues background jobs with `on_commit`. Raises `ValidationError` with a human message |
| `selectors.py` | **Reads** that involve permissions or more than one query. `visible_enrollments(user, offering)` | Always take `user` first and scope the queryset to what that user may see |
| `scoring/engine.py` | **Maths.** Pure functions, no Django | Never touches the database |

**Why.** Three reasons:

1. The same write is triggered from several places: the grade sheet, the bulk upload, the admin, a management command. If the rule lives in the view, three of those four forget it.
2. Services are easy to test without HTTP.
3. The permission matrix test can trust that no view reads student data except through a selector.

**The pattern you'll type**

```python
# apps/grading/views.py
@login_required
@require_offering_access(edit=True)
def publish(request, offering_id, assessment_id, offering, perms_for):
    assessment = get_object_or_404(offering.assessments, pk=assessment_id)
    if request.method == "POST":
        try:
            result = services.publish_assessment(request.user, assessment)
        except ValidationError as e:
            messages.error(request, e.messages[0])
        else:
            messages.success(request, f"{assessment.name} published to {result.published} students.")
        return redirect("grading:sheet", offering_id=offering.id)
    return render(request, "grading/publish_modal.html", {"assessment": assessment, "offering": offering})
```

The view has no ORM writes and no business rules. It parses, calls, and renders.

**Common mistake.** "Just a tiny `.save()` in the view, it's faster." That save skips the audit trail and the closed-term check. The reviewer checklist (§9.7) asks about it on every PR.

---

## 5. HTMX 2: interactivity without writing JavaScript

**What it is.** A 14 KB JavaScript library that lets any HTML element send an HTTP request and put the server's HTML response somewhere on the page. You write attributes, not JS. The server keeps rendering HTML with Django templates, as you already know how to do.

**Why we use it** (decision D9). The grade sheet and the weight grids need "save this cell without reloading the page". A React frontend would mean a second app, an API, JSON serializers, and duplicated validation. HTMX gives the same feel with server-rendered templates, so all three of us work in Django only.

### 5.1 The five attributes

| Attribute | Meaning | Example |
|---|---|---|
| `hx-get` / `hx-post` | Send a GET/POST to this URL | `hx-post="{% url 'grading:cell' offering.id a.id e.id %}"` |
| `hx-trigger` | When to send it. Defaults: `click` for buttons, `change` for inputs, `submit` for forms | `hx-trigger="change"`, `hx-trigger="every 2s"`, `hx-trigger="keyup changed delay:400ms"` |
| `hx-target` | Which element receives the response (CSS selector). Default: the element itself | `hx-target="#modal-body"`, `hx-target="closest td"` |
| `hx-swap` | How to insert it | `innerHTML` (default), `outerHTML` (replace the element itself), `beforeend` |
| `hx-headers` | Extra request headers (JSON) | the CSRF token, see below |

### 5.2 Tiny runnable example: a counter

```django
{# templates/demo.html #}
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
  {% partialdef counter inline %}
    <button id="counter" hx-post="{% url 'demo' %}" hx-swap="outerHTML">Clicked {{ n }} times</button>
  {% endpartialdef %}
  <script src="{% static 'vendor/htmx.min.js' %}"></script>
</body>
```

```python
def demo(request):
    n = request.session.get("n", 0)
    if request.method == "POST":
        n = request.session["n"] = n + 1
    template = "demo.html#counter" if request.htmx else "demo.html"
    return render(request, template, {"n": n})
```

Click the button. The page doesn't reload; only the button is replaced by the new one the server rendered.

### 5.3 `request.htmx`

`django-htmx`'s middleware adds `request.htmx`, which is truthy when the request came from HTMX. That's how one view returns the full page on a normal visit and just the partial on an HTMX call (as above). Useful extras:

- `request.htmx.target` is the id of the target element.
- `from django_htmx.http import HttpResponseClientRedirect` tells HTMX to do a full browser redirect, used after a successful modal form.

### 5.4 CSRF

Django rejects any POST without a CSRF token (403). Forms include `{% csrf_token %}`, but HTMX requests from a button or an `<input>` aren't forms. We set the header once on `<body>` in `base.html`, and every HTMX request inherits it:

```django
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
```

Note the single quotes outside and double quotes inside. JSON requires double quotes.

### 5.5 Polling (the "Reading your syllabus…" page)

```django
{% partialdef status inline %}
  <div id="job-status"
       {% if job.status == "pending" or job.status == "processing" %}
         hx-get="{% url 'ingestion:status' job.id %}" hx-trigger="every 2s" hx-swap="outerHTML"
       {% endif %}>
    {{ job.get_status_display }}
  </div>
{% endpartialdef %}
```

While the job is running, the div re-fetches itself every 2 s. When the server renders it with a finished status, the new div has no `hx-trigger`, so polling stops by itself. (HTMX also stops polling if the server answers with status code 286. We use the template approach because it is visible in the HTML.)

### 5.6 Common mistakes

- **No CSRF header** gives a 403 on the first POST. Check that `base.html` has the `<body hx-headers=…>` line.
- **Returning the whole page into a cell.** The view forgot the `if request.htmx` branch, so a full page with navbar appears inside a table cell. Check the template name ends in `#partial`.
- **Losing the `id`.** With `hx-swap="outerHTML"`, the returned HTML replaces the element. If the response lacks the same `id` or `hx-*` attributes, the next interaction targets nothing.
- **Validation errors with status 400/422.** By default HTMX does *not* swap error responses. Return the error partial with status 200, or configure it. We return 200 with the error rendered in the cell.

---

## 6. Bootstrap 5.3 and dark mode

**What.** You used Bootstrap in CSE 220. What's new in 5.3 is built-in colour modes: put `data-bs-theme="dark"` on `<html>` (or any element) and every component switches to its dark palette.

**Why.** Students check their PO scores at night on phones. Dark mode costs us about ten lines.

**Patterns**

```html
<html lang="en" data-bs-theme="light">
```

```js
// static/js/polaris.js — respect the OS setting, allow an override stored in localStorage
const stored = localStorage.getItem("theme");
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
document.documentElement.dataset.bsTheme = stored ?? (prefersDark ? "dark" : "light");
```

```css
/* static/css/polaris.css — our tokens, defined for both modes */
:root, [data-bs-theme="light"] { --pl-primary: #1f3a68; --pl-accent: #e0a100; }
[data-bs-theme="dark"]          { --pl-primary: #8fb3ff; --pl-accent: #ffc94d; }
.score { font-variant-numeric: tabular-nums; }
```

Use Bootstrap's semantic classes (`text-body`, `bg-body-tertiary`, `border`) rather than fixed colours (`text-dark`, `bg-white`), because those don't flip in dark mode.

**Common mistake.** Hard-coded colours (`style="color:#000"`, `bg-white`). They look fine in light mode and become invisible in dark mode. Run through each page in both modes before marking a UI story Done.

---

## 7. Chart.js 4

**What.** A small charting library that draws on a `<canvas>`. We use bar (student PO scores), radar (T1.5), line (trend) and a heat-map-like table (that one is plain HTML).

**Why.** It's one script file, needs no build step, and does the three chart types we need. We serve it from `static/vendor/`, not a CDN, so the demo works on bad Wi-Fi.

**Pattern: data from Django, safely.** Never build JavaScript strings in a template. Use `json_script`:

```django
{{ chart_data|json_script:"po-chart-data" }}
<canvas id="po-chart" aria-label="PO scores bar chart" role="img"></canvas>
<script src="{% static 'vendor/chart.umd.min.js' %}"></script>
<script>
  const d = JSON.parse(document.getElementById("po-chart-data").textContent);
  new Chart(document.getElementById("po-chart"), {
    type: "bar",
    data: { labels: d.labels, datasets: [{ label: "Score", data: d.values }] },
    options: { indexAxis: "y", scales: { x: { min: 0, max: 100 } } },
  });
</script>
```

```python
# in the view: numbers already rounded for display, None stays None (Chart.js skips null)
ctx["chart_data"] = {
    "labels": [f"PO {po.number}" for po in pos],
    "values": [float(display(s)) if s is not None else None for s in scores],
}
```

Converting to `float` here is fine and is the one exception to "never float". These values only draw pixels, and they come from `display()`, so they are already rounded exactly like the table next to the chart. AC T1.5.1 ("radar and table show identical numbers") depends on this.

**Common mistake.** Passing a `Decimal` straight into `json_script`, which gives `TypeError: Object of type Decimal is not JSON serializable`. Convert as above. Second mistake: drawing the chart before the canvas has a size, inside a hidden Bootstrap tab. Create it on the tab's `shown.bs.tab` event.

---

## 8. Testing: pytest, pytest-django, factory_boy, Hypothesis

### 8.1 pytest

**What.** A test runner where tests are plain functions with plain `assert`s. It replaces `manage.py test` and `unittest` classes.

```python
def test_weighted_average_of_the_slide_example():
    assert weighted_average([(Decimal("90"), Decimal("60")), (Decimal("80"), Decimal("40"))]) == Decimal("86")
```

| Command | Does |
|---|---|
| `uv run pytest` | Everything |
| `uv run pytest apps/scoring` | One folder |
| `uv run pytest -k publish` | Tests whose name contains "publish" |
| `uv run pytest -x --lf` | Stop at first failure; rerun only last failures |
| `uv run pytest --cov --cov-report=term-missing` | Coverage, with the missed line numbers |

### 8.2 pytest-django

It adds Django to pytest through **fixtures**: arguments you name in your test function, which pytest creates for you.

| Fixture / marker | Gives you |
|---|---|
| `@pytest.mark.django_db` | Permission to touch the (test) database; rolled back after the test |
| `client` | Django's test client (`client.get(url)`) |
| `django_user_model` | The `User` class |
| `django_assert_max_num_queries` | `with django_assert_max_num_queries(5): client.get(url)` fails on N+1 |
| `settings` | Change a setting for one test: `settings.CELERY_TASK_ALWAYS_EAGER = True` |
| `mailoutbox` | Emails sent during the test |

Our own fixtures live in the root `conftest.py` (§4.8 code map): `client_as("instructor")`, `elif_data`.

```python
@pytest.mark.django_db
def test_student_cannot_open_someone_elses_course(client_as, elif_data):
    client = client_as("student")
    response = client.get(reverse("student:course", args=[elif_data.offering.id]))
    assert response.status_code == 404
```

### 8.3 factory_boy

**What.** Factories build valid model objects with sensible defaults, so a test states only what matters to it.

```python
# apps/core/tests/factories.py
import factory
from decimal import Decimal

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"
    email = factory.Sequence(lambda n: f"user{n}@live.acibadem.edu.tr")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.django.Password("pw")

class AssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "outcomes.Assessment"
    offering = factory.SubFactory("apps.core.tests.factories.OfferingFactory")
    name = factory.Sequence(lambda n: f"Quiz {n}")
    kind = "quiz"
    max_score = Decimal("100")
```

```python
quiz = AssessmentFactory(max_score=Decimal("20"))      # offering, course, term, program all created for you
AssessmentFactory.create_batch(5, offering=quiz.offering)
```

**Common mistake.** `SubFactory` chains quietly create *new* parents for every object. Twenty grades made with `GradeFactory()` belong to twenty different offerings. Pass the shared parent explicitly (`GradeFactory(assessment=a, enrollment=e)`) or use the `elif_scenario()` helper.

### 8.4 Hypothesis (property-based testing)

**What.** Instead of you choosing example inputs, Hypothesis generates hundreds of random inputs and checks that a *property* always holds. When it finds a failure, it shrinks it to the smallest failing input.

**Why.** The engine must be right for every possible mapping, not just the slide example. Properties like "multiplying all weights by the same factor doesn't change any score" (scale invariance) catch bugs no hand-picked example would.

```python
from decimal import Decimal
from hypothesis import given, strategies as st

scores = st.decimals(min_value=0, max_value=100, places=2)
weights = st.decimals(min_value=Decimal("0.01"), max_value=100, places=2)

@given(st.lists(st.tuples(scores, weights), min_size=1, max_size=8))
def test_weighted_average_stays_between_min_and_max(pairs):
    avg = weighted_average(pairs)
    values = [s for s, _ in pairs]
    assert min(values) <= avg <= max(values)
```

**Common mistake.** Comparing Decimals that went through a division with `==`. `100/3` has a last-digit difference depending on the order of operations. Use a tolerance: `assert abs(a - b) < Decimal("1e-20")` (the spec's §2.6 does this).

---

## 9. Docker and Docker Compose

**What it is.**

| Term | Meaning |
|---|---|
| **Image** | A packaged filesystem plus a start command, built from a `Dockerfile`. Example: `postgres:17`, or our `ghcr.io/onurhaniffa/polaris:<sha>` |
| **Container** | A running instance of an image. Delete it and start a new one: same result |
| **Volume** | Storage that survives container deletion. Our Postgres data lives in the volume `pgdata` |
| **Compose** | A YAML file listing several containers that run together, started with one command |

**Why we use it.** Locally: Postgres 17 and Redis 7 with zero installation, identical on Mac, Windows and Linux. In production: the exact image CI tested is what runs on the server.

**Two compose files, two jobs**

| | `compose.yml` (dev) | `compose.prod.yml` (staging/prod) |
|---|---|---|
| Runs | `db`, `redis` only | `web`, `worker`, `db`, `redis` (plus `beat` from T2.2). One shared Caddy on the server sits in front of both stacks and handles HTTPS |
| Django | On your laptop (`uv run python manage.py runserver`) for auto-reload and debugger | In the `web` container (gunicorn) |
| Built by | Nobody; uses public images | CI builds our image and pushes it to GHCR |

**What you'll type**

| Command | Does |
|---|---|
| `docker compose up -d` | Start db + redis in the background |
| `docker compose ps` | Are they running and healthy? |
| `docker compose logs -f db` | Follow a service's logs |
| `docker compose down` | Stop and remove containers. **Data stays** (the volume survives) |
| `docker compose down -v` | Stop and **delete the volumes**: an empty database next time. Use it on purpose only |
| `docker compose exec db psql -U polaris polaris` | Run a command inside a running container |

**Common mistake.** Treating `down -v` as "restart". It wipes your local database, including any test data you typed in. Also: a native Postgres installed with Homebrew already holds port 5432, and Docker's fails with "port is already allocated". Stop the native one (`brew services stop postgresql@17`).

---

## 10. Celery and Redis: background jobs

**What it is.**

- A **task** is a Python function decorated with `@shared_task`.
- Calling `task.delay(42)` doesn't run it. It writes a message ("run task X with argument 42") into a **broker**.
- A separate **worker** process (`celery -A config worker`) reads messages from the broker and runs them.
- Our broker is **Redis**, an in-memory key-value store that also serves as Django's cache.
- **Celery beat** is a third process that sends tasks on a schedule, like cron.

```
 web (Django) ──delay()──► Redis (queue) ──► worker ──► Claude API / WeasyPrint / emails
                                             ▲
                         beat (schedule) ────┘
```

**Why we use it** (decision D8). Reading a syllabus with Claude takes 20–60 s, and building a PDF takes a few seconds. A web request that slow times out and blocks a gunicorn worker. Background tasks let the page return immediately and poll for the result (HTMX §5.5). Django 6's built-in Tasks framework defines the API but ships no production worker yet, so we use Celery.

**What you'll type**

```python
# apps/reports/tasks.py
from celery import shared_task

@shared_task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=30, max_retries=4)
def build_export(self, export_id: int):
    export = ExportJob.objects.get(pk=export_id)
    ...
```

```python
# enqueue from a service, after commit (see §3.5)
transaction.on_commit(lambda: build_export.delay(export.id))
```

```bash
uv run celery -A config worker -l info          # run a worker locally (Sprint 5+)
uv run celery -A config beat -l info            # run the scheduler (T2.2)
```

| Option | Meaning |
|---|---|
| `autoretry_for=(…)` | Retry automatically when these exceptions are raised |
| `retry_backoff=30` | Wait 30 s, then 60, 120… between retries |
| `max_retries=4` | Then give up (we mark the job FAILED) |
| `CELERY_TASK_ACKS_LATE=True` (settings) | A message is removed from the queue only after the task finishes, so a crashed worker's task is redelivered. This means tasks must be **idempotent**: running one twice must be harmless |

**Eager mode in tests and early dev.** `CELERY_TASK_ALWAYS_EAGER = True` makes `.delay()` run the task immediately, in the same process. There's no worker, and no Redis needed for the queue. Our `test.py` settings always use it, and `dev.py` uses it until Sprint 5. Note: `on_commit` callbacks don't fire inside a normal test transaction. Use pytest-django's `django_capture_on_commit_callbacks(execute=True)` fixture.

**Common mistake.** Passing a model object to a task (`build_export.delay(export)`). Arguments must be JSON-serialisable, and even if they weren't, the object would be stale by the time the worker runs. Always pass the **id** and re-fetch.

---

## 11. GitHub Actions

**What it is.** GitHub runs commands for us on a fresh Linux machine whenever something happens in the repo. The pieces:

| Term | Meaning | Ours |
|---|---|---|
| Workflow | A YAML file in `.github/workflows/` | `ci.yml`, `cd.yml` |
| Trigger (`on:`) | When it runs | `pull_request`, `push` to `develop`/`main`, `workflow_call` |
| Job | A group of steps on one machine; jobs run in parallel unless `needs:` says otherwise | `lint`, `test`, `deploy-check`, `docker-build`, `deploy` |
| Step | One command (`run:`) or a reusable action (`uses:`) | `uv run pytest`, `actions/checkout@v7` |
| Service container | A Docker container next to the job | Postgres and Redis for `test` |
| Secret | An encrypted value, never printed in logs | `SSH_KEY`, `ANTHROPIC_API_KEY` for staging |
| Required check | Branch protection blocks the merge until this job is green | `lint`, `test`, `deploy-check`, `docker-build` |

**Why we use it.** Every PR is linted and tested before review, so reviewers read code instead of hunting syntax errors. CSE 311 report Section 5 asks for the YAML and run summaries. The CI writes a coverage table into each run's summary page for exactly that.

**What you'll do**

- Open a PR. Watch the checks at the bottom of the page.
- A red check: click **Details**, read the failing step's log, fix locally, push again. The checks rerun.
- Run the same commands locally first, so CI never surprises you: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- Re-run a flaky job: **Re-run failed jobs** on the run page. If something is flaky twice, open a bug issue, because flaky tests destroy trust in CI.

**Common mistake.** "It passes locally" when your local `.env` has a variable CI doesn't. CI sets only the variables in the workflow's `env:` block. If you add a setting read with `env("NEW_THING")` and no default, add it to `ci.yml` and `.env.example` in the same PR.

---

## 12. The Claude API call, line by line (spec §7.5)

**What it is.** The Anthropic Python SDK sends a request to Claude and returns a response. We send a syllabus (PDF, image or text) plus instructions, and ask for an answer that must match a Pydantic schema (`SyllabusExtraction`). The SDK validates it and gives us a typed Python object.

**Why this shape.** Free-text answers would need fragile parsing. Structured output means the response is guaranteed to fit our schema, or the call fails loudly. We still check *meaning* afterwards in `validate_and_derive` (§7.6), because a well-formed answer can still be wrong.

```python
_client = anthropic.Anthropic(timeout=300.0, max_retries=2)
```

Create the client once per process. It reads `ANTHROPIC_API_KEY` from the environment, which is why the key never appears in code. `timeout=300` allows long documents. `max_retries=2` lets the SDK retry quick blips (rate limit 429, server 5xx, dropped connection) by itself.

```python
response = _client.beta.messages.parse(
```

`messages` is the main API. `.parse(...)` is the variant that takes a Pydantic model and parses the answer into it. It's under `beta` because the server-side fallback option we use below is a beta feature.

```python
    model=settings.ANTHROPIC_MODEL,          # "claude-opus-5-5", overridable via the environment
    max_tokens=16000,                        # upper bound on the answer length; a syllabus extraction uses ~2–5k
    system=SYSTEM_PROMPT,                    # the rules (only extract what's in the document, quote sources…)
```

The **system** prompt sets the rules. It is versioned (`PROMPT_VERSION`) and stored on each job, so we know which prompt produced which result.

```python
    messages=[{"role": "user", "content": _content_blocks(path, media_type, po_list_text)}],
```

One user turn made of two **content blocks**. The first is the document (`{"type": "document", …}` for PDF, `{"type": "image", …}` for photos, or text for DOCX converted beforehand), base64-encoded. The second is the instruction, including the 11 POs written out in full so the model maps against the official wording.

```python
    output_format=SyllabusExtraction,        # the answer MUST match this Pydantic schema
    output_config={"effort": "high"},        # think harder: mapping LOs to POs is judgment
    betas=["server-side-fallback-2026-07-01"],
    extra_body={"fallbacks": "default"},     # if a classifier wrongly refuses, retry on a fallback model in the same call
)
```

```python
if response.stop_reason == "refusal": ...       # the model declined: friendly FAILED message
if response.stop_reason == "max_tokens": ...    # answer cut off: document too long
return response.parsed_output, response          # a SyllabusExtraction instance, plus the raw response for usage/cost
```

Always check **`stop_reason`** before trusting the output. `"end_turn"` is normal. The caller stores the following on the `IngestionJob`, which gives us cost tracking and a way to ask Anthropic support about a specific call:

- `response.usage.input_tokens`
- `response.usage.output_tokens`
- `response.model`
- the request id

**What you'll type**

```bash
# one-off manual test from a shell (costs a few cents)
uv run python manage.py shell
>>> from pathlib import Path
>>> from apps.ingestion.extraction import extract_syllabus
>>> out, resp = extract_syllabus(Path("seed/syllabi/cse311.pdf"), "application/pdf", "PO 1: …")
>>> out.learning_outcomes[0], resp.usage
```

**Tests never call the API.** They mock `_client.beta.messages.parse` and return a fixture `SyllabusExtraction` (spec §7.10). The accuracy eval (§7.9) is a separate script you run by hand.

**Common mistakes**

- Committing the API key, or putting it in a template or JavaScript. It lives only in `.env` (gitignored) and in server/CI secrets. If it leaks, revoke it in the Anthropic Console first, then clean up.
- Calling the API inside a web request. Always use the Celery task: the call can take a minute.
- Trusting `parsed_output` blindly. The schema guarantees shape, not truth. `validate_and_derive` checks that weights are in range, that POs exist in the active set, and that every LO has a source quote.

---

## Where to go next

- Spec §0.4 (conventions) and §4.8 (code map) before you write code.
- The build guide chapter for your current sprint (`docs/build/sprint-NN.md`).
- Part 15 of the spec (gotchas) when something behaves strangely.
