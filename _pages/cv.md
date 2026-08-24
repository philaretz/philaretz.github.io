---
layout: archive
title: "CV / Resume"
permalink: /cv/
description: "Curriculum vitae of Philipp Aretz, including education, publications, talks, honours, teaching, and leadership activities."
author_profile: true
redirect_from:
  - /resume
---

{% include base_path %}

Education
======
* Ph.D. in Theoretical Physics, MIT, 2024-2029 (expected)
* MASt. in Mathematics (92% - Distinction Grade), University of Cambridge, 2023-24
* B.S. in Physics, Heidelberg University (1.0), 2020-23

Research Themes
======
* Effective field theory and precision QCD
* Heavy-ion collisions and medium effects at the LHC
* Mathematical methods for quantum field theory

Publications
=====
{% assign pubs_sorted = site.publications | sort: "date" | reverse %}
{% if pubs_sorted.size > 0 %}
<ul>
{% for pub in pubs_sorted %}
  <li><a href="{{ pub.url | relative_url }}">{{ pub.title }}</a>, {{ pub.venue }} ({{ pub.date | date: "%Y" }})</li>
{% endfor %}
</ul>
{% endif %}

Selected Talks
======
{% assign talks_sorted = site.talks | sort: "date" | reverse %}
{% if talks_sorted.size > 0 %}
<ul>
{% for talk in talks_sorted %}
  <li><a href="{{ talk.url | relative_url }}">{{ talk.title }}</a>, {{ talk.venue }} ({{ talk.date | date: "%b %Y" }})</li>
{% endfor %}
</ul>
{% else %}
Talk metadata is currently being curated; please see the [Contact page](/contact/) for recent presentation details.
{% endif %}

Honours
=====
* Tom Frank Fellowship at MIT, 2024-25
* Jennings Prize for academic performance in Part 3 of the mathematical tripos, 2024
* DAAD Scholarship, 2023-24
* Wolfson College Scholarship, 2023-24

Teaching
======
* Graduate TA for Classical Mechanics (8.01), MIT, 2025

Non-Academic Engagements
======
* President, MIT Rowing Club
* Organizer, MIT Graduate Student Seminar (2024-2025)
* Treasurer, Edgerton House (2025-2026)
* Mentor for first-year physics students, University of Heidelberg
