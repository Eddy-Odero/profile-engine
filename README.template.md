<div align="center">

![{{ username }} terminal]({{ terminal_svg_path }})

<sub>~ live session · {{ username }}@github · re-renders every build ~</sub>

{{ stat_badges | join(" ") }}

</div>

---

### Tech Stack

<div align="center">

![Tech Stack]({{ tech_stack_svg_path }})

**Tools**

![Tools]({{ tools_svg_path }})

</div>

### Projects

<div align="center">

![Projects]({{ project_cards_svg_path }})

</div>

{% for project in projects %}
**{{ project.name }}**
{% if project.preview_url %}[![Preview]({{ badge_preview_path }})]({{ project.preview_url }}){% else %}![not hosted yet]({{ badge_disabled_path }}) <sub>not hosted yet</sub>{% endif %} [![Code]({{ badge_code_path }})]({{ project.repo_url }})
{% endfor %}

### A quote I like

<div align="center">

![Quote]({{ quote_svg_path }})

</div>

---

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

<sub>Last rendered: {{ build_time }} · theme: {{ theme }} · auto-generated, do not edit by hand</sub>
