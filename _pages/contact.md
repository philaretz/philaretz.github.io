---
title: "Contact"
permalink: /contact/
description: "Contact details for Philipp Aretz at MIT, including email and office location."
layout: bespoke
---

<section class="page-head">
  <h1>Contact</h1>
</section>

<p class="contact-lead">I welcome messages about research, collaborations, and academic opportunities — including a short context note helps me respond quickly.</p>

<a href="mailto:{{ site.data.contact.email_obfuscated }}" class="contact-email">{{ site.data.contact.email_obfuscated_mdtext }}</a>
<p class="contact-affil">{{ site.author.employer }} Center for Theoretical Physics<br>Office: <a href="http://whereis.mit.edu/?go=6-413">MIT, Room 6-413</a><br>{{ site.author.location }}</p>

<h2 class="section-label">Elsewhere</h2>
<div class="link-row">
  {% if site.author.arxiv %}<a href="{{ site.author.arxiv }}">arXiv</a><span class="dot">&middot;</span>{% endif %}
  {% if site.author.googlescholar %}<a href="{{ site.author.googlescholar }}">Google Scholar</a><span class="dot">&middot;</span>{% endif %}
  {% if site.author.orcid %}<a href="{{ site.author.orcid }}">ORCID</a><span class="dot">&middot;</span>{% endif %}
  {% if site.author.inspire-hep %}<a href="{{ site.author.inspire-hep }}">INSPIRE-HEP</a><span class="dot">&middot;</span>{% endif %}
  {% if site.author.github %}<a href="https://github.com/{{ site.author.github }}">GitHub</a>{% endif %}
  {% if site.author.linkedin %}<span class="dot">&middot;</span><a href="https://www.linkedin.com/in/{{ site.author.linkedin }}">LinkedIn</a>{% endif %}
</div>
