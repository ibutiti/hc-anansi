from collections import Counter
from datetime import timedelta as td
from itertools import tee

import requests
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.forms.models import model_to_dict
from django.utils.six.moves.urllib.parse import urlencode
from hc.api.decorators import uuid_or_400
from hc.api.models import DEFAULT_GRACE, DEFAULT_TIMEOUT, Channel, Check, Ping
from hc.front.forms import (AddChannelForm, AddWebhookForm, NameTagsForm,
                            PriorityForm, TimeoutForm)
from .models import Faq, Tutorial
from .forms import CreateBlogPost, CreateCategory, CreateCommentForm
from .models import Category, Blog_post, Comment

# from itertools recipes:
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def blogs(request, filter_by):
    """function to render the home page"""
    num = 3 # setting number of blog posts to be displayed as three per row
    category = Category.objects.all()
    if int(filter_by):
        category_id = Category.objects.get(pk=filter_by).id
        stories = Blog_post.objects.filter(category=category_id)
    else:
        stories = Blog_post.objects.all()
    list_of_stories = [story for story in stories]
    blogs = [list_of_stories[item:item+num] for item in range(0, len(list_of_stories), num)]
    ctx = {
        'category':category,
        'blogs':blogs
    }
    return render(request, 'front/blog_posts.html', ctx)


def create_blog(request):
    """function to create a category and a blog """
    form = CreateBlogPost(request.POST)
    category_form = CreateCategory(request.POST)
    if request.method == 'POST':
        if 'new_category' in request.POST and category_form.is_valid():
                name = category_form.cleaned_data['category']
                ctg = Category(name = name)
                ctg.save()
                return redirect(create_blog)
        elif 'create_blog' in request.POST and form.is_valid():
                title = request.POST['title']
                blog = form.cleaned_data['content']
                selected_category = request.POST['category_name']
                category = Category.objects.get(name=selected_category)
                published = timezone.now()
                user = request.user
                blog = Blog_post(title=title, content=blog, category=category,
                                published=published, user=user)
                blog.save()
                messages.add_message(request, messages.INFO, 'Successfully created blog')
                return redirect(read_blog, pk=blog.id)
    else:
        categories = Category.objects.all()
        ctx = {
            'category': categories,
            'form': CreateBlogPost({'content':'Write Blog'}),
            'category_form': category_form,
            'edit': False
            }
        return render(request, 'front/create_blog.html', ctx)


def read_blog(request, pk):
    comment_form = CreateCommentForm(request.POST)
    blog = Blog_post.objects.get(pk=pk)
    featured = Blog_post.objects.get(pk=pk)
    comments = Comment.objects.filter(blog = blog.id)
    url = "https://hc-anansi-staging.herokuapp.com/blog/read_blog/{pk}".format(pk=pk)
    ctx = {
        'blog': blog,
        'featured': featured,
        'tweet_url': url,
        'comments': comments
    }
    if 'add_comment' in request.POST and comment_form.is_valid():
            posted_comment = request.POST['comment']
            published = timezone.now()
            comment = Comment(comment = posted_comment, blog = blog, user = request.user, published=published)
            comment.save()
            return redirect(read_blog, pk=blog.id)
    return render(request, 'front/readblog.html', ctx )


def delete_blog(request, pk):
    deleted_blog = Blog_post.objects.get(pk=pk)
    Blog_post.objects.get(pk=pk).delete()
    messages.add_message(request, messages.INFO, 'Successfully deleted blog')
    return redirect(blogs, filter_by=0)


def edit_blog(request, pk):
    blog =  Blog_post.objects.get(pk=pk)
    Category = blog.category
    if request.method == 'POST':
        form = CreateBlogPost(request.POST)
        category_form = CreateCategory(request.POST)
        if "create_blog" in request.POST and form.is_valid():
                blog.category = blog.category
                blog.title = request.POST['title']
                blog.content = request.POST['content']
                blog.publish = timezone.now()
                blog.save()
                messages.add_message(request, messages.INFO, 'Successfully edited blog')
                return redirect(read_blog, pk)
    else:
        form = CreateBlogPost({'content':blog.content})
        ctx = {
        'form': form,
        'title': blog.title,
        'edit': True
         }
        return render(request, "front/create_blog.html", ctx )


