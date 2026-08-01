<div align="center">

![{{ username }} terminal]({{ terminal_svg_path }})

<sub>~ live session · {{ username }}@github · re-renders every build ~</sub>

{{ stat_badges | join(" ") }}

</div>

---

<div align="center">

![System Modules header]({{ section_headers['System Modules'] }})

![System Modules]({{ skill_modules_svg_path }})

</div>

<div align="center">

![Projects header]({{ section_headers['Projects'] }})

</div>

<table>
{% for row in project_cards|batch(4) %}
<tr>
{% for project in row %}
<td align="center" width="220">

![{{ project.name }}]({{ project.card_svg_path }})

<table><tr>
<td align="left">{% if project.preview_url %}[![View]({{ badge_view_path }})]({{ project.preview_url }}){% else %}![not hosted]({{ badge_disabled_path }})<br><sub>not hosted yet</sub>{% endif %}</td>
<td align="right">[![Code]({{ badge_code_path }})]({{ project.repo_url }})</td>
</tr></table>

</td>
{% endfor %}
</tr>
{% endfor %}
</table>

<div align="center">

![Dimensional Stats header]({{ section_headers['Dimensional Stats'] }})

![Dimensional Stats]({{ dimensional_stats_svg_path }})

</div>

<div align="center">

![Quote]({{ quote_svg_path }})

</div>

<div align="center">

![Event Log header]({{ section_headers['Event Log'] }})

![Event Log]({{ event_log_svg_path }})

</div>

<div align="center">

![Fragmented Data header]({{ section_headers['Fragmented Data'] }})

</div>

<table>
{% for row in fragment_cards|batch(2) %}
<tr>
{% for project in row %}
<td align="center" width="360">

![{{ project.name }}]({{ project.card_svg_path }})

</td>
{% endfor %}
</tr>
{% endfor %}
</table>

<div align="center">

![Signal Uplink header]({{ section_headers['Signal Uplink'] }})

{% for link in social_links %}{% if link.url %}[![{{ link.label }}]({{ link.pill_svg_path }})]({{ link.url }}) {% else %}![{{ link.label }}]({{ link.pill_svg_path }}) {% endif %}{% endfor %}

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

<div align="center">

![Neural Activity header]({{ section_headers['Neural Activity'] }})

![Neural Activity]({{ neural_activity_svg_path }})

</div>

---

<sub>Last rendered: {{ build_time }} · theme: {{ theme }} · auto-generated, do not edit by hand</sub>
