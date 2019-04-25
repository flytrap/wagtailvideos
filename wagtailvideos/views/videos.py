#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from wagtail.admin import messages
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.utils import PermissionPolicyChecker, popular_tags_for_model
from wagtail.core.models import Collection
from wagtail.search.backends import get_search_backends
from wagtail.utils.pagination import paginate

from wagtailvideos import ffmpeg
from wagtailvideos.forms import VideoTranscodeAdminForm, get_video_form
from wagtailvideos.models import Video
from wagtailvideos.permissions import permission_policy

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    # Get Videos (filtered by user permission)
    videos = Video.objects.all()

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search videos"))
        if form.is_valid():
            query_string = form.cleaned_data['q']

            videos = videos.search(query_string)
    else:
        form = SearchForm(placeholder=_("Search videos"))

    # Filter by collection
    current_collection = None
    collection_id = request.GET.get('collection_id')
    if collection_id:
        try:
            current_collection = Collection.objects.get(id=collection_id)
            videos = videos.filter(collection=current_collection)
        except (ValueError, Collection.DoesNotExist):
            pass

    paginator, videos = paginate(request, videos)

    # Create response
    if request.is_ajax():
        response = render(request, 'wagtailvideos/videos/results.html', {
            'vidoes': videos,
            'query_string': query_string,
            'is_searching': bool(query_string),
        })
        return response
    else:
        response = render(request, 'wagtailvideos/videos/index.html', {
            'videos': videos,
            'query_string': query_string,
            'is_searching': bool(query_string),

            'search_form': form,
            'popular_tags': popular_tags_for_model(Video),
            'current_collection': current_collection,
        })
        return response


@permission_checker.require('change')
def edit(request, video_id):
    VideoForm = get_video_form(Video)
    video = get_object_or_404(Video, id=video_id)

    if request.POST:
        original_file = video.file
        form = VideoForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            if 'file' in form.changed_data:
                # if providing a new video file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)

                # Set new video file size
                video.file_size = video.file.size

            video = form.save()
            video.save()

            # Reindex the image to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(video)

            messages.success(request, _("Video '{0}' updated.").format(video.title), buttons=[
                messages.button(reverse('wagtailvideos:edit', args=(video.id,)), _('Edit again'))
            ])
            return redirect('wagtailvideos:index')
        else:
            messages.error(request, _("The video could not be saved due to errors."))
    else:
        form = VideoForm(instance=video)

    if not video._meta.get_field('file').storage.exists(video.file.name):
        # Give error if image file doesn't exist
        messages.error(request, _(
            "The source video file could not be found. Please change the source or delete the video."
        ).format(video.title), buttons=[
            messages.button(reverse('wagtailvideos:delete', args=(video.id,)), _('Delete'))
        ])

    return render(request, "wagtailvideos/videos/edit.html", {
        'video': video,
        'form': form,
        'filesize': video.get_file_size(),
        'can_transcode': ffmpeg.installed(),
        'transcodes': video.transcodes.all(),
        'transcode_form': VideoTranscodeAdminForm(video=video),
        'user_can_delete': permission_policy.user_has_permission_for_instance(request.user, 'delete', video)
    })


def create_transcode(request, video_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    video = get_object_or_404(Video, id=video_id)
    transcode_form = VideoTranscodeAdminForm(data=request.POST, video=video)

    if transcode_form.is_valid():
        transcode_form.save()
    return redirect('wagtailvideos:edit', video_id)


@permission_checker.require('delete')
def delete(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if request.POST:
        video.delete()
        messages.success(request, _("Video '{0}' deleted.").format(video.title))
        return redirect('wagtailvideos:index')

    return render(request, "wagtailvideos/videos/confirm_delete.html", {
        'video': video,
    })


@permission_checker.require('add')
def add(request):
    VideoForm = get_video_form(Video)

    if request.POST:
        video = Video(uploaded_by_user=request.user)
        form = VideoForm(request.POST, request.FILES, instance=video, user=request.user)
        if form.is_valid():
            # Save
            video = form.save(commit=False)
            video.file_size = video.file.size
            video.save()

            # Success! Send back an edit form
            for backend in get_search_backends():
                backend.add(video)

            messages.success(request, _("Video '{0}' added.").format(video.title), buttons=[
                messages.button(reverse('wagtailvideos:edit', args=(video.id,)), _('Edit'))
            ])
            return redirect('wagtailvideos:index')
        else:
            messages.error(request, _("The video could not be created due to errors."))
    else:
        form = VideoForm(user=request.user)

    return render(request, "wagtailvideos/videos/add.html", {
        'form': form,
    })


def usage(request, image_id):
    image = get_object_or_404(Video, id=image_id)

    paginator, used_by = paginate(request, image.get_usage())

    return render(request, "wagtailvideos/videos/usage.html", {
        'image': image,
        'used_by': used_by
    })
