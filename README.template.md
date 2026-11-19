<div align="center">

![{{ username }} terminal]({{ terminal_svg_path_dark }}#gh-dark-mode-only)
![{{ username }} terminal]({{ terminal_svg_path_light }}#gh-light-mode-only)

<sub>~ live session · {{ username }}@github · re-renders every build ~</sub>

<br><br>

![Stats]({{ stats_strip_svg_path_dark }}#gh-dark-mode-only)
![Stats]({{ stats_strip_svg_path_light }}#gh-light-mode-only)

<br><br>

![System Modules]({{ skill_modules_svg_path_dark }}#gh-dark-mode-only)
![System Modules]({{ skill_modules_svg_path_light }}#gh-light-mode-only)

<br><br>

![Quote]({{ quote_svg_path }})

<br><br>

![LeetCode Stats]({{ leetcode_panel_svg_path_dark }}#gh-dark-mode-only)
![LeetCode Stats]({{ leetcode_panel_svg_path_light }}#gh-light-mode-only)

<br><br>

![Event Log]({{ event_log_svg_path_dark }}#gh-dark-mode-only)
![Event Log]({{ event_log_svg_path_light }}#gh-light-mode-only)

<br><br>

![Selected Work]({{ fragment_heading_svg_path_dark }}#gh-dark-mode-only)
![Selected Work]({{ fragment_heading_svg_path_light }}#gh-light-mode-only)

</div>

<br>

<table width="820" cellpadding="0" cellspacing="0" border="0">
{% for row in fragment_cards|batch(2) %}
<tr>
{% for project in row %}
<td align="{{ 'left' if loop.index0 == 0 else 'right' }}" valign="top">
<a href="{{ project.card_url }}"><img src="{{ project.card_svg_path }}" alt="{{ project.name }}" width="410"></a>
</td>
{% endfor %}
</tr>
{% endfor %}
</table>

<div align="center">

<br><br>

![Signal Uplink]({{ signal_heading_svg_path_dark }}#gh-dark-mode-only)
![Signal Uplink]({{ signal_heading_svg_path_light }}#gh-light-mode-only)

<table width="820" cellpadding="0" cellspacing="0" border="0"><tr><td align="left">
{% for link in social_links %}{% if link.url %}<a href="{{ link.url }}"><img src="{{ link.pill_svg_path }}" alt="{{ link.label }}"></a>&nbsp;{% else %}<img src="{{ link.pill_svg_path }}" alt="{{ link.label }}">&nbsp;{% endif %}{% endfor %}
</td></tr></table>

![Status]({{ signal_status_svg_path_dark }}#gh-dark-mode-only)
![Status]({{ signal_status_svg_path_light }}#gh-light-mode-only)

<br><br>

![Neural Activity]({{ activity_heading_svg_path_dark }}#gh-dark-mode-only)
![Neural Activity]({{ activity_heading_svg_path_light }}#gh-light-mode-only)

![Neural Activity]({{ neural_activity_svg_path_dark }}#gh-dark-mode-only)
![Neural Activity]({{ neural_activity_svg_path_light }}#gh-light-mode-only)

![Status]({{ activity_status_svg_path_dark }}#gh-dark-mode-only)
![Status]({{ activity_status_svg_path_light }}#gh-light-mode-only)

</div>

<sub>Last rendered: {{ build_time }} · theme: {{ theme }} · auto-generated, do not edit by hand</sub>
