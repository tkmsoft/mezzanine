
from copy import deepcopy

from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from mezzanine.pages.models import Page, ContentPage
from mezzanine.core.admin import DisplayableAdmin


page_fieldsets = deepcopy(DisplayableAdmin.fieldsets)
page_fieldsets[0][1]["fields"] += (("in_navigation", "in_footer"), 
    "login_required",)


class PageAdmin(DisplayableAdmin):
    """
    Admin class for the ``Page`` model and all subclasses of ``Page``. Handles
    redirections between admin interfaces for the ``Page`` model and its
    subclasses.
    """
    
    fieldsets = page_fieldsets
    
    def in_menu(self):
        """
        Hide subclasses from the admin menu.
        """
        return self.model is Page
    
    def add_view(self, request, **kwargs):
        """
        For the ``Page`` model, redirect to the add view for the 
        ``ContentPage`` model.
        """
        if self.model is Page:
            app = ContentPage._meta.app_label
            name = ContentPage.__name__.lower()
            add_url = reverse("admin:%s_%s_add" % (app, name))
            return HttpResponseRedirect(add_url)
        return super(PageAdmin, self).add_view(request, **kwargs)

    def change_view(self, request, object_id, extra_context=None):
        """
        For the ``Page`` model, check ``page.get_content_model()`` for a
        subclass and redirect to its admin change view.
        """
        if self.model is Page:
            page = get_object_or_404(Page, pk=object_id)
            content_model = page.get_content_model()
            if content_model is not None:
                app = content_model.__class__._meta.app_label
                name = content_model.__class__.__name__.lower()
                change_url = reverse("admin:%s_%s_change" % (app, name),
                    args=(content_model.id,))
                return HttpResponseRedirect(change_url)
        return super(PageAdmin, self).change_view(request, object_id,
            extra_context=None)

    def changelist_view(self, request, extra_context=None):
        """
        Redirect to the ``Page`` changelist view for ``Page`` subclasses.
        """
        if self.model is not Page:
            return HttpResponseRedirect(reverse("admin:pages_page_changelist"))
        return super(PageAdmin, self).changelist_view(request, extra_context)

    def save_model(self, request, obj, form, change):
        """
        Set the ID of the parent page if passed in via querystring.
        """
        # Force parent to be saved to trigger handling of ordering and slugs.
        parent = request.GET.get("parent")
        if parent is not None and not change:
            obj.parent_id = parent
            obj._order = None
            obj.slug = None
            obj.save()
        super(PageAdmin, self).save_model(request, obj, form, change)

    def _maintain_parent(self, request, response):
        """
        Maintain the parent ID in the querystring for response_add and
        response_change.
        """
        location = response._headers["location"][1]
        parent = request.GET.get("parent")
        if parent is not None and "?" not in location:
            location += "?parent=%s" % parent
        return HttpResponseRedirect(location)

    def response_add(self, request, obj):
        """
        Maintain the parent ID in the querystring.
        """
        response = super(PageAdmin, self).response_add(request, obj)
        return self._maintain_parent(request, response)

    def response_change(self, request, obj):
        """
        Maintain the parent ID in the querystring.
        """
        response = super(PageAdmin, self).response_change(request, obj)
        return self._maintain_parent(request, response)


content_page_fieldsets = deepcopy(PageAdmin.fieldsets)
content_page_fieldsets[0][1]["fields"].insert(3, "content")

class ContentPageAdmin(PageAdmin):
    """
    Admin class for the ContentPage default content type.
    """
    fieldsets = content_page_fieldsets


admin.site.register(Page, PageAdmin)
admin.site.register(ContentPage, ContentPageAdmin)
