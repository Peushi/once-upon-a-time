from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from .flask_api import flask_api
from .models import UserProfile, Rating, Report
import json


def convert_tags_to_list(story):
    """Helper function to convert tags string to list"""
    if story and story.get("tags"):
        story["tags_list"] = [t.strip() for t in story["tags"].split(",") if t.strip()]
    else:
        story["tags_list"] = []
    return story


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")
        role = request.POST.get("role", "reader")

        if not username or not password:
            messages.error(request, "Username and password are required")
            return render(request, "registration/register.html")

        if password != password2:
            messages.error(request, "Passwords do not match")
            return render(request, "registration/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, "registration/register.html")

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        UserProfile.objects.create(user=user, role=role)
        auth_login(request, user)
        messages.success(request, f"Welcome, {username}! Your account has been created")
        return redirect("home")
    return render(request, "registration/register.html")


@login_required
def my_stories(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if not profile.is_author():
        messages.error(
            request, "You need to be an author to create stories, make an account!"
        )
        return redirect("home")
    all_stories = flask_api.get_stories()
    my_stories = [s for s in all_stories if s.get("author_id") == request.user.id]
    for i, s in enumerate(my_stories):
        full = flask_api.get_story(s["id"], include_pages=True)
        if full:
            my_stories[i] = full
    for story in my_stories:
        convert_tags_to_list(story)
    published_count = len([s for s in my_stories if s.get("status") == "published"])
    draft_count = len([s for s in my_stories if s.get("status") == "draft"])
    context = {"stories": my_stories, "published_count": published_count, "draft_count": draft_count,          }
    return render(request, "game/my_stories.html", context)


@login_required
def create_story(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_author():
        messages.error(request, "You need to be an author to create a story.")
        return redirect("home")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        tags = request.POST.get("tags")

        if not title:
            messages.error(request, "Title is required")
            return render(request, "game/create_story.html")

        tags_list = [t.strip() for t in tags.split(",")] if tags else []

        story = flask_api.create_story(
            title=title,
            description=description,
            status="draft",
            author_id=request.user.id,
            tags=tags_list,
        )
        if story:
            messages.success(request, "Story created successfully!")
            return redirect("edit_story", story_id=story["id"])
        else:
            messages.error(request, "Failed to create story")
    return render(request, "game/create_story.html")


@login_required
def edit_story(request, story_id):
    story = flask_api.get_story(story_id, include_pages=True)
    if not story:
        messages.error(request, "Story not found")
        return redirect("my_stories")

    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin() and story.get("author_id") != request.user.id:
        messages.error(request, "You do not have permission to edit this story.")
        return redirect("home")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_story":
            title = request.POST.get("title")
            description = request.POST.get("description", "")
            tags = request.POST.get("tags", "")
            status = request.POST.get("status", "draft")

            tags_list = [t.strip() for t in tags.split(",") if t.strip()]

            updated_story = flask_api.update_story(
                story_id,
                title=title,
                description=description,
                status=status,
                tags=tags_list,
            )
            if updated_story:
                messages.success(request, "Story has been updated")
                return redirect("edit_story", story_id=story_id)
            else:
                messages.error(request, "Failed to update")
        elif action == "set_start_page":
            start_page_id = request.POST.get("start_page_id")
            if start_page_id:
                flask_api.update_story(story_id, start_page_id=int(start_page_id))
                messages.success(request, "Start page updated")
                return redirect("edit_story", story_id=story_id)
    story = flask_api.get_story(story_id, include_pages=True)
    convert_tags_to_list(story)
    context = {"story": story}
    return render(request, "game/edit_story.html", context)


def delete_story(request, story_id):
    story = flask_api.get_story(story_id, include_pages=True)
    if not story:
        messages.error(request, "Story not found")
        return redirect("my_stories")

    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin() and story.get("author_id") != request.user.id:
        return HttpResponseForbidden("You do not have permission to delete this story")
    if request.method == "POST":
        if flask_api.delete_story(story_id):
            messages.success(request, "Story deleted successfully")
        else:
            messages.error(request, "Faile to delete story")
        return redirect("my_stories")
    convert_tags_to_list(story)
    return render(request, "game/delete_story_confirm.html", {"story": story})


@login_required
def create_page(request, story_id):
    story = flask_api.get_story(story_id)
    if not story:
        messages.error(request, "Story not found")
        return redirect("my_stories")

    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin() and story.get("author_id") != request.user.id:
        return HttpResponseForbidden("You do not have permission to edit this story")

    if request.method == "POST":
        text = request.POST.get("text")
        is_ending = request.POST.get("is_ending") == "on"
        ending_label = request.POST.get("ending_label", "")

        if not text:
            messages.error(request, "Page text is required")
            return render(request, "game/create_page.html", {"story": story})
        page = flask_api.create_page(
            story_id=story_id, text=text, is_ending=is_ending, ending_label=ending_label
        )
        if page:
            messages.success(request, "Page created successfully")
            return redirect("edit_story", story_id=story_id)
        else:
            messages.error(request, "Failed to create page")
    return render(request, "game/create_page.html", {"story": story})


@login_required
def edit_page(request, page_id):
    page = flask_api.get_page(page_id)
    if not page:
        messages.error(request, "Page not found")
        return redirect("my_stories")
    story = flask_api.get_story(page["story_id"], include_pages=True)
    
    page["page_number"] = page["id"] 
    if story and story.get("pages"):
        for idx, p in enumerate(story["pages"], start=1):
            if p["id"] == page["id"]:
                page["page_number"] = idx
                break
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin() and story.get("author_id") != request.user.id:
        return HttpResponseForbidden("You do not have permission to edit this page")
    if request.method == "POST":
        text = request.POST.get("text")
        is_ending = request.POST.get("is_ending") == "on"
        ending_label = request.POST.get("ending_label", "")
        updated_page = flask_api.update_page(
            page_id, text=text, is_ending=is_ending, ending_label=ending_label
        )
        if updated_page:
            messages.success(request, "Page updated successfully")
            return redirect("edit_story", story_id=page["story_id"])
        else:
            messages.error(request, "Failed to update page")
    context = {"page": page, "story": story}
    return render(request, "game/edit_page.html", context)


@login_required
def delete_page(request, page_id):
    page = flask_api.get_page(page_id)
    if not page:
        messages.error(request, "Page not found")
        return redirect("my_stories")
    story_id = page["story_id"]
    story = flask_api.get_story(story_id, include_pages=True)
    page["page_number"] = page["id"] 
    if story and story.get("pages"):
        for idx, p in enumerate(story["pages"], start=1):
            if p["id"] == page["id"]:
                page["page_number"] = idx
                break
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin() and story.get("author_id") != request.user.id:
        return HttpResponseForbidden("You do not have permission to delete this story")
    if request.method == "POST":
        if flask_api.delete_page(page_id):
            messages.success(request, "Page deleted successfully")
        else:
            messages.error(request, "Failed to delete page")
        return redirect("edit_story", story_id=story_id)
    return render(
        request, "game/delete_page_confirm.html", {"page": page, "story": story}
    )


@login_required
def create_choice(request, page_id):
    page = flask_api.get_page(page_id)
    if not page:
        messages.error(request, "Page not found")
        return redirect("my_stories")

    story = flask_api.get_story(page["story_id"], include_pages=True)
    profile = get_object_or_404(UserProfile, user=request.user)
    if not profile.is_admin() and story.get("author_id") != request.user.id:
        return HttpResponseForbidden("You do not have permission to edit this page")

    if request.method == "POST":
        text = request.POST.get("text")
        next_page_id = int(request.POST.get("next_page_id"))
        try:
            next_page_id = int(next_page_id)
        except (TypeError, ValueError):
            messages.error(request, "next_page_id must be a number")
            return render(
                request, "game/create_choice.html", {"page": page, "story": story}
            )

        if not text or not next_page_id:
            messages.error(request, "Choice text and destination are required")
            return render(
                request, "game/create_choice.html", {"page": page, "story": story}
            )
        choice = flask_api.create_choice(
            page_id=page_id, text=text, next_page_id=next_page_id
        )
        if choice:
            messages.success(request, "Choice created successfully")
            return redirect("edit_story", story_id=story["id"])

        else:
            messages.error(request, "Failed to create choice")
    context = {"page": page, "story": story}
    return render(request, "game/create_choice.html", context)


@login_required
def delete_choice(request, choice_id):
    if request.method == "POST":
        page_id = request.POST.get("page_id")
        story_id = request.POST.get("story_id")

        if flask_api.delete_choice(choice_id):
            messages.success(request, "choice deleted successfully")
        else:
            messages.error(request, "Failed to delete choice")
        return redirect("edit_story", story_id=story_id)
    return redirect("my_stories")


@login_required
def suspend_story(request, story_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Admin access required")
    if request.method == "POST":
        story = flask_api.update_story(story_id, status="suspended")
        if story:
            messages.success(request, "Story suspended")
        else:
            messages.error(request, "Failed to suspend story")

    return redirect("story_detail", story_id=story_id)


@login_required
def unsuspend_story(request, story_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Admin access required")

    if request.method == "POST":
        story = flask_api.update_story(story_id, status="published")
        if story:
            messages.success(request, "Story published")
        else:
            messages.error(request, "Failed to publish story")

    return redirect("story_detail", story_id=story_id)



def story_tree(request, story_id):
    story = flask_api.get_story(story_id, include_pages=True)
    if not story:
        messages.error(request, "Story not found")
        return redirect("home")
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to view the story map.")
        return redirect("login")

    profile = getattr(request.user, "profile", None)
    if not profile:
        messages.error(request, "You do not have permission to view this story map.")
        return redirect("home")

    if not profile.is_admin() and story.get("author_id") != request.user.id:
        messages.error(request, "You do not have permission to view this story map.")
        return redirect("home")

    pages = story.get("pages", []) or []
    start_id = story.get("start_page_id")

    nodes = []
    edges = []

    for p in pages:
        text_preview = (p.get("text") or "").strip()
        if len(text_preview) > 60:
            text_preview = text_preview[:57] + "..."

        nodes.append(
            {
                "id": p.get("id"),
                "page_number": p.get("page_number"),
                "text": text_preview,
                "is_start": (p.get("id") == start_id),
                "is_ending": bool(p.get("is_ending")),
                "ending_label": p.get("ending_label") or "",
            }
        )

        for c in p.get("choices") or []:
            edges.append(
                {
                    "from": p.get("id"),
                    "to": c.get("next_page_id"),
                    "text": (c.get("text") or "").strip(),
                }
            )

    tree_data = {"nodes": nodes, "edges": edges}

    return render(
        request,
        "game/story_tree.html",
        {
            "story": story,
            "tree_data": json.dumps(tree_data),
        },
    )

@login_required
def rate_story(request, story_id):
    story = flask_api.get_story(story_id)
    if not story:
        messages.error(request, "Story not found.")
        return redirect("home")

    if request.method != "POST":
        return redirect("story_detail", story_id=story_id)

    rating_value = request.POST.get("rating")
    comment = request.POST.get("comment", "").strip()
    try:
        rating_value = int(rating_value)
        if rating_value < 1 or rating_value > 5:
            raise ValueError()
    except:
        messages.error(request, "Invalid rating. Please choose between 1 and 5.")
        return redirect("story_detail", story_id=story_id)
    
    created = Rating.objects.update_or_create(
        story_id=story_id,
        user=request.user,
        defaults={"rating": rating_value, "comment": comment},
    )

    if created:
        messages.success(request, "Your rating has been submitted!")
    else:
        messages.success(request, "Your rating has been updated!")

    return redirect("story_detail", story_id=story_id)

@login_required
def delete_rating(request, rating_id):
    rating = get_object_or_404(Rating, id=rating_id)

    if rating.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to delete this rating.")

    story_id = rating.story_id
    rating.delete()

    messages.success(request, "Your rating has been deleted.")
    return redirect("story_detail", story_id=story_id)

@login_required
def report_story(request, story_id):
    story = flask_api.get_story(story_id)
    if not story:
        messages.error(request, "Story not found.")
        return redirect("home")

    if request.method == "POST":
        reason = request.POST.get("reason")
        description = request.POST.get("description", "").strip()

        if not reason:
            messages.error(request, "Please select a reason.")
            return redirect("report_story", story_id=story_id)

        if not description:
            messages.error(request, "Please describe the issue.")
            return redirect("report_story", story_id=story_id)
        
        Report.objects.create(
            story_id=story_id,
            user=request.user,
            reason=reason,
            description=description,
        )
        messages.success(request, "Report submitted successfully. Thank you!")
        return redirect("story_detail", story_id=story_id)

    return render(request, "game/report_story.html", {"story": story})


@login_required
def reports_list(request):
    if not request.user.is_staff:
        messages.error(request, "Admin access required")
        return redirect("home")

    reports = Report.objects.all().order_by("status", "-id")
    enriched_reports = []
    for r in reports:
        story = flask_api.get_story(r.story_id)
        r.story_title = story["title"] if story else "Unknown Story"
        enriched_reports.append(r)

    return render(request, "game/reports_list.html", {"reports": enriched_reports})


@login_required
def update_report(request, report_id):
    if not request.user.is_staff:
        messages.error(request, "Admin access required")
        return redirect("home")
    report = get_object_or_404(Report, id=report_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        notes = request.POST.get("moderator_notes", "").strip()

        valid_statuses = [s[0] for s in Report.status_choice]
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status.")
            return redirect("reports_list")

        report.status = new_status
        report.moderator_notes = notes
        report.reviewed_by = request.user
        report.save()
        messages.success(request, "Report updated successfully.")
        return redirect("reports_list")

    story = flask_api.get_story(report.story_id)
    story_title = story["title"] if story else "Unknown Story"

    return render(
        request,
        "game/update_report.html",
        {"report": report, "story_title": story_title},
    )
