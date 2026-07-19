<div align="center">

```
{{ avatar_ascii }}
```

```
{{ boot_sequence }}
{{ system_message }}
```

</div>

<div align="center">

# {{ username }}

**Status:** `{{ status }}` {{ cursor }}

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

---

<div align="center">

**Today's Quote**

> {{ quote }}

</div>

---

<sub>Last rendered: {{ build_time }} · auto-generated, do not edit by hand</sub>
