<div align="center">

<img src="{{ terminal_svg_path_dark }}#gh-dark-mode-only" alt="{{ username }} terminal">
<img src="{{ terminal_svg_path_light }}#gh-light-mode-only" alt="{{ username }} terminal">

<table align="center" width="820" cellpadding="0" cellspacing="0" border="0"><tr><td align="left">
<a href="#selected-work"><img src="{{ cta_work_svg_path }}" alt="See my work" width="170"></a>&nbsp;&nbsp;<a href="#signal-uplink"><img src="{{ cta_hello_svg_path }}" alt="Say hello" width="170"></a>
</td></tr></table>

<sub>~ live session · {{ username }}@github · re-renders every build ~</sub>

<br><br>

<img src="{{ stats_strip_svg_path_dark }}#gh-dark-mode-only" alt="Stats">
<img src="{{ stats_strip_svg_path_light }}#gh-light-mode-only" alt="Stats">

<br><br>

<img src="{{ skill_modules_svg_path_dark }}#gh-dark-mode-only" alt="System Modules">
<img src="{{ skill_modules_svg_path_light }}#gh-light-mode-only" alt="System Modules">

<br><br>

<img src="{{ quote_svg_path }}" alt="Quote">

<br><br>

<img src="{{ leetcode_panel_svg_path_dark }}#gh-dark-mode-only" alt="LeetCode Stats">
<img src="{{ leetcode_panel_svg_path_light }}#gh-light-mode-only" alt="LeetCode Stats">

<br><br>

<img src="{{ event_log_svg_path_dark }}#gh-dark-mode-only" alt="Event Log">
<img src="{{ event_log_svg_path_light }}#gh-light-mode-only" alt="Event Log">

<br><br>

<a id="selected-work"></a>
<img src="{{ fragment_heading_svg_path_dark }}#gh-dark-mode-only" alt="Selected Work">
<img src="{{ fragment_heading_svg_path_light }}#gh-light-mode-only" alt="Selected Work">

</div>

<br>

<table align="center" width="820" cellpadding="0" cellspacing="0" border="0">
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

<a id="signal-uplink"></a>
<img src="{{ signal_heading_svg_path_dark }}#gh-dark-mode-only" alt="Signal Uplink">
<img src="{{ signal_heading_svg_path_light }}#gh-light-mode-only" alt="Signal Uplink">

<table align="center" width="820" cellpadding="0" cellspacing="0" border="0"><tr><td align="left">
{% for link in social_links %}{% if link.url %}<a href="{{ link.url }}"><img src="{{ link.pill_svg_path }}" alt="{{ link.label }}"></a>&nbsp;{% else %}<img src="{{ link.pill_svg_path }}" alt="{{ link.label }}">&nbsp;{% endif %}{% endfor %}
</td></tr></table>

<img src="{{ signal_status_svg_path_dark }}#gh-dark-mode-only" alt="Status">
<img src="{{ signal_status_svg_path_light }}#gh-light-mode-only" alt="Status">

<br><br>

<img src="{{ activity_heading_svg_path_dark }}#gh-dark-mode-only" alt="Neural Activity">
<img src="{{ activity_heading_svg_path_light }}#gh-light-mode-only" alt="Neural Activity">

<img src="{{ neural_activity_svg_path_dark }}#gh-dark-mode-only" alt="Neural Activity">
<img src="{{ neural_activity_svg_path_light }}#gh-light-mode-only" alt="Neural Activity">

<img src="{{ activity_status_svg_path_dark }}#gh-dark-mode-only" alt="Status">
<img src="{{ activity_status_svg_path_light }}#gh-light-mode-only" alt="Status">

</div>

<sub>Last rendered: {{ build_time }} · theme: {{ theme }} · auto-generated, do not edit by hand</sub>
