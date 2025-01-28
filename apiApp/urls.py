from django.urls import path
from . import views


urlpatterns = [
    path("category/", views.CategoryView.as_view(), name="category"),
    path("product/", views.ProductView.as_view(), name="product"),
    path("search-img/", views.ImageSearchEngine.as_view(), name="image-search-engine")
]