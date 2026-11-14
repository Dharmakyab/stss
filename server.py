import os
import sys
import json
import sqlite3
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from email.parser import BytesParser
from email.policy import default
from datetime import datetime

import database

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

class STSSRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status=status)

    def serve_file(self, file_path, as_attachment=False, download_name=None):
        if not file_path.exists() or not file_path.is_file():
            self.send_error_json("File not found", status=404)
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        if file_path.suffix.lower() == ".md":
            mime_type = "text/markdown; charset=utf-8"
        elif file_path.suffix.lower() == ".pdf":
            mime_type = "application/pdf"

        file_size = file_path.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

        if as_attachment:
            filename = download_name or file_path.name
            safe_filename = filename.replace('"', '\\"')
            self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}"')
        else:
            filename = download_name or file_path.name
            safe_filename = filename.replace('"', '\\"')
            self.send_header("Content-Disposition", f'inline; filename="{safe_filename}"')

        self.end_headers()

        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                self.wfile.write(chunk)

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        return json.loads(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"
        query = parse_qs(parsed.query)

        # Static assets
        if path == "/" or path == "/index.html":
            return self.serve_file(STATIC_DIR / "index.html")
        elif path.startswith("/static/"):
            rel_path = unquote(path[len("/static/"):])
            return self.serve_file(STATIC_DIR / rel_path)
        elif path.startswith("/uploads/"):
            rel_path = unquote(path[len("/uploads/"):])
            return self.serve_file(UPLOADS_DIR / rel_path)

        # API Routes
        if path == "/api/resources":
            return self.handle_get_resources(query)
        elif path.startswith("/api/resources/") and path.endswith("/download"):
            parts = path.split("/")
            res_id = parts[3]
            return self.handle_download_resource(res_id)
        elif path.startswith("/api/resources/") and path.endswith("/file"):
            parts = path.split("/")
            res_id = parts[3]
            return self.handle_serve_resource_file(res_id)
        elif path.startswith("/api/resources/") and path.endswith("/comments"):
            parts = path.split("/")
            res_id = parts[3]
            return self.handle_get_comments(res_id)
        elif path.startswith("/api/resources/"):
            parts = path.split("/")
            res_id = parts[3]
            return self.handle_get_resource_detail(res_id, query)
        elif path == "/api/profile":
            return self.handle_get_profile(query)
        elif path == "/api/users":
            return self.handle_get_users()
        elif path == "/api/favorites":
            return self.handle_get_favorites(query)
        elif path == "/api/moderation/audit":
            return self.handle_get_moderation_audit()
        elif path == "/api/stats":
            return self.handle_get_stats()
        elif path == "/api/schools":
            return self.handle_get_schools()
        elif path == "/api/templates":
            return self.handle_get_templates()
        else:
            self.send_error_json("Endpoint not found", status=404)

    def handle_get_resources(self, query):
        conn = database.get_connection()
        cursor = conn.cursor()

        sql = """
        SELECT id, title, title_en, subject, grade_level, grade_category, chapter_topic,
               resource_type, medium_language, description, teaching_notes, file_name, file_type,
               file_size_kb, author_name, author_role, school_name, downloads_count,
               likes_count, views_count, rating_avg, rating_count, status, rejection_reason,
               created_at, tags
        FROM resources
        WHERE 1=1
        """
        params = []

        # Status filter: default to Published unless specified otherwise (e.g., 'Pending Review' or 'All')
        status = query.get("status", ["Published"])[0]
        if status != "All":
            sql += " AND status = ?"
            params.append(status)

        # Subject Filter
        if "subject" in query and query["subject"][0]:
            sql += " AND subject = ?"
            params.append(query["subject"][0])

        # Stage Filter
        if "grade_category" in query and query["grade_category"][0]:
            sql += " AND grade_category = ?"
            params.append(query["grade_category"][0])

        # Class Filter
        if "grade_level" in query and query["grade_level"][0]:
            sql += " AND grade_level = ?"
            params.append(query["grade_level"][0])

        # Resource Type Filter
        if "resource_type" in query and query["resource_type"][0]:
            sql += " AND resource_type = ?"
            params.append(query["resource_type"][0])

        # Medium / Language Filter
        if "medium_language" in query and query["medium_language"][0]:
            sql += " AND medium_language = ?"
            params.append(query["medium_language"][0])

        # School Filter
        if "school" in query and query["school"][0]:
            sql += " AND school_name = ?"
            params.append(query["school"][0])

        # Author Filter (For Profile page)
        if "author" in query and query["author"][0]:
            sql += " AND author_name = ?"
            params.append(query["author"][0])

        # Rating Filter (e.g. min_rating=4)
        if "min_rating" in query and query["min_rating"][0]:
            try:
                min_r = float(query["min_rating"][0])
                sql += " AND rating_avg >= ?"
                params.append(min_r)
            except ValueError:
                pass

        # Favorites Filter
        if "favorites_user" in query and query["favorites_user"][0]:
            fav_user = query["favorites_user"][0]
            sql += " AND id IN (SELECT resource_id FROM favorites WHERE user_name = ?)"
            params.append(fav_user)

        # Keyword search
        if "q" in query and query["q"][0]:
            q = f"%{query['q'][0].strip()}%"
            sql += """ AND (
                title LIKE ? OR title_en LIKE ? OR description LIKE ? OR
                chapter_topic LIKE ? OR tags LIKE ? OR author_name LIKE ? OR
                teaching_notes LIKE ?
            )"""
            params.extend([q, q, q, q, q, q, q])

        # Sorting
        sort = query.get("sort", ["newest"])[0]
        if sort == "popular":
            sql += " ORDER BY downloads_count DESC, views_count DESC"
        elif sort == "rating":
            sql += " ORDER BY rating_avg DESC, rating_count DESC"
        elif sort == "views":
            sql += " ORDER BY views_count DESC"
        elif sort == "likes":
            sql += " ORDER BY likes_count DESC"
        elif sort == "title":
            sql += " ORDER BY title ASC"
        else:
            sql += " ORDER BY created_at DESC, id DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        resources = [dict(row) for row in rows]
        conn.close()

        self.send_json({"count": len(resources), "resources": resources})

    def handle_get_resource_detail(self, res_id, query):
        conn = database.get_connection()
        cursor = conn.cursor()

        # Increment views_count
        cursor.execute("UPDATE resources SET views_count = views_count + 1 WHERE id = ?", (res_id,))
        conn.commit()

        cursor.execute("SELECT * FROM resources WHERE id = ?", (res_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            self.send_error_json("Resource not found", status=404)
            return

        data = dict(row)

        # Attach comments
        cursor.execute("SELECT * FROM comments WHERE resource_id = ? ORDER BY created_at DESC", (res_id,))
        data["comments"] = [dict(c) for c in cursor.fetchall()]

        # User-specific rating & favorite status if user query provided
        current_user = query.get("user", [""])[0]
        if current_user:
            cursor.execute("SELECT rating FROM ratings WHERE resource_id = ? AND user_name = ?", (res_id, current_user))
            user_r = cursor.fetchone()
            data["user_rating"] = user_r["rating"] if user_r else None

            cursor.execute("SELECT id FROM favorites WHERE resource_id = ? AND user_name = ?", (res_id, current_user))
            data["is_favorited"] = bool(cursor.fetchone())
        else:
            data["user_rating"] = None
            data["is_favorited"] = False

        conn.close()
        self.send_json(data)

    def handle_download_resource(self, res_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resources WHERE id = ?", (res_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            self.send_error_json("Resource not found", status=404)
            return

        cursor.execute("UPDATE resources SET downloads_count = downloads_count + 1 WHERE id = ?", (res_id,))
        conn.commit()
        conn.close()

        item = dict(row)
        file_path_str = item.get("file_path")
        file_name = item.get("file_name") or f"resource_{res_id}.txt"

        if file_path_str:
            target_path = BASE_DIR / file_path_str
            if target_path.exists():
                return self.serve_file(target_path, as_attachment=True, download_name=file_name)

        content_text = item.get("content_text", "")
        content_bytes = content_text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Length", str(len(content_bytes)))
        self.send_header("Content-Disposition", f'attachment; filename="{file_name}"')
        self.end_headers()
        self.wfile.write(content_bytes)

    def handle_serve_resource_file(self, res_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resources WHERE id = ?", (res_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            self.send_error_json("Resource not found", status=404)
            return

        item = dict(row)
        file_path_str = item.get("file_path")
        file_name = item.get("file_name") or f"resource_{res_id}.txt"

        if file_path_str:
            target_path = BASE_DIR / file_path_str
            if target_path.exists():
                return self.serve_file(target_path, as_attachment=False, download_name=file_name)

        content_text = item.get("content_text", "")
        content_bytes = content_text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Length", str(len(content_bytes)))
        self.send_header("Content-Disposition", f'inline; filename="{file_name}"')
        self.end_headers()
        self.wfile.write(content_bytes)

    def handle_get_profile(self, query):
        name = query.get("name", [""])[0].strip()
        if not name:
            self.send_error_json("name parameter is required", status=400)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        user_row = cursor.fetchone()

        cursor.execute("""
        SELECT COUNT(*) as total_resources,
               COALESCE(SUM(downloads_count), 0) as total_downloads,
               COALESCE(SUM(views_count), 0) as total_views,
               COALESCE(SUM(likes_count), 0) as total_likes,
               COALESCE(AVG(rating_avg), 5.0) as avg_rating
        FROM resources
        WHERE author_name = ?
        """, (name,))
        stats_row = cursor.fetchone()

        cursor.execute("""
        SELECT id, title, title_en, subject, grade_level, chapter_topic, resource_type,
               medium_language, file_type, downloads_count, views_count, likes_count,
               rating_avg, rating_count, status, created_at, school_name
        FROM resources
        WHERE author_name = ?
        ORDER BY created_at DESC
        """, (name,))
        user_resources = [dict(r) for r in cursor.fetchall()]
        conn.close()

        school_default = user_resources[0]["school_name"] if user_resources else "STSS Network"
        role_default = "Senior Teacher" if (user_row and user_row["role"] == "Teacher") else (user_row["role"] if user_row else "Teacher")

        profile = {
            "name": name,
            "role": user_row["role"] if user_row else "Teacher",
            "school": user_row["school"] if (user_row and user_row["school"]) else school_default,
            "specialization": user_row["specialization"] if (user_row and user_row["specialization"]) else "STSS Teaching Contributor",
            "joined_date": user_row["joined_date"] if user_row else "Active Contributor",
            "stats": {
                "total_resources": stats_row["total_resources"] or 0,
                "total_downloads": stats_row["total_downloads"] or 0,
                "total_views": stats_row["total_views"] or 0,
                "total_likes": stats_row["total_likes"] or 0,
                "avg_rating": round(stats_row["avg_rating"], 1) if stats_row["avg_rating"] else 5.0
            },
            "resources": user_resources
        }
        self.send_json(profile)

    def handle_get_comments(self, res_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM comments WHERE resource_id = ? ORDER BY created_at DESC", (res_id,))
        comments = [dict(c) for c in cursor.fetchall()]
        conn.close()
        self.send_json({"resource_id": int(res_id), "comments": comments})

    def handle_get_users(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY id ASC")
        users = [dict(u) for u in cursor.fetchall()]
        conn.close()
        self.send_json({"users": users})

    def handle_get_favorites(self, query):
        user_name = query.get("user_name", [""])[0]
        if not user_name:
            self.send_error_json("user_name parameter required", status=400)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT resource_id FROM favorites WHERE user_name = ?", (user_name,))
        ids = [row["resource_id"] for row in cursor.fetchall()]
        conn.close()
        self.send_json({"user_name": user_name, "favorite_ids": ids})

    def handle_get_moderation_audit(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.*, r.title as resource_title
        FROM moderation_audit a
        LEFT JOIN resources r ON a.resource_id = r.id
        ORDER BY a.created_at DESC LIMIT 50
        """)
        audits = [dict(a) for a in cursor.fetchall()]
        conn.close()
        self.send_json({"audit_logs": audits})

    def handle_get_stats(self):
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total_resources FROM resources WHERE status = 'Published'")
        total_resources = cursor.fetchone()["total_resources"]

        cursor.execute("SELECT COUNT(*) as pending_review FROM resources WHERE status = 'Pending Review'")
        pending_review = cursor.fetchone()["pending_review"]

        cursor.execute("SELECT SUM(downloads_count) as total_downloads FROM resources")
        total_downloads = cursor.fetchone()["total_downloads"] or 0

        cursor.execute("SELECT SUM(views_count) as total_views FROM resources")
        total_views = cursor.fetchone()["total_views"] or 0

        cursor.execute("SELECT COUNT(*) as total_reviews FROM comments")
        total_reviews = cursor.fetchone()["total_reviews"]

        cursor.execute("SELECT subject, COUNT(*) as count FROM resources WHERE status = 'Published' GROUP BY subject ORDER BY count DESC")
        by_subject = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT grade_category, COUNT(*) as count FROM resources WHERE status = 'Published' GROUP BY grade_category ORDER BY count DESC")
        by_grade_category = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT resource_type, COUNT(*) as count FROM resources WHERE status = 'Published' GROUP BY resource_type ORDER BY count DESC")
        by_type = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT school_name, COUNT(*) as count FROM resources WHERE status = 'Published' GROUP BY school_name ORDER BY count DESC LIMIT 5")
        top_schools = [dict(r) for r in cursor.fetchall()]

        conn.close()

        self.send_json({
            "total_resources": total_resources,
            "pending_review": pending_review,
            "total_downloads": total_downloads,
            "total_views": total_views,
            "total_reviews": total_reviews,
            "by_subject": by_subject,
            "by_grade_category": by_grade_category,
            "by_type": by_type,
            "top_schools": top_schools
        })

    def handle_get_schools(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM schools ORDER BY name ASC")
        schools = [dict(r) for r in cursor.fetchall()]
        conn.close()
        self.send_json({"schools": schools})

    def handle_get_templates(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM templates ORDER BY id ASC")
        templates = [dict(r) for r in cursor.fetchall()]
        conn.close()
        self.send_json({"templates": templates})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/resources/") and path.endswith("/like"):
            res_id = path.split("/")[3]
            return self.handle_like_resource(res_id)
        elif path.startswith("/api/resources/") and path.endswith("/rate"):
            res_id = path.split("/")[3]
            return self.handle_rate_resource(res_id)
        elif path.startswith("/api/resources/") and path.endswith("/comments"):
            res_id = path.split("/")[3]
            return self.handle_add_comment(res_id)
        elif path.startswith("/api/resources/") and path.endswith("/favorite"):
            res_id = path.split("/")[3]
            return self.handle_toggle_favorite(res_id)
        elif path.startswith("/api/resources/") and path.endswith("/report"):
            res_id = path.split("/")[3]
            return self.handle_report_resource(res_id)
        elif path.startswith("/api/moderation/") and path.endswith("/action"):
            res_id = path.split("/")[3]
            return self.handle_moderation_action(res_id)
        elif path == "/api/resources":
            return self.handle_create_resource()
        else:
            self.send_error_json("Invalid POST endpoint", status=404)

    def handle_like_resource(self, res_id):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE resources SET likes_count = likes_count + 1 WHERE id = ?", (res_id,))
        if cursor.rowcount == 0:
            conn.close()
            self.send_error_json("Resource not found", status=404)
            return

        cursor.execute("SELECT likes_count FROM resources WHERE id = ?", (res_id,))
        likes = cursor.fetchone()["likes_count"]
        conn.commit()
        conn.close()
        self.send_json({"id": int(res_id), "likes_count": likes})

    def handle_rate_resource(self, res_id):
        data = self.read_json_body()
        user_name = data.get("user_name", "Anonymous Teacher")
        try:
            rating = int(data.get("rating", 5))
            if not (1 <= rating <= 5):
                raise ValueError
        except (ValueError, TypeError):
            self.send_error_json("Rating must be an integer between 1 and 5", status=400)
            return

        conn = database.get_connection()
        cursor = conn.cursor()

        # Insert or replace user's rating
        cursor.execute("""
        INSERT INTO ratings (resource_id, user_name, rating, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(resource_id, user_name) DO UPDATE SET rating = excluded.rating, created_at = CURRENT_TIMESTAMP
        """, (res_id, user_name, rating))

        # Recompute average and count
        cursor.execute("SELECT AVG(rating) as avg_r, COUNT(rating) as count_r FROM ratings WHERE resource_id = ?", (res_id,))
        agg = cursor.fetchone()
        avg_rating = round(agg["avg_r"], 1) if agg["avg_r"] else 5.0
        count_rating = agg["count_r"] or 0

        cursor.execute("UPDATE resources SET rating_avg = ?, rating_count = ? WHERE id = ?", (avg_rating, count_rating, res_id))
        conn.commit()
        conn.close()

        self.send_json({
            "resource_id": int(res_id),
            "user_rating": rating,
            "rating_avg": avg_rating,
            "rating_count": count_rating
        })

    def handle_add_comment(self, res_id):
        data = self.read_json_body()
        user_name = data.get("user_name", "").strip() or "STSS Teacher"
        user_school = data.get("user_school", "").strip() or "STSS Network"
        user_role = data.get("user_role", "").strip() or "Teacher"
        comment_text = data.get("comment_text", "").strip()

        if not comment_text:
            self.send_error_json("Comment text cannot be empty", status=400)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO comments (resource_id, user_name, user_school, user_role, comment_text)
        VALUES (?, ?, ?, ?, ?)
        """, (res_id, user_name, user_school, user_role, comment_text))
        new_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM comments WHERE id = ?", (new_id,))
        comment = dict(cursor.fetchone())
        conn.close()

        self.send_json(comment, status=201)

    def handle_toggle_favorite(self, res_id):
        data = self.read_json_body()
        user_name = data.get("user_name", "").strip()
        if not user_name:
            self.send_error_json("user_name is required", status=400)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM favorites WHERE resource_id = ? AND user_name = ?", (res_id, user_name))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("DELETE FROM favorites WHERE id = ?", (existing["id"],))
            favorited = False
        else:
            cursor.execute("INSERT INTO favorites (resource_id, user_name) VALUES (?, ?)", (res_id, user_name))
            favorited = True

        conn.commit()
        conn.close()

        self.send_json({"resource_id": int(res_id), "user_name": user_name, "favorited": favorited})

    def handle_report_resource(self, res_id):
        data = self.read_json_body()
        user_name = data.get("user_name", "Teacher")
        reason = data.get("reason", "").strip() or "Quality or copyright review requested."

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO moderation_audit (resource_id, moderator_name, action, reason)
        VALUES (?, ?, 'Flagged', ?)
        """, (res_id, user_name, reason))
        conn.commit()
        conn.close()

        self.send_json({"resource_id": int(res_id), "status": "flagged", "message": "Report logged for moderator review."})

    def handle_moderation_action(self, res_id):
        data = self.read_json_body()
        moderator_name = data.get("moderator_name", "Tenzin")
        action = data.get("action", "") # "Approved", "Rejected", "Archived"
        reason = data.get("reason", "").strip()

        if action not in ["Approved", "Rejected", "Archived"]:
            self.send_error_json("Action must be 'Approved', 'Rejected', or 'Archived'", status=400)
            return

        new_status = "Published" if action == "Approved" else ("Rejected" if action == "Rejected" else "Archived")

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE resources
        SET status = ?, rejection_reason = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (new_status, reason if action == "Rejected" else None, res_id))

        cursor.execute("""
        INSERT INTO moderation_audit (resource_id, moderator_name, action, reason)
        VALUES (?, ?, ?, ?)
        """, (res_id, moderator_name, action, reason))

        conn.commit()

        cursor.execute("SELECT * FROM resources WHERE id = ?", (res_id,))
        row = cursor.fetchone()
        conn.close()

        self.send_json(dict(row))

    def handle_create_resource(self):
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)

        fields = {}
        uploaded_file = None

        if "multipart/form-data" in content_type:
            msg = BytesParser(policy=default).parsebytes(
                b"Content-Type: " + content_type.encode("latin-1", errors="replace") + b"\r\n\r\n" + body_bytes
            )
            for part in msg.iter_parts():
                name = part.get_param("name", header="content-disposition")
                filename = part.get_filename()
                payload = part.get_payload(decode=True)
                if filename:
                    uploaded_file = {"filename": filename, "content": payload}
                elif name:
                    fields[name] = payload.decode("utf-8", errors="replace")
        elif "application/json" in content_type:
            try:
                fields = json.loads(body_bytes.decode("utf-8"))
            except Exception as e:
                self.send_error_json(f"Invalid JSON: {str(e)}", status=400)
                return
        else:
            self.send_error_json("Unsupported Content-Type", status=415)
            return

        # Validation (Module B & Module K Copyright Confirmation)
        title = fields.get("title", "").strip()
        subject = fields.get("subject", "").strip()
        grade_level = fields.get("grade_level", "").strip()
        school_name = fields.get("school_name", "").strip()
        author_name = fields.get("author_name", "").strip()
        copyright_confirmed = fields.get("copyright_confirmed", False)

        if str(copyright_confirmed).lower() not in ["1", "true", "yes", "on"]:
            self.send_error_json("Module K Compliance: You must confirm that you own this material or hold copyright permissions before uploading.", status=400)
            return

        if not title or not subject or not grade_level or not school_name or not author_name:
            self.send_error_json("Required fields missing: title, subject, grade_level, school_name, and author_name are required.", status=400)
            return

        # Calculate Grade Category
        grade_category = fields.get("grade_category", "")
        if not grade_category:
            if "Pre-Primary" in grade_level or "Kindergarten" in grade_level:
                grade_category = "Pre-Primary"
            elif any(f"Class {i}" in grade_level for i in range(1, 6)):
                grade_category = "Primary (1-5)"
            elif any(f"Class {i}" in grade_level for i in range(6, 9)):
                grade_category = "Middle (6-8)"
            elif any(f"Class {i}" in grade_level for i in [9, 10]):
                grade_category = "Secondary (9-10)"
            elif any(f"Class {i}" in grade_level for i in [11, 12]):
                grade_category = "Senior Secondary (11-12)"
            else:
                grade_category = "General"

        # Handle File storage
        file_name = ""
        file_path = ""
        file_type = "md"
        file_size_kb = 0
        content_text = fields.get("content_text", "")

        if uploaded_file and uploaded_file.get("filename"):
            orig_name = uploaded_file["filename"]
            safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(orig_name)}"
            dest = UPLOADS_DIR / safe_name
            with open(dest, "wb") as f:
                f.write(uploaded_file["content"])
            file_name = orig_name
            file_path = f"uploads/{safe_name}"
            file_type = os.path.splitext(orig_name)[1].lstrip(".").lower() or "bin"
            file_size_kb = max(1, len(uploaded_file["content"]) // 1024)

            if file_type in ["md", "txt"] and not content_text:
                try:
                    content_text = uploaded_file["content"].decode("utf-8")
                except Exception:
                    pass
        elif content_text:
            safe_slug = "".join(c if c.isalnum() else "_" for c in title[:30]).strip("_")
            file_name = f"{safe_slug or 'resource'}.md"
            saved_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
            dest = UPLOADS_DIR / saved_name
            dest_content = content_text.encode("utf-8")
            with open(dest, "wb") as f:
                f.write(dest_content)
            file_path = f"uploads/{saved_name}"
            file_type = "md"
            file_size_kb = max(1, len(dest_content) // 1024)

        # Status: Module K requires "Pending Review" by default, or "Published" if approved by moderator
        status = fields.get("status", "Pending Review")

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO resources (
            title, title_en, subject, grade_level, grade_category, chapter_topic,
            resource_type, medium_language, description, teaching_notes, content_text,
            file_name, file_path, file_type, file_size_kb, author_name, author_role,
            school_name, curriculum_alignment, tags, status, copyright_confirmed
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1
        )
        """, (
            title,
            fields.get("title_en", ""),
            subject,
            grade_level,
            grade_category,
            fields.get("chapter_topic", "General"),
            fields.get("resource_type", "Lesson Plan"),
            fields.get("medium_language", "Tibetan (བོད་ཡིག)"),
            fields.get("description", ""),
            fields.get("teaching_notes", ""),
            content_text,
            file_name,
            file_path,
            file_type,
            file_size_kb,
            author_name,
            fields.get("author_role", "STSS Educator"),
            school_name,
            fields.get("curriculum_alignment", "STSS / CTA DoE & CBSE"),
            fields.get("tags", ""),
            status
        ))
        new_id = cursor.lastrowid

        # Log creation in audit
        cursor.execute("""
        INSERT INTO moderation_audit (resource_id, moderator_name, action, reason)
        VALUES (?, ?, 'Submitted', 'Initial submission into Pending Review queue.')
        """, (new_id, author_name))

        conn.commit()

        cursor.execute("SELECT * FROM resources WHERE id = ?", (new_id,))
        created_resource = dict(cursor.fetchone())
        conn.close()

        self.send_json(created_resource, status=201)

def run(port=8080):
    database.init_db()
    database.seed_sample_data()

    server_address = ("", port)
    try:
        httpd = HTTPServer(server_address, STSSRequestHandler)
    except OSError:
        port = 8081
        server_address = ("", port)
        httpd = HTTPServer(server_address, STSSRequestHandler)

    print(f"============================================================")
    print(f" བོད་མིའི་སྒྲིག་འཛུགས་ཤེས་རིག་ལས་ཁུངས། སམ་བྷོ་ཊ་བོད་སློབ་ཚོགས་པ།")
    print(f" Sambhota Tibetan Schools Society (STSS) Teaching Repository")
    print(f" Server running at: http://localhost:{port}")
    print(f"============================================================")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping STSS Teaching Repository Server...")
        httpd.server_close()

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run(port=port)
