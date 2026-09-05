---
layout: bespoke
title: "CV / Resume"
permalink: /cv/
description: "Curriculum vitae of Philipp Aretz, including education, publications, talks, honours, teaching, and leadership activities."
redirect_from:
  - /resume
---

<div class="cv-header">
  <h1>{{ site.author.name }}</h1>
  <p class="cv-role">PhD Student in Theoretical High-Energy Physics &middot; {{ site.author.employer }} Center for Theoretical Physics</p>
  <p class="cv-contact">{% include bespoke/email-link.html id="cv-email" class="cv-email-link" %} &middot; <a href="/files/cv.pdf">Download CV (PDF)</a> &middot; <a href="/files/resume.pdf">R&eacute;sum&eacute; (PDF)</a></p>
</div>

{% for section in site.data.cv.sections %}
  {% include bespoke/cv-section.html section=section %}
{% endfor %}
