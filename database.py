import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "stss_repository.db"

def get_connection():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Resources table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        title_en TEXT,
        subject TEXT NOT NULL,
        grade_level TEXT NOT NULL,
        grade_category TEXT NOT NULL,
        chapter_topic TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        medium_language TEXT NOT NULL,
        description TEXT,
        teaching_notes TEXT,
        content_text TEXT,
        file_name TEXT,
        file_path TEXT,
        file_type TEXT,
        file_size_kb INTEGER DEFAULT 0,
        author_name TEXT NOT NULL,
        author_role TEXT,
        school_name TEXT NOT NULL,
        curriculum_alignment TEXT DEFAULT 'STSS / CTA DoE & CBSE',
        tags TEXT,
        downloads_count INTEGER DEFAULT 0,
        likes_count INTEGER DEFAULT 0,
        views_count INTEGER DEFAULT 0,
        rating_avg REAL DEFAULT 5.0,
        rating_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Published',
        rejection_reason TEXT,
        copyright_confirmed INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Alter table if existing database is missing PRD columns
    cursor.execute("PRAGMA table_info(resources)")
    columns = [row["name"] for row in cursor.fetchall()]
    
    new_cols = [
        ("teaching_notes", "TEXT"),
        ("views_count", "INTEGER DEFAULT 0"),
        ("rating_avg", "REAL DEFAULT 5.0"),
        ("rating_count", "INTEGER DEFAULT 0"),
        ("status", "TEXT DEFAULT 'Published'"),
        ("rejection_reason", "TEXT"),
        ("copyright_confirmed", "INTEGER DEFAULT 1")
    ]
    for col_name, col_type in new_cols:
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE resources ADD COLUMN {col_name} {col_type}")

    # Schools directory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        state TEXT,
        settlement TEXT,
        level TEXT,
        established INTEGER
    );
    """)

    # Users table (PRD Persona Management & SSO Simulation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        school TEXT NOT NULL,
        specialization TEXT,
        photo TEXT,
        joined_date TEXT
    );
    """)

    # Ratings table (Module E: 1-5 Stars, one per teacher, editable)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        rating INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(resource_id, user_name),
        FOREIGN KEY(resource_id) REFERENCES resources(id)
    );
    """)

    # Comments / Reviews table (Module E)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        user_school TEXT,
        user_role TEXT,
        comment_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(resource_id) REFERENCES resources(id)
    );
    """)

    # Favorites table (Module H)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        resource_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_name, resource_id),
        FOREIGN KEY(resource_id) REFERENCES resources(id)
    );
    """)

    # Moderation & Copyright Audit Log (Module K)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS moderation_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER NOT NULL,
        moderator_name TEXT NOT NULL,
        action TEXT NOT NULL,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Lesson plan templates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        title_tibetan TEXT,
        description TEXT,
        category TEXT,
        content TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def seed_sample_data():
    conn = get_connection()
    cursor = conn.cursor()

    # Clean up any legacy placeholder users
    cursor.execute("DELETE FROM users WHERE name IN ('Sarah Lim', 'Jason Wong', 'Tenzin Norbu', 'Principal Ahmad')")

    # Seed PRD User Personas with Authentic Tibetan Names
    users = [
        ("Dolma", "Teacher", "STSS Paonta Sahib", "Senior Mathematics Teacher", "female_teacher.png", "2021-04-15"),
        ("Tashi", "Teacher", "STSS Chauntra", "Mathematics Teacher", "male_teacher.png", "2023-08-01"),
        ("Tenzin", "Moderator", "STSS Dharamshala (Petoen)", "Curriculum Quality & Copyright Moderator", "moderator.png", "2019-02-10"),
        ("Lhamo", "Admin", "STSS Central Education Council", "School Administrator", "admin.png", "2017-06-20")
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO users (name, role, school, specialization, photo, joined_date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, users)

    # Migrate any previous placeholder names in resources, ratings, comments, favorites, audit
    cursor.execute("UPDATE resources SET author_name = 'Dolma' WHERE author_name = 'Sarah Lim'")
    cursor.execute("UPDATE resources SET author_name = 'Tashi' WHERE author_name = 'Jason Wong'")
    cursor.execute("UPDATE resources SET author_name = 'Tenzin' WHERE author_name = 'Tenzin Norbu'")
    cursor.execute("UPDATE resources SET author_name = 'Lhamo' WHERE author_name = 'Principal Ahmad'")

    cursor.execute("UPDATE resources SET content_text = REPLACE(content_text, 'Sarah Lim', 'Dolma')")
    cursor.execute("UPDATE resources SET content_text = REPLACE(content_text, 'Jason Wong', 'Tashi')")
    cursor.execute("UPDATE resources SET content_text = REPLACE(content_text, 'Principal Ahmad', 'Lhamo')")

    cursor.execute("UPDATE ratings SET user_name = 'Dolma' WHERE user_name = 'Sarah Lim'")
    cursor.execute("UPDATE ratings SET user_name = 'Tashi' WHERE user_name = 'Jason Wong'")

    cursor.execute("UPDATE comments SET user_name = 'Dolma' WHERE user_name = 'Sarah Lim'")
    cursor.execute("UPDATE comments SET user_name = 'Tashi' WHERE user_name = 'Jason Wong'")

    cursor.execute("UPDATE favorites SET user_name = 'Dolma' WHERE user_name = 'Sarah Lim'")
    cursor.execute("UPDATE favorites SET user_name = 'Tashi' WHERE user_name = 'Jason Wong'")

    cursor.execute("UPDATE moderation_audit SET moderator_name = 'Tenzin' WHERE moderator_name IN ('Tenzin Norbu', 'Admin')")

    # Seed STSS Schools
    schools = [
        ("STSS Paonta Sahib", "Himachal Pradesh", "Paonta Cholsum", "Senior Secondary", 1978),
        ("STSS Chauntra", "Himachal Pradesh", "Bir Chauntra", "Senior Secondary", 1980),
        ("STSS Bylakuppe", "Karnataka", "Lugsung Samdupling", "Senior Secondary", 1972),
        ("STSS Mundgod", "Karnataka", "Doeguling", "Senior Secondary", 1975),
        ("STSS Herbertpur", "Uttarakhand", "Dehradun Valley", "Secondary", 1982),
        ("STSS Mussoorie", "Uttarakhand", "Happy Valley", "Senior Secondary", 1960),
        ("STSS Shimla", "Himachal Pradesh", "Chhota Shimla", "Senior Secondary", 1962),
        ("STSS Dalhousie", "Himachal Pradesh", "Dalhousie", "Senior Secondary", 1963),
        ("STSS Miao (Choepheling)", "Arunachal Pradesh", "Miao", "Middle School", 1985),
        ("STSS Tezu (Dhargyeling)", "Arunachal Pradesh", "Tezu", "Secondary", 1986),
        ("STSS Dekyiling", "Uttarakhand", "Dehradun", "Middle School", 1990),
        ("STSS Kollegal", "Karnataka", "Dhondenling", "Secondary", 1974),
        ("STSS Hunsur", "Karnataka", "Rabgayling", "Secondary", 1976),
        ("STSS Mainpat", "Chhattisgarh", "Phendeling", "Secondary", 1965),
        ("STSS Chandragiri", "Odisha", "Phuntsokling", "Secondary", 1968),
        ("STSS Dharamshala (Petoen)", "Himachal Pradesh", "Gangchen Kyishong", "Model School", 2005)
    ]
    cursor.executemany("INSERT OR IGNORE INTO schools (name, state, settlement, level, established) VALUES (?, ?, ?, ?, ?)", schools)

    # Specific PRD Maths Hub Resources
    math_resources = [
        {
            "title": "Quadratic Equations: Factorisation, Quadratic Formula & Real-World Modeling",
            "title_en": "Complete Chapter Teaching Package for Class 10 CBSE & STSS Mathematics",
            "subject": "Mathematics",
            "grade_level": "Class 10",
            "grade_category": "Secondary (9-10)",
            "chapter_topic": "Chapter 4: Quadratic Equations (འགྱུར་ལྡོག་གཉིས་ལྡན་མཉམ་རྩིས)",
            "resource_type": "Lesson Plan",
            "medium_language": "English",
            "description": "Comprehensive teaching package on Quadratic Equations covering discriminant nature of roots, step-by-step factorization techniques, completing the square, and real-life speed/time and projectile word problems.",
            "teaching_notes": "Recommended approach: Start with the geometric proof of completing the square using physical square tiles before introducing the algebraic formula x = (-b ± √(b² - 4ac)) / (2a). Watch out for negative sign errors when b is negative.",
            "content_text": """# Class 10 Mathematics: Quadratic Equations
