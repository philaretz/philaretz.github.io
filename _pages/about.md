---
permalink: /
title: "About"
description: "I am a PhD student at MIT working on theoretical high-energy physics, effective field theory, precision QCD, and heavy-ion collisions."
author_profile: true
redirect_from:
  - /about/
  - /about.html
---

I am Philipp Aretz, a PhD student in theoretical high-energy physics at MIT.

My research combines effective field theory, precision QCD, and heavy-ion physics to better understand how fundamental interactions emerge in high-energy collisions.

## Research in plain language

I build mathematical tools that help turn collider data into reliable physical insight. In practice, this means improving how we connect what detectors measure to the underlying dynamics of quarks and gluons, and making those predictions more robust for both precision tests and new-physics searches.

## Current projects

- Effective field theory methods for precision collider observables <span class="status-pill status-pill--ongoing">ongoing</span>
- Medium effects and jet modification in heavy-ion collisions <span class="status-pill status-pill--ongoing">ongoing</span>

## Selected publications

- [A rigorous Keldysh functional integral for fermions](/publication/Keldysh)
- [Families of periodic delay orbits](/publication/Periodic)

## Selected talks

{% assign recent_talks = site.talks | sort: "date" | reverse %}
{% if recent_talks.size > 0 %}
<ul class="selected-talks">
{% for talk in recent_talks limit: 4 %}
  <li><a href="{{ talk.url | relative_url }}">{{ talk.title }}</a> — {{ talk.venue }}, {{ talk.date | date: "%Y" }}</li>
{% endfor %}
</ul>
{% else %}
Recent talks will be posted here soon.
{% endif %}