@login_required
def my_checks(request):
    q = Check.objects.filter(user=request.team.user).order_by("-priority",
                                                              "created")
    checks = list(q)
    # create a list of unresolved checks
    unresolved_checks = []
    # add queryset of email channels to context
    channels = Channel.objects.filter(user=request.team.user,
                                      kind="email").order_by("created")

    counter = Counter()
    down_tags, grace_tags = set(), set()
    for check in checks:
        status = check.get_status()
        if status == "down":
            # add checks with status down to unresolved checks list
            unresolved_checks.append(check)
        for tag in check.tags_list():
            if tag == "":
                continue

            counter[tag] += 1

            if status == "down":
                down_tags.add(tag)
            elif check.in_grace_period():
                grace_tags.add(tag)

    ctx = {
        "page": "checks",
        "checks": checks,
        "channels": channels,
        "now": timezone.now(),
        # pass unresolved checks list to context
        "unresolved_checks": unresolved_checks,
        "tags": counter.most_common(),
        "down_tags": down_tags,
        "grace_tags": grace_tags,
        "ping_endpoint": settings.PING_ENDPOINT
    }

    return render(request, "front/my_checks.html", ctx)


def _welcome_check(request):
    check = None
    if "welcome_code" in request.session:
        code = request.session["welcome_code"]
        check = Check.objects.filter(code=code).first()

    if check is None:
        check = Check()
        check.save()
        request.session["welcome_code"] = str(check.code)

    return check


def index(request):
    if request.user.is_authenticated:
        return redirect("hc-checks")

    check = _welcome_check(request)

    ctx = {
        "page": "welcome",
        "check": check,
        "ping_url": check.url(),
        "enable_pushover": settings.PUSHOVER_API_TOKEN is not None
    }

    return render(request, "front/welcome.html", ctx)


def docs(request):
    check = _welcome_check(request)

    ctx = {
        "page": "docs",
        "section": "home",
        "ping_endpoint": settings.PING_ENDPOINT,
        "check": check,
        "ping_url": check.url()
    }

    return render(request, "front/docs.html", ctx)


def docs_api(request):
    ctx = {
        "page": "docs",
        "section": "api",
        "SITE_ROOT": settings.SITE_ROOT,
        "PING_ENDPOINT": settings.PING_ENDPOINT,
        "default_timeout": int(DEFAULT_TIMEOUT.total_seconds()),
        "default_grace": int(DEFAULT_GRACE.total_seconds())
    }

    return render(request, "front/docs_api.html", ctx)

def docs_faq(request):
    """
    Renders the faq page
    """
    all_faqs = Faq.objects.all()
    faqs = list(all_faqs)

    ctx = {
        "page": "docs",
        "section": "faq",
        "SITE_ROOT": settings.SITE_ROOT,
        "PING_ENDPOINT": settings.PING_ENDPOINT,
        "faqs": faqs
    }

    return render(request, "front/docs_faq.html", ctx)


def docs_getting_started(request):
    """
    Renders the getting started page
    """
    all_tutorials = Tutorial.objects.all()
    tutorials = list(all_tutorials)
    # get tutorial titles
    all_tutorial_titles = Tutorial.objects.values_list('title', flat=True).all()
    titles_list = list(all_tutorial_titles)
    ctx = {
        "page": "docs",
        "section": "overview",
        "tutorials": tutorials,
        "titles": titles_list
    }

    return render(request, "front/docs_getting_started.html", ctx)


def about(request):
    return render(request, "front/about.html", {"page": "about"})


@login_required
def add_check(request):
    assert request.method == "POST"

    check = Check(user=request.team.user)
    check.save()

    check.assign_all_channels()

    return redirect("hc-checks")


