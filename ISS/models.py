from django.db import models
from django.contrib import auth
from django.utils import timezone
from django.core.urlresolvers import reverse

from ISS import utils


class Poster(auth.models.AbstractBaseUser, auth.models.PermissionsMixin):
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [ 'email' ]

    username = models.CharField(max_length=256, unique=True)
    email = models.EmailField()
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = auth.models.UserManager()

    def get_long_name(self):
        return self.username

    def get_short_name(self):
        return self.get_long_name()

    def get_url(self):
        return '/'

    def get_user_title(self):
        return 'Regular'

    def embed_images(self):
        return True

class Forum(models.Model):
    name = models.TextField()
    description = models.TextField()
    priority = models.IntegerField(default=2147483647, null=False)

    def get_thread_count(self):
        return self.thread_set.count()

    def get_post_count(self):
        return Post.objects.filter(thread__forum_id=self.pk).count()

    def get_url(self):
        return reverse('thread-index', kwargs={'forum_id': self.pk})

    def __unicode__(self):
        return self.name

class Thread(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now_add=True)
    locked = models.BooleanField(default=False)

    forum = models.ForeignKey(Forum)
    title = models.TextField()
    log = models.TextField(blank=True)

    _flag_cache = None

    def get_last_post(self):
        return (self.post_set
                    .order_by('-created')
                    .select_related('author'))[0]

    def get_first_post(self):
        return (self.post_set
                    .order_by('created')
                    .select_related('author'))[0]

    def get_author(self):
        return self.get_first_post().author

    def get_post_count(self):
        return self.post_set.count()

    def get_posts_in_thread_order(self):
        return self.post_set.order_by('created')

    def get_url(self, post=None):
        self_url = reverse('thread', kwargs={'thread_id': self.pk})

        if post:
            predecessors = (self.get_posts_in_thread_order()
                .filter(created__lt=post.created)
                .count())

            page_num = predecessors / utils.get_config('posts_per_thread_page')

            self_url += '?p=%d#post-%d' % (page_num + 1, post.pk)

        return self_url

    def can_reply(self):
        return not self.locked

    def _get_flag(self, user, save=True):
        if not self._flag_cache:
            self._flag_cache, created = ThreadFlag.objects.get_or_create(
                poster=user,
                thread=self)

            if created and save:
                self._flag_cache.save()

        return self._flag_cache

    def has_unread_posts(self, user):
        flag = self._get_flag(user)

        if not flag.last_read_date or flag.last_read_date < self.last_update:
            return True
        else:
            return False

    def mark_read(self, user, post=None):
        flag = self._get_flag(user, save=False)

        if post is None:
            post = self.get_last_post()

        flag.last_read_post = post
        flag.last_read_date = post.created

        flag.save()

    def subscribe(self, user):
        flag = self._get_flag(user, save=False)
        flag.subscribed = False

        flag.save()

    def __unicode__(self):
        return self.title

class Post(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    thread = models.ForeignKey(Thread)
    content = models.TextField()
    author = models.ForeignKey(Poster)

    def quote_content(self):
        return '[quote]%s[/quote]' % self.content

    def get_url(self):
        return self.thread.get_url(self)

class Thanks(models.Model):
    given = models.DateTimeField(auto_now_add=True)

    thanker = models.ForeignKey(Poster, related_name='thanks_given')
    thankee = models.ForeignKey(Poster, related_name='thanks_received')
    post = models.ForeignKey(Post)

class ThreadFlag(models.Model):
    class Meta:
        unique_together = ('thread', 'poster')

    thread = models.ForeignKey(Thread)
    poster = models.ForeignKey(Poster)

    last_read_post = models.ForeignKey(Post, null=True)
    last_read_date = models.DateTimeField(null=True)
    subscribed = models.BooleanField(default=False)

def update_thread_last_update(sender, instance, created, **kwargs):
    if not created:
        # Edits don't bump threads.
        return

    thread = instance.thread

    if thread.last_update < instance.created:
        thread.last_update = instance.created
        thread.save()

models.signals.post_save.connect(update_thread_last_update, sender=Post)