## STSS Central Maths Hub Curriculum Package
### Author: Dolma (Senior Mathematics Teacher, STSS Paonta Sahib)

---
### 1. Conceptual Framework & Syllabus Targets
- Standard Form of Quadratic Equation: $ax^2 + bx + c = 0$, where $a \\neq 0$.
- Roots of quadratic equations by factorization method.
- Solution by completing the square method.
- Quadratic Formula: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$.
- Nature of Roots based on Discriminant $D = b^2 - 4ac$:
  - $D > 0$: Two distinct real roots.
  - $D = 0$: Two equal real roots.
  - $D < 0$: No real roots.

---
### 2. Differentiated Classroom Activity (35 Mins)
1. **Direct Modeling (10 mins):** Solve $2x^2 - 7x + 3 = 0$ using splitting middle term:
   - Product = $2 \\times 3 = 6$, Sum = $-7$. Factors are $-6$ and $-1$.
   - $2x(x - 3) - 1(x - 3) = 0 \\implies x = 3, \\frac{1}{2}$.
2. **Real-World Word Problem Modeling (15 mins):**
   - A motorboat whose speed is 18 km/h in still water takes 1 hour more to go 24 km upstream than to return downstream to the same spot. Find speed of the stream.
3. **Exit Ticket & Diagnostic Check (10 mins):**
   - Determine the nature of roots for $3x^2 - 4\\sqrt{3}x + 4 = 0$.