@login_required
@uuid_or_400
def update_name(request, code):
    assert request.method == "POST"

    check = get_object_or_404(Check, code=code)
    if check.user_id != request.team.user.id:
        return HttpResponseForbidden()

    form = NameTagsForm(request.POST)
    if form.is_valid():
        check.name = form.cleaned_data["name"]
        check.tags = form.cleaned_data["tags"]
        check.save()

    return redirect("hc-checks")


@login_required
@uuid_or_400
def update_priority(request, code):
    """Receives the check priority form and saves check priority to db"""
    assert request.method == 'POST'

    check = get_object_or_404(Check, code=code)
    if check.user != request.team.user:
        return HttpResponseForbidden()

    form = PriorityForm(request.POST)
    if form.is_valid():
        check.priority = form.cleaned_data["priority"]
        check.escalation_email = form.cleaned_data["escalation_email"]
        check.save()
    return redirect("hc-checks")


@login_required
@uuid_or_400
def update_timeout(request, code):
    assert request.method == "POST"

    check = get_object_or_404(Check, code=code)
    if check.user != request.team.user:
        return HttpResponseForbidden()

    form = TimeoutForm(request.POST)
    if form.is_valid():
        check.timeout = td(seconds=form.cleaned_data["timeout"])
        check.grace = td(seconds=form.cleaned_data["grace"])
        check.nag = td(seconds=form.cleaned_data["nag"])
        check.save()

    return redirect("hc-checks")


@login_required
@uuid_or_400
def pause(request, code):
    assert request.method == "POST"

    check = get_object_or_404(Check, code=code)
    if check.user_id != request.team.user.id:
        return HttpResponseForbidden()

    check.status = "paused"
    check.save()

    return redirect("hc-checks")


@login_required
@uuid_or_400
def remove_check(request, code):
    assert request.method == "POST"

    check = get_object_or_404(Check, code=code)
    if check.user != request.team.user:
        return HttpResponseForbidden()

    check.delete()

    return redirect("hc-checks")


@login_required
@uuid_or_400
def log(request, code):
    check = get_object_or_404(Check, code=code)
    if check.user != request.team.user:
        return HttpResponseForbidden()

    limit = request.team.ping_log_limit
    pings = Ping.objects.filter(owner=check).order_by("-id")[:limit]

    pings = list(pings.iterator())
    # oldest-to-newest order will be more convenient for adding
    # "not received" placeholders:
    pings.reverse()

    # Add a dummy ping object at the end. We iterate over *pairs* of pings
    # and don't want to handle a special case of a check with a single ping.
    pings.append(Ping(created=timezone.now()))

    # Now go through pings, calculate time gaps, and decorate
    # the pings list for convenient use in template
    wrapped = []

    early = False
    for older, newer in pairwise(pings):
        wrapped.append({"ping": older, "early": early})

        # Fill in "missed ping" placeholders:
        expected_date = older.created + check.timeout
        n_blanks = 0
        while expected_date + check.grace < newer.created and n_blanks < 10:
            wrapped.append({"placeholder_date": expected_date})
            expected_date = expected_date + check.timeout
            n_blanks += 1

        # Prepare early flag for next ping to come
        early = older.created + check.timeout > newer.created + check.grace

    reached_limit = len(pings) > limit

    wrapped.reverse()
    ctx = {
        "check": check,
        "pings": wrapped,
        "num_pings": len(pings),
        "limit": limit,
        "show_limit_notice": reached_limit and settings.USE_PAYMENTS
    }

    return render(request, "front/log.html", ctx)


