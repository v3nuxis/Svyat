from django import forms
from django.shortcuts import redirect, render
from django.views.generic.edit import FormView
from rest_framework import generics, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["name"]


# def index(request):
#     tasks = Task.objects.all()
#     form = TaskForm()

#     if request.method == "POST":
#         form = TaskForm(request.POST)

#         if form.is_valid():
#             form.save()
#             return redirect("index")

#     return render(request, "index.html", {"form": form, "tasks": tasks})


# class Index(FormView):
#     template_name = "index.html"
#     form_class = TaskForm
#     success_url = "index"


class TaskSerializser(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "name"]


# @api_view(["GET", "POST"])
# def index(request):
#     if request.method == "GET":
#         tasks = Task.objects.all()
#         serializer = TaskSerializser(tasks, many=True)

#         return Response(serializer.data)
#     else:
#         serializer = TaskSerializser(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=201)


class Index(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializser
