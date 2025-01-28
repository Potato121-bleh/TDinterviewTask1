from django.db import models

class CategoryTB(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"CategoryTB(id: {self.id}, name: {self.name})"


class ProductTB(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    image = models.CharField(max_length=50)
    price = models.FloatField()
    Cat = models.ForeignKey("CategoryTB", on_delete=models.CASCADE, related_name="products")

    def __str__(self):
        return f"ProductTB(id: {self.id}, name: {self.name}, image: {self.image}, price: {self.image}, Cat_id: {self.Cat_id})"


