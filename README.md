# Sambhota Tibetan Schools Society (STSS) Teachers' Teaching Repository & Maths Hub
### སམ་བྷོ་ཊ་བོད་སློབ་ཚོགས་པའི་དགེ་རྒན་གྱི་སློབ་ཁྲིད་མཐུན་རྐྱེན་མཛོད་ཁང་།

An integrated digital repository for educators across the **Sambhota Tibetan Schools Society (STSS)** network in India, integrating the full feature requirements of the **STSS Maths Hub Product Requirements Document (PRD v1.1)** while preserving the base UI and traditional aesthetic.

---

## 🌟 Key Features (STSS Repository + Maths Hub PRD v1.1)

1. **Curriculum-Aligned Categorization & Maths Hub**:
   - **Mathematics Focus**: Includes CBSE/NCERT curriculum packages (Quadratic Equations, Applications of Trigonometry, Experimental Probability, Visual Fractions & Decimals, Differential Calculus).
   - **Full Subject Coverage**: Tibetan Language & Literature (བོད་ཡིག), Science (ཚན་རིག), Social Science & Tibetan History (སྤྱི་ཚོགས), English, Hindi (ཧིན་དྷི), and SEE Learning / Dialectics (བཟང་སྤྱོད་ཤེས་ཡོན).
   - **Education Stages**: Pre-Primary (Montessori/KG), Primary (Classes 1–5), Middle School (Classes 6–8), Secondary (Classes 9–10), and Senior Secondary (Classes 11–12).

2. **Persona Management & Role-Based Access (Module A & F)**:
   - Built-in persona simulator in the header:
     - **Tashi** (Mathematics Teacher, Consumer, STSS Chauntra)
     - **Dolma** (Senior Mathematics Teacher, Contributor, STSS Paonta Sahib)
     - **Tenzin** (Content & Quality Moderator, CTA DoE)
     - **Lhamo** (School Administrator / Admin, STSS Central Council)

3. **Ratings & Peer Review Comments (Module E)**:
   - **1–5 Star Rating System**: Real-time average rating calculation, rating counts, editable user ratings.
   - **Peer Reviews**: Interactive discussion and commentary thread for teachers to exchange pedagogy, adaptations, and constructive feedback.
   - **Engagement Metrics**: Live views counter (`views_count`), download tracker, and appreciation likes.

4. **Teaching Notes & Pedagogical Strategy (Module B & D)**:
   - Dedicated highlight box for pedagogical advice, common student misconceptions, suggested manipulatives (e.g. algebra tiles, fraction kits), and pacing tips.

5. **Favorites & Bookmarks (Module H)**:
   - Dedicated "Favorites & Saved" tab for teachers to bookmark frequently used lesson plans and worksheets for fast access.

6. **Content Moderation & Copyright Gate (Module K - Phase 1 MVP)**:
   - **Mandatory Copyright Confirmation**: Explicit ownership/rights checkbox required on all uploads.
   - **Moderation Queue Tab**: Resources enter `Pending Review` status; moderators can inspect, approve, or reject with feedback reasons.
   - **12-Month Audit Trail**: Complete log of moderation decisions and flagged content.
   - **Takedown / Flag Mechanism**: Teachers can flag any live resource for copyright or quality review.

7. **Instant Search & Deep Filtering**:
   - Search across topics, keywords, grammar chapters, tags, and teacher names.
   - Filter by Stage, Class, Subject, Minimum Star Rating (★ 4.8+, ★ 4.5+, ★ 4.0+, ★ 3.5+), Medium, and School.

8. **Zero External Dependencies**:
   - Runs out-of-the-box on Python 3 standard library (`http.server`, `sqlite3`, `email.parser`).

---

## 📂 Project Architecture

```
stss-teaching-repository/
├── server.py                            # REST API server, multipart uploads, ratings, comments, moderation
├── database.py                          # SQLite schema, PRD Maths Hub seed data, users & audit log
├── run.sh                               # One-click startup script
├── static/
│   ├── css/
│   │   └── style.css                    # Traditional Tibetan maroon & gold design, preserving base UI
│   ├── js/
│   │   └── app.js                       # Client SPA logic (ratings, reviews, favorites, moderation queue)
│   └── index.html                       # Responsive web portal UI
├── templates/                           # Standardized STSS templates
│   ├── lesson-plan-template-tibetan.md
│   ├── lesson-plan-template-english.md
│   ├── see-learning-lesson-plan.md
│   └── assessment-rubric-template.md
├── data/
│   ├── sample_resources/                # Seeded Mathematics & Tibetan curriculum resources
│   └── stss_repository.db               # SQLite database
├── uploads/                             # Destination for teacher-uploaded files
└── README.md                            # Documentation
```

---

## 🚀 Quick Start Guide

In your terminal:

```bash
cd /Users/dharma/.gemini/antigravity/scratch/stss-teaching-repository
./run.sh
```

Or run directly with Python:
```bash
python3 server.py 8080
```

Then visit **[http://localhost:8080](http://localhost:8080)**.
