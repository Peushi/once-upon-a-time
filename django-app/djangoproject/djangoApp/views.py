from django.shortcuts import render, redirect
from django.contrib import messages
from .flask_api import flask_api
from .models import Play, PlaySession, UserProfile, Rating, Report
from django.contrib.auth.models import User
from django.db.models import Count, Avg

user = User.objects.get(username="keeps")  # replace with your username
user.is_staff = True
user.is_superuser = True  # gives full access
user.save()
print("Done! You are now staff.")

def convert_tags_to_list(story):
    """Helper function to convert tags string to list"""
    if story and story.get("tags"):
        story["tags_list"] = [t.strip() for t in story["tags"].split(",") if t.strip()]
    else:
        story["tags_list"] = []
    return story


# home and browsing
def home(request):
    # get filter
    search_query = request.GET.get("search", "")
    tags_filter = request.GET.get("tags", "")

    # fetches
    stories = flask_api.get_stories(
        status="published",
        search=search_query if search_query else None,
        tags=tags_filter if tags_filter else None,
    )
    if stories:
        for story in stories:
            convert_tags_to_list(story)
            ratings = Rating.objects.filter(story_id=story["id"])
            if ratings.exists():
                story["avg_rating"] = ratings.aggregate(Avg("rating"))["rating__avg"]
                story["rating_count"] = ratings.count()
            else:
                story["avg_rating"] = None
                story["rating_count"] = 0

    context = {
        "stories": stories,
        "search_query": search_query,
        "tags_filter": tags_filter,
    }
    return render(request, "game/home.html", context)


def story_detail(request, story_id):
    story = flask_api.get_story(story_id)
    if not story:
        messages.error(request, "Story not found")
        return redirect("home")

    convert_tags_to_list(story)

    # check if user can view
    if story["status"] == "draft":
        if not request.user.is_authenticated:
            messages.error(request, "This story is not yet published")
            return redirect("home")

        profile = getattr(request.user, "profile", None)
        if not profile or (
            not profile.is_admin() and story.get("author_id") != request.user.id
        ):
            messages.error(request, "You do not have permission to view this story")
            return redirect("home")

    # stats:
    plays = Play.objects.filter(story_id=story_id)
    total_plays = plays.count()

    # ending distribution
    ending_count = plays.values("ending_page_id").annotate(count=Count("id"))
    ending_stats = []
    for ending in ending_count:
        percentage = (ending["count"] / total_plays * 100) if total_plays > 0 else 0
        ending_page = flask_api.get_page(ending["ending_page_id"])
        ending_label = ending_page.get("ending_label") if ending_page else None
        ending_stats.append(
            {
                "ending_page_id": ending["ending_page_id"],
                "ending_label": ending_label,
                "count": ending["count"],
                "percentage": round(percentage, 1),
            }
        )

    ratings = Rating.objects.filter(story_id=story_id).select_related("user")
    avg_rating = ratings.aggregate(Avg("rating"))["rating__avg"]
    user_rating = None
    if request.user.is_authenticated:
        user_rating = ratings.filter(user=request.user).first()

    can_edit = False
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        can_edit = (profile and profile.is_admin()) or story.get(
            "author_id"
        ) == request.user.id

    can_moderate = request.user.is_staff if request.user.is_authenticated else False
    reports = None
    if can_moderate:
        reports = Report.objects.filter(story_id=story_id).select_related("user")

    context = {
        "story": story,
        "total_plays": total_plays,
        "ending_stats": ending_stats,
        "ratings": ratings,
        "avg_rating": round(avg_rating, 1) if avg_rating else None,
        "rating_count": ratings.count(),
        "user_rating": user_rating,
        "can_edit": can_edit,
        "can_moderate": can_moderate,
        "reports": reports,
    }
    return render(request, "game/story_detail.html", context)


# gameplay


def play_story(request, story_id):
    story = flask_api.get_story(story_id)
    if not story:
        messages.error(request, "Story not found")
        return redirect("home")

    if story["status"] not in ["published", "draft"]:
        messages.error(request, "This story is not available for playing")
        return redirect("home")
    
    is_preview = (
        request.user.is_authenticated and 
        story.get("author_id") == request.user.id
    )

    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    saved_session = PlaySession.objects.filter(
        session_key=session_key, story_id=story_id
    ).first()

    if saved_session and request.GET.get("resume") != "false":
        return redirect(
            "play_page", story_id=story_id, page_id=saved_session.current_page_id
        )

    start_page = flask_api.get_story_start(story_id)
    start_page_id = start_page.get("page_id") if start_page else None
    if not start_page_id:
        messages.error(request, "Story has no start page set yet.")
        return redirect("story_detail", story_id=story_id)

    if saved_session:
        saved_session.current_page_id = start_page_id
        saved_session.save()
    else:
        PlaySession.objects.create(
            session_key=session_key,
            story_id=story_id,
            current_page_id=start_page_id,
            user=request.user if request.user.is_authenticated else None,
        )
    redirect_url = f"/play/{story_id}/page/{start_page_id}/"
    if is_preview:
        redirect_url += "?preview=1"
    return redirect(redirect_url)

def play_page(request, story_id, page_id):
    story = flask_api.get_story(story_id)
    page = flask_api.get_page(page_id)

    if not story or not page:
        messages.error(request, "Page not found")
        return redirect("home")
    is_preview = request.GET.get("preview") == "1"
    session_key = request.session.session_key
    if session_key:
        PlaySession.objects.update_or_create(
            session_key=session_key,
            story_id=story_id,
            defaults={
                "current_page_id": page_id,
                "user": request.user if request.user.is_authenticated else None,
            },
        )
    if page.get("is_ending"):
        if not is_preview:
            play = Play.objects.create(
                story_id=story_id,
                ending_page_id=page_id,
                user=request.user if request.user.is_authenticated else None,
            )
            play_id = play.id
        else:
            play_id = None 

        if session_key:
            PlaySession.objects.filter(
                session_key=session_key, story_id=story_id
            ).delete()

        context = {
            "story": story,
            "page": page,
            "is_ending": True,
            "play_id": play_id,
            "is_preview": is_preview, 
        }
        return render(request, "game/play_ending.html", context)

    context = {
        "story": story,
        "page": page,
        "is_ending": False,
        "is_preview": is_preview,
    }
    return render(request, "game/play_page.html", context)


def stats(request):
    if request.user.is_authenticated and not request.user.is_staff:
        messages.error(request, "You do not have permission to view statistics")
        return redirect("home")

    stories = flask_api.get_stories(status="published")
    story_stats = []
    for story in stories:
        plays = Play.objects.filter(story_id=story["id"])
        total_plays = plays.count()
        ending_counts = plays.values("ending_page_id").annotate(count=Count("id"))
        story_stats.append(
            {
                "story": story,
                "total_plays": total_plays,
                "unique_players": plays.filter(user__isnull=False)
                .values("user")
                .distinct()
                .count(),
                "endings": list(ending_counts),
            }
        )
    total_plays = Play.objects.count()
    total_users = User.objects.count()
    total_stories = len(stories)
    context = {
        "story_stats": story_stats,
        "total_plays": total_plays,
        "total_users": total_users,
        "total_stories": total_stories,
    }
    return render(request, "game/statistics.html", context)
