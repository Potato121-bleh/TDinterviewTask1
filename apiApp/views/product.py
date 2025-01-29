from apiApp.ulti import sql_update_builder, sql_insert_builder
from apiApp.models import ProductTB
from django.db import connection, transaction
from django.db.backends.utils import CursorWrapper
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import request

def query_constructor(db_c: CursorWrapper, query_sql_statement, params, field=""):
    """
    This method allow you to construct the sql statement and perform the execution and return as list of turple of data

    @ Parameters: 
                    `db_c`: CursorWrapper   :   coming from connection.cursor() \n
                    `query_sql_statement`: str  : which already built by previous builder \n
                    `params` : dict[str, any]   : coming from request.data \n
                    `field` : str   : to determine what field the constructor should working on \n

    @ return: `list[tuple[Any, ...]]`


    NOTE: This method are used only in GET Request in product only! it not dynamically built for other get request

    .
    """
    if not field == "":
        query_sql_statement += f" WHERE apiApp_producttb.{field} = %s"
        db_c.execute(query_sql_statement, [params.get(field)])
    else:
        db_c.execute(query_sql_statement)
    return db_c.fetchall()

class ProductView(APIView):
    def get(self, request: request, *args, **kwargs):
        params = request.query_params

        # query column of producttb to determine the field, for dynamically operation
        product_sample = ProductTB.objects.all().values()[0]
        available_key = list(product_sample.keys())
        query_sql_statement = "SELECT "

        # FROM apiApp_producttb INNER JOIN apiApp_categorytb ON apiApp_producttb.Cat_id = apiApp_categorytb.id WHERE "
        for i in range(len(available_key)):
            if i == (len(available_key) - 1):
                query_sql_statement += f" apiApp_categorytb.name AS 'cate' "
            else:
                query_sql_statement += f" apiApp_producttb.{available_key[i]} , "
        
        query_sql_statement += "FROM apiApp_producttb INNER JOIN apiApp_categorytb ON apiApp_producttb.Cat_id = apiApp_categorytb.id "

        try:
            with connection.cursor() as db_c:
                if params.get("id"):
                    queried_data = query_constructor(db_c, query_sql_statement, params, "id")

                elif params.get("name"):
                    queried_data = query_constructor(db_c, query_sql_statement, params, "name")

                elif params.get("image"):
                    queried_data = query_constructor(db_c, query_sql_statement, params, "image")
                    
                else:
                    queried_data = queried_data = query_constructor(db_c, query_sql_statement, params)
            
            # construct new response data
            response_dataset = []

            # change original field to fit the need
            available_key[-1] = "cate"
            for element in queried_data:
                prep_dataset = dict(zip(available_key, element))
                response_dataset.append(prep_dataset)

            
        except Exception as e:
            print(e)
            return Response({"Message": "Something went wrong with database query, Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"Message": response_dataset})

    def post(self, request: request, *args, **kwargs):
        request_data = request.POST
        try:
            request_image  = request.FILES["image"]
        except Exception as e:
            print(e)
            return Response({"Message": "Please assign product image file with field named: 'image'. "}, status=status.HTTP_400_BAD_REQUEST)

        insert_statement = sql_insert_builder(ProductTB, request_data, "image")
        if insert_statement == None:
            return Response({"Message": "Something went wrong, Make you include all correct field."}, status=status.HTTP_400_BAD_REQUEST)
        
        if request_image is None:
            return Response({"Message": "Please include a product image with field named 'image' in png format."}, status=status.HTTP_400_BAD_REQUEST)

        image_format_name = request_image.name.split(".")[-1]
        if image_format_name != "png":
            return Response({"Message": "Please make sure your image in png format."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction.set_autocommit(autocommit=False)
            with connection.cursor() as db_c:
                db_c.execute(insert_statement)
                if db_c.rowcount != 1:
                    raise Exception("Unexpected behavior from database, from insert")
                
                # Since the commit hasn't been commit we still get the recent id from recently added data
                db_c.execute("SELECT id FROM apiApp_producttb ORDER BY id DESC LIMIT 1")
                queried_product_id_arr = db_c.fetchall()[0][0]


                # Update the empty image field
                db_c.execute("UPDATE apiApp_producttb SET image = %s WHERE id = %s", [f"{queried_product_id_arr}.png", queried_product_id_arr])
                if db_c.rowcount != 1:
                    raise Exception("Unexpected behavior from database, from update")
                
                
                fs = FileSystemStorage(location="./apiApp/static/img")
                fs.save(f"{queried_product_id_arr}.png", request_image)

                transaction.commit()
        except Exception as e: 
            transaction.rollback()
            print(e)
            return Response({"Message": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        transaction.set_autocommit(autocommit=True)
        return Response({"Message": "Product has created"})
    
    def patch(self, request: request, *args, **kwargs):
        params = request.query_params
        request_data = request.data 
        if not params.get("id"):
            return Response({"Message": "Please assign the id into url params"}, status=status.HTTP_400_BAD_REQUEST)

        origin_data = ProductTB.objects.filter(id=params.get("id")).values()
        if not origin_data.exists():
            return Response({"Message":"No product found"}, status=status.HTTP_400_BAD_REQUEST)

        try: 
            update_statement = sql_update_builder(ProductTB, request_data, origin_data[0])
            if update_statement is None:
                raise Exception("failed to create update statement, Please try again")
            
            transaction.set_autocommit(autocommit=False)

            with connection.cursor() as db_c:
                db_c.execute(update_statement)
                if db_c.rowcount != 1:
                    raise Exception("Unexpected behavior from database")
                transaction.commit()
        except Exception as e:
            transaction.rollback()
            print(e)
            return Response({"Message": "Something went wrong, Please make sure you insert the correct field."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        transaction.set_autocommit(autocommit=True)
        return Response({"Message": "Product Updated Successfully"})

    def delete(self, request: request, *args, **kwargs):
        request_data = request.data 
        if not request_data.get("id"):
            return Response({"Message": "Please make sure the request body include the id you want to delete"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction.set_autocommit(autocommit=False)
            with connection.cursor() as db_c:
                db_c.execute("DELETE FROM apiApp_producttb WHERE id = %s", [request_data.get("id")])
                if db_c.rowcount != 1:
                    raise Exception("Unexpected behavior from database")
                
                fs = FileSystemStorage(location="./apiApp/static/img")
                if fs.exists(f"{request_data.get("id")}.png"):
                    fs.delete(f"{request_data.get("id")}.png")
                else: 
                    raise Exception("Image not found in local storage")

                transaction.commit()
        except Exception as e:
            transaction.rollback()
            print(e)
            return Response({"Message": "Something went wrong, Please make sure you assign only Id field in request body to perform deletion"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
               
        transaction.set_autocommit(autocommit=True)
        return Response({"Message": "Product has been Deleted"})

