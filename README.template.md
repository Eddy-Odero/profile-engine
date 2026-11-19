<div align="center">

{% macro pic(n, href) -%}
<a href="{{ href }}"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ hero.dark[n].path }}"><source media="(prefers-color-scheme: light)" srcset="{{ hero.light[n].path }}"><img align="top" src="{{ hero.light[n].path }}" width="{{ hero.dark[n].w }}" height="{{ hero.dark[n].h }}" alt="{{ username }}"></picture></a>
{%- endmacro %}
<a id="top"></a>
{{ pic('top', '#top') }}<br>
{{ pic('a', '#top') }}{{ pic('work', '#selected-work') }}{{ pic('gap', '#top') }}{{ pic('hello', '#signal-uplink') }}{{ pic('rest', '#top') }}<br>
{{ pic('bottom', '#top') }}

<sub>~ live session · {{ username }}@github · re-renders every build ~</sub>

<br><br>

<a id="s1"></a>
<a href="#s1"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ stats_strip_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ stats_strip_svg_path_light }}"><img src="{{ stats_strip_svg_path_light }}" alt="Stats"></picture></a>

<br><br>

<a id="s2"></a>
<a href="#s2"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ skill_modules_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ skill_modules_svg_path_light }}"><img src="{{ skill_modules_svg_path_light }}" alt="System Modules"></picture></a>

<br><br>

<a id="s3"></a>
<a href="#s3"><img src="{{ quote_svg_path }}" alt="Quote"></a>

<br><br>

<a id="s4"></a>
<a href="#s4"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ leetcode_panel_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ leetcode_panel_svg_path_light }}"><img src="{{ leetcode_panel_svg_path_light }}" alt="LeetCode Stats"></picture></a>

<br><br>

<a id="s5"></a>
<a href="#s5"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ event_log_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ event_log_svg_path_light }}"><img src="{{ event_log_svg_path_light }}" alt="Event Log"></picture></a>

<br><br>

<a id="selected-work"></a>
<a href="#selected-work"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ fragment_heading_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ fragment_heading_svg_path_light }}"><img src="{{ fragment_heading_svg_path_light }}" alt="Selected Work"></picture></a>

<br>

{% for row in fragment_cards|batch(2) %}{% for project in row %}<a href="{{ project.card_url }}"><img align="top" src="{{ project.card_svg_path }}" alt="{{ project.name }}" width="410"></a>{% endfor %}<br>
{% endfor %}


<br><br>

<a id="signal-uplink"></a>
<a href="#signal-uplink"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ signal_heading_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ signal_heading_svg_path_light }}"><img src="{{ signal_heading_svg_path_light }}" alt="Signal Uplink"></picture></a>

{% for link in social_links %}{% if link.url %}<a href="{{ link.url }}"><img align="top" src="{{ link.pill_svg_path }}" alt="{{ link.label }}"></a>{% else %}<img align="top" src="{{ link.pill_svg_path }}" alt="{{ link.label }}">{% endif %}{% endfor %}{% if pill_spacer_svg_path %}<img align="top" src="{{ pill_spacer_svg_path }}" alt="">{% endif %}

<a id="s6"></a>
<a href="#s6"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ signal_status_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ signal_status_svg_path_light }}"><img src="{{ signal_status_svg_path_light }}" alt="Status"></picture></a>

<br><br>

<a id="s7"></a>
<a href="#s7"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ activity_heading_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ activity_heading_svg_path_light }}"><img src="{{ activity_heading_svg_path_light }}" alt="Neural Activity"></picture></a>

<a id="s8"></a>
<a href="#s8"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ neural_activity_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ neural_activity_svg_path_light }}"><img src="{{ neural_activity_svg_path_light }}" alt="Neural Activity"></picture></a>

<a href="{{ city_page_url }}"><img align="top" src="{{ cta_city_svg_path }}" alt="Open interactive city" width="250"></a><img align="top" src="{{ city_note_svg_path }}" alt="">

<a id="s9"></a>
<a href="#s9"><picture><source media="(prefers-color-scheme: dark)" srcset="{{ activity_status_svg_path_dark }}"><source media="(prefers-color-scheme: light)" srcset="{{ activity_status_svg_path_light }}"><img src="{{ activity_status_svg_path_light }}" alt="Status"></picture></a>

</div>

<sub>Last rendered: {{ build_time }} · theme: {{ theme }} · auto-generated, do not edit by hand</sub>