@login_required
def channels(request):
    if request.method == "POST":
        code = request.POST["channel"]
        try:
            channel = Channel.objects.get(code=code)
        except Channel.DoesNotExist:
            return HttpResponseBadRequest()
        if channel.user_id != request.team.user.id:
            return HttpResponseForbidden()

        new_checks = []
        for key in request.POST:
            if key.startswith("check-"):
                code = key[6:]
                try:
                    check = Check.objects.get(code=code)
                except Check.DoesNotExist:
                    return HttpResponseBadRequest()
                if check.user_id != request.team.user.id:
                    return HttpResponseForbidden()
                new_checks.append(check)

        channel.checks = new_checks
        return redirect("hc-channels")

    channels = Channel.objects.filter(user=request.team.user).order_by("created")
    channels = channels.annotate(n_checks=Count("checks"))

    num_checks = Check.objects.filter(user=request.team.user).count()

    ctx = {
        "page": "channels",
        "channels": channels,
        "num_checks": num_checks,
        "enable_pushbullet": settings.PUSHBULLET_CLIENT_ID is not None,
        "enable_pushover": settings.PUSHOVER_API_TOKEN is not None
    }
    return render(request, "front/channels.html", ctx)


def do_add_channel(request, data):
    form = AddChannelForm(data)
    if form.is_valid():
        channel = form.save(commit=False)
        channel.user = request.team.user
        channel.save()

        channel.assign_all_checks()

        if channel.kind == "email":
            channel.send_verify_link()

        return redirect("hc-channels")
    else:
        return HttpResponseBadRequest()


@login_required
def add_channel(request):
    assert request.method == "POST"
    return do_add_channel(request, request.POST)


@login_required
@uuid_or_400
def channel_checks(request, code):
    channel = get_object_or_404(Channel, code=code)
    if channel.user_id != request.team.user.id:
        return HttpResponseForbidden()

    assigned = set(channel.checks.values_list('code', flat=True).distinct())
    checks = Check.objects.filter(user=request.team.user).order_by("created")

    ctx = {
        "checks": checks,
        "assigned": assigned,
        "channel": channel
    }

    return render(request, "front/channel_checks.html", ctx)


@uuid_or_400
def verify_email(request, code, token):
    channel = get_object_or_404(Channel, code=code)
    if channel.make_token() == token:
        channel.email_verified = True
        channel.save()
        return render(request, "front/verify_email_success.html")

    return render(request, "bad_link.html")


@login_required
@uuid_or_400
def remove_channel(request, code):
    assert request.method == "POST"

    # user may refresh the page during POST and cause two deletion attempts
    channel = Channel.objects.filter(code=code).first()
    if channel:
        if channel.user != request.team.user:
            return HttpResponseForbidden()
        channel.delete()

    return redirect("hc-channels")


@login_required
def add_email(request):
    ctx = {"page": "channels"}
    return render(request, "integrations/add_email.html", ctx)


@login_required
def add_webhook(request):
    if request.method == "POST":
        form = AddWebhookForm(request.POST)
        if form.is_valid():
            channel = Channel(user=request.team.user, kind="webhook")
            channel.value = form.get_value()
            channel.save()

            channel.assign_all_checks()
            return redirect("hc-channels")
    else:
        form = AddWebhookForm()

    ctx = {"page": "channels", "form": form}
    return render(request, "integrations/add_webhook.html", ctx)


@login_required
def add_pd(request):
    ctx = {"page": "channels"}
    return render(request, "integrations/add_pd.html", ctx)


def add_slack(request):
    if not settings.SLACK_CLIENT_ID and not request.user.is_authenticated:
        return redirect("hc-login")

    ctx = {
        "page": "channels",
        "slack_client_id": settings.SLACK_CLIENT_ID
    }
    return render(request, "integrations/add_slack.html", ctx)


@login_required
def add_slack_btn(request):
    code = request.GET.get("code", "")
    if len(code) < 8:
        return HttpResponseBadRequest()

    result = requests.post("https://slack.com/api/oauth.access", {
        "client_id": settings.SLACK_CLIENT_ID,
        "client_secret": settings.SLACK_CLIENT_SECRET,
        "code": code
    })

    doc = result.json()
    if doc.get("ok"):
        channel = Channel()
        channel.user = request.team.user
        channel.kind = "slack"
        channel.value = result.text
        channel.save()
        channel.assign_all_checks()
        messages.success(request, "The Slack integration has been added!")
    else:
        s = doc.get("error")
        messages.warning(request, "Error message from slack: %s" % s)

    return redirect("hc-channels")


