from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from http import HTTPStatus


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Prints response type in terminal
    # print('response', response)

    # Checks whether a response is present
    if response is not None:
      # map all the status codes and descriptions in the dictionary
        http_code_to_message = {v.value: v.description for v in HTTPStatus}

        # defines the format of the error
        error_payload = {
            "error": {
                "status_code": 0,
                "message": "",
                "details": []
            }
        }

        error = error_payload["error"]
        status_code = response.status_code

        # Assigning values to the error dictionary
        error["status_code"] = status_code
        error["message"] = http_code_to_message[status_code]
        error["details"] = response.data

        # Making the response the error payload
        response.data = error_payload

        return response
    # else:
    #     error = {
    #         "error": "Something went wrong. Please try again later."
    #     }
    #     return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
