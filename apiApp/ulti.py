from django.db import models
import numpy
from .models import ProductTB, CategoryTB
from django.db import transaction
from django.http import QueryDict


def user_data_request_validation(dict_one: dict, dict_two: dict, except_field=""):
    """
    This method provide a easy way to compare the two list whether the `first dict` element exist in `second dict` or not
    if not, then it'll return `False` indicate any unexpected element inside of first dict.
    """
    if len(dict_one) == 0:
        return False
    for i in dict_one:
        trigger_flag = False
        if i == except_field:
            continue
        for j in dict_two:
            if i == j:
                trigger_flag = True
                break
        if not trigger_flag:
            return False
    return True

def handle_category_json_format(category_data):
    """
    This function allow you to query all of category product and format them into json format ready to response.
    this function accept the category list of QuerySet that already queried from database.

    @ return: `list[ dict[Any, Any] ]`

    .
    """
    category_list = []
    for category_element in category_data:
        related_product = ProductTB.objects.filter(Cat_id=category_element["id"]).values()
        prep_data_dict = {"id": category_element["id"], "name": category_element["name"], "products": related_product}
        category_list.append(prep_data_dict)
    return category_list

def sql_update_builder(model: models.Model, client_data: dict, origin_data: dict):
    """
    This function design to handle the patching process of the incoming data & original data, By this function
    it allow user to pass only the field they want to update and perform some validation to make sure the request data 
    are cleaned before prepare the sql statement. 

    @ Return:      `SQL Statement` | `None`

    .
    """
    
    available_field = list(origin_data.keys())
    client_field = list(client_data.keys())
    data_id = origin_data["id"]
    del available_field[0]

    #validation whether the incoming data are fitted into the origin data or not if not throw an error
    user_request_validate_result = user_data_request_validation(dict_one=client_field, dict_two=available_field)
    if not user_request_validate_result:
        return None

    patch_sql_statement = f"UPDATE apiApp_{model._meta.model_name} SET "
    for origin_field in available_field:
        if not client_data.get(origin_field) == None:
            patch_sql_statement += f"{origin_field} = '{client_data.get(origin_field)}' ,"
        else:
            patch_sql_statement += f"{origin_field} = '{origin_data[origin_field]}' ,"
    patch_sql_statement_list = patch_sql_statement.split(" ")
    patch_sql_statement_list.pop()
    patch_sql_statement_formatted = " ".join(patch_sql_statement_list)
    patch_sql_statement_formatted += f" WHERE id = {data_id}"
    
    
    return patch_sql_statement_formatted

def sql_insert_builder(model: models.Model, client_data: dict, except_field=""):
    """
    This method allow user to be able to build their own insert sql statement. It talking in the model as u passed in to determine which table user working with
    and then it take the incoming request as type `dict` to do validation to determine that the incoming data have field that met the existing field in database or not.
    if not it return an `None` and if validation is work, it start perform the data patching and return SQL Statement ready for database interaction.

    @ return str(SQL Statement) | None

    NOTE: During validation, validator will check all of exist field in client_request data but if you have any field you want the validator to skip as it not for assign into database script
    Please make sure to assign the field you want to skip in `except_field` on 3rd argument of this method.

    .
    """
    try:
        if isinstance(client_data, QueryDict):
            clean_client_data = client_data.dict()
        else:
            clean_client_data = client_data
        
        sample_data = model.objects.all().values()[0]
        available_field = list(sample_data.keys())
        client_field = list(clean_client_data.keys())

        del available_field[0]
        if except_field:
            clean_client_data[except_field] = ""

        if except_field:
            user_request_validation = user_data_request_validation(dict_one=available_field, dict_two=client_field, except_field=except_field)
        else:
            user_request_validation = user_data_request_validation(dict_one=available_field, dict_two=client_field)
            print(available_field)
            print(client_field)
        if not user_request_validation:
            return None
        
        #construct the sql statement
        sql_insert_statement = f"INSERT INTO apiApp_{model._meta.model_name} ("
        for i in available_field:
            if i == available_field[-1]:
                sql_insert_statement += f" {i} "
                continue
            sql_insert_statement += f" {i} , "
            
        sql_insert_statement += " ) VALUES ("

        for i in available_field:
            # valiation make sure it on correct type 
            # because some database doesn't auto format datatype
            if isinstance(clean_client_data[i], int) or isinstance(clean_client_data[i], float):
                sql_insert_statement += f" {clean_client_data[i]} ,"
                continue
            sql_insert_statement += f" '{clean_client_data[i]}' ,"
        
        #format the sql statement
        sql_insert_statement_list = sql_insert_statement.split(" ")
        sql_insert_statement_list.pop()
        sql_insert_statement_formatted = " ".join(sql_insert_statement_list)
        sql_insert_statement_formatted += ")"
        print(sql_insert_statement_formatted)

    except Exception as e:
        print(e)
        return None

    return sql_insert_statement_formatted

def calculate_histogram(formatted_image: numpy.ndarray):
    """
    This method allow us to calculate the image into histogram where it accept an formatted image in `numpy.ndarray` to met the need of cv2 library
    that image then will split into 3 channels which is RED GREEN BLUE for calculation due to it accuracy and similarity.

    @ return: `List[List[hist]]`

         Overall, the return value is a 2D lists. since all images are not in a single histogram 
         they are divide into 3 channels of RGB which is why the return list is a list of each image channel.

    .
    """
    image_channel = cv2.split(formatted_image)
    histogram_channel = []
    for channel in image_channel:
        hist = cv2.calcHist([channel], [0], None, [256], [0, 256])
        hist_normalized = cv2.normalize(hist, hist).flatten()
        histogram_channel.append(hist_normalized)
    return histogram_channel


