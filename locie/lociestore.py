from .engine import Engine
from django.template import Context, Template
# from django.shortcuts import render, HttpResponse
from django.http import HttpResponse
from .models import LocieStoreSite,Publytics
from django.views import View
from rest_framework.views import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny


class LocieStoreHomeView(View):
    def get(self, request):
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
    def get(self, request, obees):
        uname = request.get_host().split(".")[0]
        # print(obees)
        locie_store = LocieStoreSite.objects.get(uname=uname)
        context = {}
        if locie_store.site_context:
            context = Context(locie_store.site_context[obees])
        rendered = Engine().render(locie_store.site, page_name=obees)
        template = Template(rendered).render(context)
        return HttpResponse(template)


"""
  - API View to meter the views of a site
  - ajax will send uname after which we have to increas the view countof that sitein LocieStore Site
"""

class ViewMeter(APIView):
    permission_classes = [AllowAny]

    def get(self,request,format=None):
        publytics = Publytics.objects.filter(site_uname=request.GET['uname'])
        if publytics:
            publytics = publytics.first()
            publytics.views_log[request.GET['date']] += 1
            publytics.save()
            return Response({},status=status.HTTP_200_OK)
        else:
            return Response({},status=status.HTTP_200_OK)

