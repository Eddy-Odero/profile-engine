<div align="center">

![{{ username }} terminal]({{ terminal_svg_path }})

<sub>~ live session · {{ username }}@github · re-renders every build ~</sub>

{{ stat_badges | join(" ") }}

![System Modules header]({{ section_headers['System Modules'] }})

![System Modules]({{ skill_modules_svg_path }})

![Dimensional Stats header]({{ section_headers['Dimensional Stats'] }})

![Dimensional Stats]({{ dimensional_stats_svg_path }})

![Quote]({{ quote_svg_path }})

![LeetCode Stats header]({{ section_headers['LeetCode Stats'] }})

![LeetCode Stats]({{ leetcode_panel_svg_path }})

![Event Log header]({{ section_headers['Event Log'] }})

![Event Log]({{ event_log_svg_path }})

![Fragmented Data header]({{ section_headers['Fragmented Data'] }})

</div>

<table cellpadding="2" cellspacing="2" border="0">
{% for row in fragment_cards|batch(2) %}
<tr>
{% for project in row %}
<td align="center">

![{{ project.name }}]({{ project.card_svg_path }})

</td>
{% endfor %}
</tr>
{% endfor %}
</table>

<div align="center">

![Signal Uplink header]({{ section_headers['Signal Uplink'] }})

{% for link in social_links %}{% if link.url %}[![{{ link.label }}]({{ link.pill_svg_path }})]({{ link.url }}) {% else %}![{{ link.label }}]({{ link.pill_svg_path }}) {% endif %}{% endfor %}

![Neural Activity header]({{ section_headers['Neural Activity'] }})

![Neural Activity]({{ neural_activity_svg_path }})

</div>

<sub>Last rendered: {{ build_time }} · theme: {{ theme }} · auto-generated, do not edit by hand</sub>