@login_required
def add_hipchat(request):
    ctx = {"page": "channels"}
    return render(request, "integrations/add_hipchat.html", ctx)


@login_required
def add_pushbullet(request):
    if settings.PUSHBULLET_CLIENT_ID is None:
        raise Http404("pushbullet integration is not available")

    if "code" in request.GET:
        code = request.GET.get("code", "")
        if len(code) < 8:
            return HttpResponseBadRequest()

        result = requests.post("https://api.pushbullet.com/oauth2/token", {
            "client_id": settings.PUSHBULLET_CLIENT_ID,
            "client_secret": settings.PUSHBULLET_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code"
        })

        doc = result.json()
        if "access_token" in doc:
            channel = Channel(kind="pushbullet")
            channel.user = request.team.user
            channel.value = doc["access_token"]
            channel.save()
            channel.assign_all_checks()
            messages.success(request,
                             "The Pushbullet integration has been added!")
        else:
            messages.warning(request, "Something went wrong")

        return redirect("hc-channels")

    redirect_uri = settings.SITE_ROOT + reverse("hc-add-pushbullet")
    authorize_url = "https://www.pushbullet.com/authorize?" + urlencode({
        "client_id": settings.PUSHBULLET_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code"
    })

    ctx = {
        "page": "channels",
        "authorize_url": authorize_url
    }
    return render(request, "integrations/add_pushbullet.html", ctx)


@login_required
def add_pushover(request):
    if settings.PUSHOVER_API_TOKEN is None or settings.PUSHOVER_SUBSCRIPTION_URL is None:
        raise Http404("pushover integration is not available")

    if request.method == "POST":
        # Initiate the subscription
        nonce = get_random_string()
        request.session["po_nonce"] = nonce

        failure_url = settings.SITE_ROOT + reverse("hc-channels")
        success_url = settings.SITE_ROOT + reverse("hc-add-pushover") + "?" + urlencode({
            "nonce": nonce,
            "prio": request.POST.get("po_priority", "0"),
        })
        subscription_url = settings.PUSHOVER_SUBSCRIPTION_URL + "?" + urlencode({
            "success": success_url,
            "failure": failure_url,
        })

        return redirect(subscription_url)

    # Handle successful subscriptions
    if "pushover_user_key" in request.GET:
        if "nonce" not in request.GET or "prio" not in request.GET:
            return HttpResponseBadRequest()

        # Validate nonce
        if request.GET["nonce"] != request.session.get("po_nonce"):
            return HttpResponseForbidden()

        # Validate priority
        if request.GET["prio"] not in ("-2", "-1", "0", "1", "2"):
            return HttpResponseBadRequest()

        # All looks well--
        del request.session["po_nonce"]

        if request.GET.get("pushover_unsubscribed") == "1":
            # Unsubscription: delete all Pushover channels for this user
            Channel.objects.filter(user=request.user, kind="po").delete()
            return redirect("hc-channels")
        else:
            # Subscription
            user_key = request.GET["pushover_user_key"]
            priority = int(request.GET["prio"])

            return do_add_channel(request, {
                "kind": "po",
                "value": "%s|%d" % (user_key, priority),
            })

    # Show Integration Settings form
    ctx = {
        "page": "channels",
        "po_retry_delay": td(seconds=settings.PUSHOVER_EMERGENCY_RETRY_DELAY),
        "po_expiration": td(seconds=settings.PUSHOVER_EMERGENCY_EXPIRATION),
    }
    return render(request, "integrations/add_pushover.html", ctx)


@login_required
def add_victorops(request):
    ctx = {"page": "channels"}
    return render(request, "integrations/add_victorops.html", ctx)


def privacy(request):
    return render(request, "front/privacy.html", {})


def terms(request):
    return render(request, "front/terms.html", {})
