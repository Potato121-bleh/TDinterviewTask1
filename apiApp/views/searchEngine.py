import os
import cv2
from apiApp.models import ProductTB
from apiApp.ulti import calculate_histogram
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import request
import numpy


class ImageSearchEngine(APIView):
    def get(self, request: request, *args, **kwargs):

        # handle request image with in form-data format
        try:
            request_img = request.FILES["image"]
        except Exception as e:
            print(e)
            return Response({"Message": "Please assign image in your request with field named: 'image'. "})

        # convert client request into ndarray format for cv2 operation
        image_byte = request_img.read()
        np_array = numpy.frombuffer(image_byte, numpy.uint8)
        cv2_format_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        # calculate the histogram of client image
        user_hist = calculate_histogram(cv2_format_image)

        try:
            # query all image from database for preparation of comparison
            queried_img = list(ProductTB.objects.all().values("image"))       

            # retrieve image from local file and convert them into histogram 
            # and store in a list for later operation
            local_img_hist_list = []        
            for local_img in queried_img:
                prep_img_path = f"./apiApp/static/img/{local_img['image']}"
                if not os.path.exists(prep_img_path):
                    raise Exception(f"{prep_img_path}: img path not found")
                local_img_cv2_format = cv2.imread(prep_img_path)
                local_img_hist = calculate_histogram(local_img_cv2_format)
                
                local_img_hist_list.append(local_img_hist)

            # loop of all local img compared to the user_img in RGB method
            local_img_similarity_score = []
            for local_img_hist in local_img_hist_list:
                rgb_total = 0

                 # we loop 3 times as it was for a list of 3 channel of each histogram image where it RED GREEN BLUE
                for i in range(3): 
                    rgb_score = cv2.compareHist(user_hist[i], local_img_hist[i], cv2.HISTCMP_BHATTACHARYYA)
                    rgb_total += rgb_score

                rgb_score_result = rgb_total / 3
                local_img_similarity_score.append(rgb_score_result)

            # rearrange the data to fit its own image name and sort it as top 10 product most similar with shape and color
            resp_data = []
            for i in range(len(queried_img)):
                prep_dict = {"image": queried_img[i]["image"], "score": local_img_similarity_score[i]}
                resp_data.append(prep_dict)

            for i in range(len(resp_data)):
                for j in range(len(resp_data)):
                    j += i
                    if j == (len(resp_data)):
                        break
                    if resp_data[i]["score"] > resp_data[j]["score"]:
                        resp_data[i], resp_data[j] = resp_data[j], resp_data[i]
    
            top_ten_data = resp_data[:10]
            prep_resp_product = []
            product_storage = list(ProductTB.objects.all().values())
            for top_product in top_ten_data:
                for product in product_storage:
                    if top_product["image"] == product["image"]:
                        prep_resp_product.append(product)
                        break

        except Exception as e:
            print(e)
            return Response({"Message": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"Top-10-Product": prep_resp_product})

