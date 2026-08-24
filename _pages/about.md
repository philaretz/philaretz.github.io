---
permalink: /
title: "About"
layout: bespoke
redirect_from:
  - /about/
  - /about.html
---

<section class="hero">
  <div class="avatar"><img src="/images/bio-avatar.jpg" alt="{{ site.author.name }}"></div>
  <div class="hero-text">
    <h1>{{ site.author.name }}</h1>
    <p class="affiliation">PhD Student in Theoretical High-Energy Physics<br>{{ site.author.employer }} Center for Theoretical Physics</p>
    <p class="bio">I am Philipp Aretz, a PhD student in theoretical high-energy physics at MIT. My research combines effective field theory, precision QCD, and heavy-ion physics to better understand how fundamental interactions emerge in high-energy collisions.</p>
    <p class="interests">Effective field theory &middot; Precision QCD &middot; Heavy-ion collisions</p>
    <div class="link-row">
      <a href="mailto:{{ site.author.email }}">Email</a><span class="dot">&middot;</span>
      {% if site.author.arxiv %}<a href="{{ site.author.arxiv }}">arXiv</a><span class="dot">&middot;</span>{% endif %}
      {% if site.author.googlescholar %}<a href="{{ site.author.googlescholar }}">Google Scholar</a><span class="dot">&middot;</span>{% endif %}
      {% if site.author.orcid %}<a href="{{ site.author.orcid }}">ORCID</a><span class="dot">&middot;</span>{% endif %}
      {% if site.author.inspire-hep %}<a href="{{ site.author.inspire-hep }}">INSPIRE-HEP</a><span class="dot">&middot;</span>{% endif %}
      {% if site.author.github %}<a href="https://github.com/{{ site.author.github }}">GitHub</a>{% endif %}
      {% if site.author.linkedin %}<span class="dot">&middot;</span><a href="https://www.linkedin.com/in/{{ site.author.linkedin }}">LinkedIn</a>{% endif %}
    </div>
  </div>
</section>

<section class="section" style="margin-top: 0;">
  <h2 class="section-label">Current Projects</h2>
  <div class="projects-grid">
    <div class="project">
      <span class="status">Ongoing</span>
      <h3>Effective field theory for precision collider observables</h3>
      <p>Developing EFT/SCET-based methods to sharpen predictions at the precision frontier of collider physics.</p>
    </div>
    <div class="project">
      <span class="status">Ongoing</span>
      <h3>Medium effects &amp; jet modification in heavy-ion collisions</h3>
      <p>Studying how the QGP medium reshapes jets and detector-level observables in heavy-ion collisions at the LHC.</p>
    </div>
  </div>
</section>

<section class="section">
  <h2 class="section-label">Selected Publications</h2>
  {% assign recent_pubs = site.publications | sort: "date" | reverse %}
  <ul class="mini-list">
  {% for post in recent_pubs limit: 2 %}
    {% assign entry_date = post.date | date: "%Y" %}
    {% include bespoke/mini-entry.html url=post.url date=entry_date title=post.title venue=post.venue %}
  {% endfor %}
  </ul>
  <a href="/publications/" class="see-all">View all publications &rarr;</a>
</section>

<section class="section">
  <h2 class="section-label">Selected Talks</h2>
  {% assign recent_talks = site.talks | sort: "date" | reverse %}
  {% if recent_talks.size > 0 %}
  <ul class="mini-list">
  {% for post in recent_talks limit: 2 %}
    {% assign entry_date = post.date | date: "%b '%y" %}
    {% include bespoke/mini-entry.html url=post.url date=entry_date title=post.title venue=post.venue %}
  {% endfor %}
  </ul>
  <a href="/talks/" class="see-all">View all talks &rarr;</a>
  {% else %}
  Recent talks will be posted here soon.
  {% endif %}
</section>
