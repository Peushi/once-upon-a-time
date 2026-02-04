from django.shortcuts import render
from .models import Play
from .flask_api import flask_api
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.http import JsonResponse

@login_required
def my_history(request):

    plays = Play.objects.filter(user=request.user).order_by('-created_at')
    
    play_data = []
    unique_stories = set()
    unique_endings = set()

    for play in plays:
        story = flask_api.get_story(play.story_id)
        if story:
            unique_stories.add(play.story_id)
            # Get ending page info
            ending_page = flask_api.get_page(play.ending_page_id)
            if ending_page and ending_page.get('ending_label'):
                unique_endings.add(ending_page.get('ending_label'))
            
            
            play_data.append({
                'play': play,
                'story': story,
                'ending_page': ending_page,
            })
    
    context = {
        'play_data': play_data,
        'unique_stories_count': len(unique_stories),
        'unique_endings_count': len(unique_endings),
    }
    
    return render(request, 'game/my_history.html', context)

def api_story_stats(request, story_id):

    plays = Play.objects.filter(story_id=story_id)
    total_plays = plays.count()
    
    # Ending distribution
    ending_counts = plays.values('ending_page_id').annotate(count=Count('id'))
    ending_stats = []
    
    for ending in ending_counts:
        percentage = (ending['count'] / total_plays * 100) if total_plays > 0 else 0
        
        # Get ending label from Flask
        ending_page = flask_api.get_page(ending['ending_page_id'])
        ending_label = ending_page.get('ending_label', 'Unknown') if ending_page else 'Unknown'
        
        ending_stats.append({
            'ending_page_id': ending['ending_page_id'],
            'ending_label': ending_label,
            'count': ending['count'],
            'percentage': round(percentage, 1)
        })
    
    return JsonResponse({
        'story_id': story_id,
        'total_plays': total_plays,
        'ending_stats': ending_stats,
    })