---
### 3. Tibetan Terminology Reference for STSS Teachers
- Quadratic Equation: འགྱུར་ལྡོག་གཉིས་ལྡན་མཉམ་རྩིས།
- Discriminant: དབྱེ་འབྱེད་གྲངས།
- Roots / Solutions: མཉམ་རྩིས་ཀྱི་རྩ་བ།
- Factorization: བགོ་འགྲེམས་བཤིག་སྒྲིལ།
""",
            "file_name": "math-class10-quadratic-equations.md",
            "file_path": "data/sample_resources/math-class10-quadratic-equations.md",
            "file_type": "md",
            "file_size_kb": 28,
            "author_name": "Dolma",
            "author_role": "Senior Mathematics Teacher",
            "school_name": "STSS Paonta Sahib",
            "curriculum_alignment": "CBSE Class 10 & STSS Maths Hub Framework",
            "tags": "Quadratic Equations, Factorization, Discriminant, Word Problems, Class 10",
            "downloads_count": 420,
            "likes_count": 135,
            "views_count": 1280,
            "rating_avg": 4.9,
            "rating_count": 24,
            "status": "Published",
            "copyright_confirmed": 1
        },
        {
            "title": "Trigonometry & Heights and Distances: Step-by-Step Visualization Guide",
            "title_en": "Applications of Trigonometry with Tibetan Settlement Landscape Problems",
            "subject": "Mathematics",
            "grade_level": "Class 10",
            "grade_category": "Secondary (9-10)",
            "chapter_topic": "Chapter 9: Some Applications of Trigonometry (ཟུར་གསུམ་རྩིས་རིག)",
            "resource_type": "Worksheet",
            "medium_language": "English",
            "description": "Scaffolded worksheet breaking down angles of elevation and depression with visual line-of-sight diagrams. Contextualized with Tibetan settlement architectural heights (prayer flag poles, monastery stupas, water towers).",
            "teaching_notes": "Crucial pedagogical pointer: Emphasize that the observer's eye height must be subtracted from the total structure height if given in the problem statement. Ensure students always draw the triangle first before writing trigonometric ratios.",
            "content_text": """# Applications of Trigonometry: Heights & Distances
