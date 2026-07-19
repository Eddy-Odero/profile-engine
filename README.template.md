<div align="center">

![{{ username }} terminal]({{ terminal_svg_path }})

</div>

<div align="center">

# {{ username }}

**Status:** `{{ status }}` {{ cursor }}

{{ stat_badges | join(" ") }}

</div>

---

### `$ whoami`

```
{{ username }}
{{ tagline }}
```

### `$ stack`

```
{% for tech in stack %}{{ tech }}
{% endfor %}```

### `$ projects`

```
{% for project in projects %}{{ project }}
{% endfor %}```

### `$ github --stats`

```
Repositories : {{ repo_count }}
Stars        : {{ stars }}
Followers    : {{ followers }}
Contributions: {{ contributions if contributions is not none else "N/A" }}
Top Languages: {{ top_languages | join(", ") }}
Pinned       : {{ pinned_repos | join(", ") }}
```

### `$ github --activity`

```
{% for line in recent_activity %}{{ line }}
{% else %}no recent public activity
{% endfor %}```

### `$ leetcode --stats`

```
Solved       : {{ solved.total }} (Easy {{ solved.easy }} / Medium {{ solved.medium }} / Hard {{ solved.hard }})
Rating       : {{ rating if rating is not none else "unrated" }}
Global Rank  : {{ ranking if ranking is not none else "N/A" }}
Top %        : {{ (top_percentage ~ "%") if top_percentage is not none else "N/A" }}
Contests     : {{ contests_attended if contests_attended is not none else 0 }}
Badges       : {{ badges | join(", ") if badges else "none yet" }}
```

{% if recent_submissions %}
### `$ leetcode --recent`

```
{% for title in recent_submissions %}{{ title }}
{% endfor %}```
{% endif %}

---

<div align="center">

**Today's Quote**

> {{ quote }}

</div>

---

<sub>Last rendered: {{ build_time }} · theme: {{ theme }} · auto-generated, do not edit by hand</sub>
