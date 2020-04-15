from .engine import Engine
from django.template import Context, Template
# from django.shortcuts import render, HttpResponse
from django.http import HttpResponse
from .models import LocieStoreSite
from django.views import View

class LocieStoreHomeView(View):
    def get(self,request):
        uname = request.get_host().split(".")[0]
        locie_store = LocieStoreSite.objects.get(uname=uname)
        print(request.path)
        # rendered = Engine().render()
        context = {}
        if locie_store.site_context:
            context = Context(locie_store.site_context['index'])
        # data = locie_store.site['index']
        rendered = str(Engine().render(locie_store.site))
        template = Template(rendered).render(context)
        return HttpResponse(template)


class LocieStorePageView(View):
    def get(self,request,obees):
        uname = request.get_host().split(".")[0]
        # print(obees)
        locie_store = LocieStoreSite.objects.get(uname=uname)
        context = {}
        if locie_store.site_context:
            context = Context(locie_store.site_context[obees])
        rendered = Engine().render(locie_store.site,page_name=obees)
        template = Template(rendered).render(context)
        return HttpResponse(template)


