from apiApp.ulti import handle_category_json_format, sql_update_builder, user_data_request_validation, sql_insert_builder
from apiApp.models import CategoryTB
from django.db import connection, transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import request



class CategoryView(APIView):
    def get(self, request: request, *args, **kwargs):
        try:
            query_param = request.query_params
            print(query_param)
            if query_param.get("id"):
                selected_id = query_param.get("id")
                category_data = CategoryTB.objects.filter(id=selected_id).values()
            elif query_param.get("name"):
                selected_name = query_param.get("name")
                category_data = CategoryTB.objects.filter(name=selected_name).values()
            else:
                category_data = CategoryTB.objects.all().values()

            if len(category_data) == 0:
                raise Exception("No Category found")
            
            category_formatted = handle_category_json_format(category_data)
            

        except Exception as e:
            print(e)
            return Response({"Message": "Validation failed, Please try again later"}, status=400)
        return Response({"Message": category_formatted}, status=status.HTTP_200_OK)
    
    def post(self, request: request, *args, **kwargs):
        request_data = dict(request.data)
        if len(request_data) != 1 or request_data.get("name") is None:
            return Response({"Message": "failed to create new category, Please input only one field: 'categoryName'"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction.set_autocommit(autocommit=False)
            with connection.cursor() as db_c:
                sql_insert_statement = sql_insert_builder(CategoryTB, request_data)
                if sql_insert_statement == None:
                    return Response({"Message": "Something went wrong, Make you include all correct field."}, status=status.HTTP_400_BAD_REQUEST)
                db_c.execute(sql_insert_statement)
                row_affected = db_c.rowcount
                if row_affected != 1:
                    transaction.rollback()
                    raise Exception("Unexpected behavior from database, Please try again")
                
                transaction.commit()
        except Exception as e:
            print(e)
            transaction.rollback()
            return Response({"Message": "Something went wrong, Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        transaction.set_autocommit(autocommit=True)
        return Response({"Message": "Category Created Successfully"})

    def patch(self, request: request, *args, **kwargs):
        query_params = request.query_params
        request_data = request.data
        if not query_params.get("id"):
            return Response({"Message": "please assign the category Id for any update"}, status=status.HTTP_400_BAD_REQUEST)
    
        selected_id = query_params.get("id")

        try:
            transaction.set_autocommit(autocommit=False)

            queried_dataset = CategoryTB.objects.filter(id=selected_id).values()
            if not len(queried_dataset) == 1:
                raise Exception("User not found")

            #patched_dataset = 
            patch_sql_statement = sql_update_builder( CategoryTB, client_data=request_data, origin_data=queried_dataset[0])
            
            if patch_sql_statement == None:
                raise Exception("Something went Wrong, Please assign at least 1 field to perform updation and make sure you type the correct field")
            
            with connection.cursor() as db_c:
                db_c.execute(patch_sql_statement)
                update_row_affected = db_c.rowcount
                if not update_row_affected == 1:
                    transaction.rollback()
                    raise Exception("Unexpected behavior from database")
                transaction.commit()
        except Exception as e:
            transaction.rollback()
            print(e)
            return Response({"Message": "failed to update, Please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        transaction.set_autocommit(autocommit=True)
        return Response({"Message": "Updated successfully"})

    def delete(self, request: request, *args, **kwargs):
        request_data = request.data 
        if request_data["id"] == None:
            Response({"Message": "Please assign only a single 'id' field."})
        
        try:
            transaction.set_autocommit(autocommit=False)
            with connection.cursor() as db_c:
                db_c.execute("DELETE FROM apiApp_categorytb WHERE id = %s", [request_data["id"]])

                if db_c.rowcount != 1:
                    transaction.rollback()
                    raise Exception("Unexcepted behavior from database")

            transaction.commit()
        except Exception as e:
            transaction.rollback()
            print(e)
            return Response({"Message": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        transaction.set_autocommit(autocommit=True)
        return Response({"Message": "Category Deleted Successfully"})
