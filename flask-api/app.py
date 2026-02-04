from flask import Flask, request, jsonify
from sqlalchemy import or_
from config import Config
from extensions import db
from models import Story, Page, Choice


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Helpers
    def error(message, code=400):
        return jsonify({"error": message}), code

    VALID_STATUSES = {"draft", "published", "suspended"}

    def require_api_key():
        expected = app.config.get("API_KEY", "")
        if not expected:
            return error("Server API key not configured", 500)

        provided = request.headers.get("X-API-KEY", "")
        if provided != expected:
            return error("Invalid or missing API key", 401)

        return None

    def normalize_tags(tags_value):
        """
        Store tags as a single comma-separated string in DB.
        Django may send tags as a list or string.
        """
        if tags_value is None:
            return None
        if isinstance(tags_value, list):
            cleaned = [str(t).strip() for t in tags_value if str(t).strip()]
            return ",".join(cleaned) if cleaned else ""
        return str(tags_value)

    # READ ENDPOINTS 

    @app.get("/stories")
    def list_stories():
        status = request.args.get("status")
        search = request.args.get("search")
        tags = request.args.get("tags") 

        q = Story.query

        if status:
            q = q.filter_by(status=status)

        if search:
            like = f"%{search.strip()}%"
            q = q.filter(Story.title.ilike(like))

        if tags:
            tag_list = [t.strip() for t in str(tags).split(",") if t.strip()]
            if tag_list:
                conditions = [Story.tags.ilike(f"%{t}%") for t in tag_list]
                q = q.filter(or_(*conditions))

        stories = q.order_by(Story.id.desc()).all()

        return jsonify([
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "status": s.status,
                "start_page_id": s.start_page_id,
                "author_id": s.author_id,
                "tags": s.tags,
            }
            for s in stories
        ])

    @app.get("/stories/<int:story_id>")
    def get_story(story_id):
        s = Story.query.get(story_id)
        if not s:
            return error("Story not found", 404)

        include_pages = request.args.get("include_pages", "").lower() in {"1", "true", "yes"}

        payload = {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "status": s.status,
            "start_page_id": s.start_page_id,
            "author_id": s.author_id,
            "tags": s.tags,
        }

        if include_pages:
            pages = Page.query.filter_by(story_id=s.id).order_by(Page.id.asc()).all()
            payload["pages"] = [
                {
                    "id": p.id,
                    "story_id": p.story_id,
                    "text": p.text,
                    "is_ending": p.is_ending,
                    "ending_label": p.ending_label,
                }
                for p in pages
            ]

        return jsonify(payload)

    @app.get("/stories/<int:story_id>/start")
    def get_story_start(story_id):
        s = Story.query.get(story_id)
        if not s:
            return error("Story not found", 404)

        if s.status == "suspended":
            return error("Story is suspended", 403)

        if not s.start_page_id:
            return error("start_page_id not set", 400)

        return jsonify({"page_id": s.start_page_id})

    @app.get("/pages/<int:page_id>")
    def get_page(page_id):
        p = Page.query.get(page_id)
        if not p:
            return error("Page not found", 404)

        choices = Choice.query.filter_by(page_id=p.id).order_by(Choice.id.asc()).all()

        return jsonify({
            "id": p.id,
            "story_id": p.story_id,
            "text": p.text,
            "is_ending": p.is_ending,
            "ending_label": p.ending_label,
            "choices": [
                {
                    "id": c.id,
                    "text": c.text,
                    "next_page_id": c.next_page_id
                }
                for c in choices
            ]
        })

    # WRITE ENDPOINTS 

    @app.post("/stories")
    def create_story():
        block = require_api_key()
        if block:
            return block

        data = request.get_json(silent=True) or {}

        title = (data.get("title") or "").strip()
        if not title:
            return error("title is required", 400)

        status = data.get("status", "draft")
        if status not in VALID_STATUSES:
            return error("Invalid status. Use draft/published/suspended", 400)

        s = Story(
            title=title,
            description=data.get("description"),
            status=status,
            author_id=data.get("author_id"),
            tags=normalize_tags(data.get("tags")),
        )

        db.session.add(s)
        db.session.commit()

        return jsonify({
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "status": s.status,
                "start_page_id": s.start_page_id,
                "author_id": s.author_id,
                "tags": s.tags,
            }
        ), 201

    @app.put("/stories/<int:story_id>")
    def update_story(story_id):
        block = require_api_key()
        if block:
            return block

        s = Story.query.get(story_id)
        if not s:
            return error("Story not found", 404)

        data = request.get_json(silent=True) or {}

        if "title" in data:
            new_title = (data.get("title") or "").strip()
            if not new_title:
                return error("title cannot be empty", 400)
            s.title = new_title

        if "description" in data:
            s.description = data.get("description")

        if "status" in data:
            new_status = data.get("status")
            if new_status not in VALID_STATUSES:
                return error("Invalid status. Use draft/published/suspended", 400)
            s.status = new_status

        if "start_page_id" in data:
            s.start_page_id = data.get("start_page_id")

        if "author_id" in data:
            s.author_id = data.get("author_id")

        if "tags" in data:
            s.tags = normalize_tags(data.get("tags"))

        db.session.commit()

        return jsonify({
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "status": s.status,
                "start_page_id": s.start_page_id,
                "author_id": s.author_id,
                "tags": s.tags,
            }
        )

    @app.delete("/stories/<int:story_id>")
    def delete_story(story_id):
        block = require_api_key()
        if block:
            return block

        s = Story.query.get(story_id)
        if not s:
            return error("Story not found", 404)

        pages = Page.query.filter_by(story_id=s.id).all()
        page_ids = [p.id for p in pages]

        if page_ids:
            Choice.query.filter(Choice.page_id.in_(page_ids)).delete(synchronize_session=False)

        Page.query.filter_by(story_id=s.id).delete(synchronize_session=False)

        db.session.delete(s)
        db.session.commit()

        return jsonify({"deleted": True})

    @app.post("/stories/<int:story_id>/pages")
    def create_page(story_id):
        block = require_api_key()
        if block:
            return block

        s = Story.query.get(story_id)
        if not s:
            return error("Story not found", 404)

        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return error("text is required", 400)

        p = Page(
            story_id=story_id,
            text=text,
            is_ending=bool(data.get("is_ending", False)),
            ending_label=data.get("ending_label"),
        )
        db.session.add(p)
        db.session.commit()

        if not s.start_page_id:
            s.start_page_id = p.id
            db.session.commit()

        return jsonify({
                "id": p.id,
                "story_id": p.story_id,
                "text": p.text,
                "is_ending": p.is_ending,
                "ending_label": p.ending_label
            }
        ), 201

    @app.put("/pages/<int:page_id>")
    def update_page(page_id):
        block = require_api_key()
        if block:
            return block

        p = Page.query.get(page_id)
        if not p:
            return error("Page not found", 404)

        data = request.get_json(silent=True) or {}

        if "text" in data:
            new_text = (data.get("text") or "").strip()
            if not new_text:
                return error("text cannot be empty", 400)
            p.text = new_text

        if "is_ending" in data:
            p.is_ending = bool(data.get("is_ending"))

        if "ending_label" in data:
            p.ending_label = data.get("ending_label")

        db.session.commit()

        return jsonify({
                "id": p.id,
                "story_id": p.story_id,
                "text": p.text,
                "is_ending": p.is_ending,
                "ending_label": p.ending_label
            }
        )

    @app.delete("/pages/<int:page_id>")
    def delete_page(page_id):
        block = require_api_key()
        if block:
            return block

        p = Page.query.get(page_id)
        if not p:
            return error("Page not found", 404)

        Choice.query.filter_by(page_id=p.id).delete(synchronize_session=False)

        s = Story.query.get(p.story_id)
        if s and s.start_page_id == p.id:
            s.start_page_id = None

        db.session.delete(p)
        db.session.commit()
        return jsonify({"deleted": True})

    @app.post("/pages/<int:page_id>/choices")
    def create_choice(page_id):
        block = require_api_key()
        if block:
            return block

        p = Page.query.get(page_id)
        if not p:
            return error("Page not found", 404)

        data = request.get_json(silent=True) or {}

        text = (data.get("text") or "").strip()
        next_page_id = data.get("next_page_id")

        if not text:
            return error("text is required", 400)
        if not isinstance(next_page_id, int):
            return error("next_page_id must be an integer", 400)

        next_page = Page.query.get(next_page_id)
        if not next_page:
            return error("next_page_id does not exist", 400)
        if next_page.story_id != p.story_id:
            return error("next_page_id must belong to the same story", 400)

        c = Choice(page_id=page_id, text=text, next_page_id=next_page_id)
        db.session.add(c)
        db.session.commit()

        return jsonify({
                "id": c.id,
                "page_id": c.page_id,
                "text": c.text,
                "next_page_id": c.next_page_id
            }
        ), 201

    @app.put("/choices/<int:choice_id>")
    def update_choice(choice_id):
        block = require_api_key()
        if block:
            return block

        c = Choice.query.get(choice_id)
        if not c:
            return error("Choice not found", 404)

        data = request.get_json(silent=True) or {}

        if "text" in data:
            new_text = (data.get("text") or "").strip()
            if not new_text:
                return error("text cannot be empty", 400)
            c.text = new_text

        if "next_page_id" in data:
            new_next_id = data.get("next_page_id")
            if not isinstance(new_next_id, int):
                return error("next_page_id must be an integer", 400)

            next_page = Page.query.get(new_next_id)
            if not next_page:
                return error("next_page_id does not exist", 400)

            current_page = Page.query.get(c.page_id)
            if not current_page:
                return error("Choice page not found", 400)

            if next_page.story_id != current_page.story_id:
                return error("next_page_id must belong to the same story", 400)

            c.next_page_id = new_next_id

        db.session.commit()

        return jsonify({
                "id": c.id,
                "page_id": c.page_id,
                "text": c.text,
                "next_page_id": c.next_page_id
            }
        )

    @app.delete("/choices/<int:choice_id>")
    def delete_choice(choice_id):
        block = require_api_key()
        if block:
            return block

        c = Choice.query.get(choice_id)
        if not c:
            return error("Choice not found", 404)

        db.session.delete(c)
        db.session.commit()
        return jsonify({"deleted": True})

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
