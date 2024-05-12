from django.db import models
from django.urls import reverse

from account.models import CustomUser


class Category(models.Model):
    title = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    image = models.ImageField(upload_to='category', null=True)

    def __str__(self):
        return self.title

    def get_url(self):
        return reverse('products:products-list', args=[self.slug])


class Brand(models.Model):
    name = models.CharField(max_length=20)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    image = models.ImageField(upload_to='gallery', null=True, blank=True)
    image1 = models.ImageField(upload_to='gallery', null=True, blank=True)
    image2 = models.ImageField(upload_to='gallery', null=True, blank=True)
    image3 = models.ImageField(upload_to='gallery', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=9, decimal_places=2)
    stock = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.title) + '|' + str(self.brand)

    def get_url(self):
        return reverse('products:category', args=[self.category.slug, self.slug])


class Cart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def item_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return str(self.product.title) + '|' + str(self.user)


class Wishlist(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("product", 'user')

    def __str__(self):
        return str(self.product.title) + '|' + str(self.user)
