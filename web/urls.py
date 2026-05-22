"""web/urls.py — URL routes for the GenAI Document Agent."""

from django.urls import path
from . import views

urlpatterns = [
    path("",                    views.index,              name="index"),
    path("job-search/",         views.job_search,         name="job_search"),
    path("resume-optimizer/",   views.resume_optimizer,   name="resume_optimizer"),
    path("download/<str:kind>/", views.download_pdf,      name="download_pdf"),
]