## Class 10 Practice Worksheet & Diagnostic Guide
### STSS Chauntra | Author: Dolma & Tashi

---
### Key Formulae & Reference:
$$\\tan \\theta = \\frac{\\text{Opposite}}{\\text{Adjacent}}, \\quad \\sin \\theta = \\frac{\\text{Opposite}}{\\text{Hypotenuse}}, \\quad \\cos \\theta = \\frac{\\text{Adjacent}}{\\text{Hypotenuse}}$$
Common Values:
- $\\tan 30^\\circ = \\frac{1}{\\sqrt{3}}$, $\\tan 45^\\circ = 1$, $\\tan 60^\\circ = \\sqrt{3}$

---
### Practice Exercises:
1. An observer 1.5 m tall stands 28.5 m away from a Tibetan chorten (stupa). The angle of elevation of the top of the chorten from her eye is $45^\\circ$. What is the height of the chorten?
2. A flagpole stands on top of an 8 m high school building. From a point on the ground, the angle of elevation of the top of the flagpole is $60^\\circ$ and that of the top of the building is $45^\\circ$. Find the height of the flagpole.
""",
            "file_name": "math-class10-trigonometry-heights.md",
            "file_path": "data/sample_resources/math-class10-trigonometry-heights.md",
            "file_type": "md",
            "file_size_kb": 22,
            "author_name": "Dolma",
            "author_role": "Senior Mathematics Teacher",
            "school_name": "STSS Paonta Sahib",
            "curriculum_alignment": "CBSE Class 10 Mathematics",
            "tags": "Trigonometry, Heights and Distances, Angle of Elevation, Class 10",
            "downloads_count": 310,
            "likes_count": 89,
            "views_count": 940,
            "rating_avg": 4.8,
            "rating_count": 18,
            "status": "Published",
            "copyright_confirmed": 1
        },
        {
            "title": "Probability & Statistics: Experimental Trials & Data Frequency Tables",
            "title_en": "Middle & Secondary Interactive Probability Laboratory Activity",
            "subject": "Mathematics",
            "grade_level": "Class 9",
            "grade_category": "Secondary (9-10)",
            "chapter_topic": "Chapter 15: Probability (སྲིད་པའི་རྩིས་རིག)",
            "resource_type": "Worksheet",
            "medium_language": "English",
            "description": "Engaging hands-on classroom lab where students perform 50 coin tosses, two-dice sums, and analyze weather data across Tibetan settlements to bridge empirical and theoretical probability.",
            "teaching_notes": "Divide students into teams of 4. Have two students record frequencies on the blackboard while two conduct the physical experiments. Debrief on the Law of Large Numbers.",
            "content_text": """# Class 9 Mathematics: Experimental vs Theoretical Probability
### Author: Tashi (TGT Mathematics, STSS Chauntra)

---
### Empirical Formula:
$$P(E) = \\frac{\\text{Number of trials in which the event happened}}{\\text{Total number of trials}}$$
""",
            "file_name": "math-class9-probability-lab.md",
            "file_path": "data/sample_resources/math-class9-probability-lab.md",
            "file_type": "md",
            "file_size_kb": 19,
            "author_name": "Tashi",
            "author_role": "TGT Mathematics",
            "school_name": "STSS Chauntra",
            "curriculum_alignment": "NCERT Class 9 Mathematics",
            "tags": "Probability, Statistics, Empirical, Dice Experiments, Class 9",
            "downloads_count": 185,
            "likes_count": 62,
            "views_count": 620,
            "rating_avg": 4.7,
            "rating_count": 12,
            "status": "Published",
            "copyright_confirmed": 1
        },
        {
            "title": "Calculus: Limits & Continuity Comprehensive Problem Set (CBSE Class 12)",
            "title_en": "Senior Secondary Mathematics Differential Calculus Problem Set",
            "subject": "Mathematics",
            "grade_level": "Class 12",
            "grade_category": "Senior Secondary (11-12)",
            "chapter_topic": "Chapter 5: Continuity and Differentiability",
            "resource_type": "Assessment / Exam",
            "medium_language": "English",
            "description": "Rigorous 50-mark diagnostic exam for Class 12 CBSE board candidates covering epsilon-delta conceptual grounding, L'Hopital's rule, and piecewise continuous functions.",
            "teaching_notes": "Includes complete step-by-step marking scheme and common pitfalls analysis.",
            "content_text": """# Class 12 Mathematics: Continuity & Differentiability
## Senior Secondary Diagnostic Assessment Paper
### Max Marks: 50 | Time: 2 Hours
""",
            "file_name": "math-class12-calculus-limits.md",
            "file_path": "data/sample_resources/math-class12-calculus-limits.md",
            "file_type": "md",
            "file_size_kb": 26,
            "author_name": "Dolma",
            "author_role": "Senior Mathematics Teacher",
            "school_name": "STSS Paonta Sahib",
            "curriculum_alignment": "CBSE Class 12 Mathematics",
            "tags": "Calculus, Limits, Continuity, Class 12, Senior Secondary",
            "downloads_count": 15,
            "likes_count": 4,
            "views_count": 45,
            "rating_avg": 5.0,
            "rating_count": 2,
            "status": "Pending Review",
            "copyright_confirmed": 1
        }
    ]

    for item in math_resources:
        cursor.execute("SELECT id FROM resources WHERE title = ?", (item["title"],))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute("""
            INSERT INTO resources (
                title, title_en, subject, grade_level, grade_category, chapter_topic,
                resource_type, medium_language, description, teaching_notes, content_text,
                file_name, file_path, file_type, file_size_kb, author_name, author_role,
                school_name, curriculum_alignment, tags, downloads_count, likes_count,
                views_count, rating_avg, rating_count, status, copyright_confirmed
            ) VALUES (
                :title, :title_en, :subject, :grade_level, :grade_category, :chapter_topic,
                :resource_type, :medium_language, :description, :teaching_notes, :content_text,
                :file_name, :file_path, :file_type, :file_size_kb, :author_name, :author_role,
                :school_name, :curriculum_alignment, :tags, :downloads_count, :likes_count,
                :views_count, :rating_avg, :rating_count, :status, :copyright_confirmed
            )
            """, item)

            file_dest = Path(__file__).parent / item["file_path"]
            file_dest.parent.mkdir(parents=True, exist_ok=True)
            if not file_dest.exists():
                with open(file_dest, "w", encoding="utf-8") as f:
                    f.write(item["content_text"])

    # Ensure sample ratings and comments exist for Quadratic Equations
    cursor.execute("SELECT id FROM resources WHERE title LIKE '%Quadratic Equations%'")
    res1 = cursor.fetchone()
    if res1:
        res1_id = res1["id"]
        cursor.execute("INSERT OR IGNORE INTO ratings (resource_id, user_name, rating) VALUES (?, ?, ?)", (res1_id, "Tashi", 5))
        cursor.execute("INSERT OR IGNORE INTO ratings (resource_id, user_name, rating) VALUES (?, ?, ?)", (res1_id, "Dolma", 5))
        cursor.execute("SELECT COUNT(*) as c FROM comments WHERE resource_id = ?", (res1_id,))
        if cursor.fetchone()["c"] == 0:
            cursor.execute("""
            INSERT INTO comments (resource_id, user_name, user_school, user_role, comment_text)
            VALUES (?, ?, ?, ?, ?)
            """, (
                res1_id,
                "Tashi",
                "STSS Chauntra",
                "Mathematics Teacher",
                "This lesson package saved me hours of preparation for my Class 10 section! The distinction between discriminant cases and the word problem examples are brilliant."
            ))
            cursor.execute("""
            INSERT INTO comments (resource_id, user_name, user_school, user_role, comment_text)
            VALUES (?, ?, ?, ?, ?)
            """, (
                res1_id,
                "Dolma",
                "STSS Paonta Sahib",
                "Senior Mathematics Teacher",
                "The Tibetan translation of math terms (འགྱུར་ལྡོག་གཉིས་ལྡན་མཉམ་རྩིས) helps our bilingual students grasp the concept faster."
            ))
        cursor.execute("INSERT OR IGNORE INTO favorites (user_name, resource_id) VALUES (?, ?)", ("Tashi", res1_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_sample_data()
    print("Database schema updated and seeded successfully.")
