import base64
import json

import falcon
from zeep import Client, xsd
from zeep.cache import SqliteCache
from zeep.helpers import serialize_object
from zeep.transports import Transport

from reference import (ERRORS_CREATE_SHIPMENT, IDENTIFIER_INVOICE_ID,
                       IDENTIFIER_SHIPMENT_ID, PROD_WSDL_URL, SUCCESSFUL,
                       TEST_WSDL_URL)
from utilities import (extract_credentials, generate_zpl_label,
                       parameter_as_list, parse_shipment, unpack_phone_numbers)

transport = Transport(cache=SqliteCache())

test_client = Client(TEST_WSDL_URL, transport=transport)
test_factory = test_client.type_factory("ns1")
prod_client = Client(PROD_WSDL_URL, transport=transport)
prod_factory = prod_client.type_factory("ns0")

class AuthMiddleware(object):
    """
    Extracts credentials from the HTTP Basic authentication header 
    and makes them available to functions further down the line.
    """
    def process_request(self, req, resp):
        try:
            parsed_auth = req.auth.split(" ")
        except AttributeError:
            raise falcon.HTTPUnauthorized(title="401 Unauthorized",
                                          description="The provided credentials are not valid")
        else:
            if len(parsed_auth) == 2 and parsed_auth[0] == "Basic":
                req.context["username"], req.context["password"] = extract_credentials(parsed_auth[1])
            else:
                raise falcon.HTTPUnauthorized(title="401 Unauthorized",
                                            description="The provided credentials are not valid")

class EnvironmentMiddleware(object):
    """
    Extracts environment information from the request and sets the
    API endpoint based on it. 
    """
    def process_request(self, req, resp):
        if (req.context["username"] == "YKTEST" 
                or req.params.get("environment", None) == "test"):
            req.context["client"] = test_client
            req.context["factory"] = test_factory

        else:
            req.context["client"] = prod_client
            req.context["factory"] = prod_factory

class LocaleMiddleware(object):
    """
    Sets locale for error messages.
    """
    def process_request(self, req, resp):
        # NOT IMPLEMENTED
        pass

class FormatMiddleware(object):
    """
    Determines response formatting.
    """

    def process_request(self, req, resp):
        req.context["formatted"] = req.get_param_as_bool("formatted", default=False)

class Shipment(object):
    """

    """
    def on_post(self, req, resp):
        """
        createShipment
        """
        body = json.load(req.bounded_stream)
        shipments = []
        resp_obj = {
            "successful": [],
            "failed": [],
        }
        for shipment in parameter_as_list(body):
            soap_object = req.context["factory"].ShippingOrderVO(
                **parse_shipment(req, shipment)
            )
            shipments.append(soap_object)


        query = req.context["client"].service.createShipment(
            wsUserName=req.context["username"],
            wsPassword=req.context["password"],
            userLanguage="TR", # Fixed value
            ShippingOrderVO=shipments,
        )
        yk_resp = serialize_object(query, target_cls=dict)

        if yk_resp["outFlag"] == "0":
            shipments_by_key = { _["cargoKey"]: serialize_object(_, target_cls=dict) for _ in shipments }
            response_by_key = { _["cargoKey"]: _ for _ in yk_resp["shippingOrderDetailVO"] }
            resp_obj["outFlag"] = str(yk_resp["outFlag"])
            resp_obj["count"] = yk_resp["count"]
            resp_obj["jobId"] = yk_resp["jobId"]
            # strip SkipValues
            for skey, shipment in shipments_by_key.items():
                for ikey, ival in shipment.items():
                    if ival == xsd.SkipValue:
                        shipments_by_key[skey][ikey] = ""

            for skey, shipment  in response_by_key.items():
                # if there aren't any errors
                if shipment["errCode"] is None:
                    # generate label and add to the main shipment object
                    shipments_by_key[shipment["cargoKey"]]["label"] = generate_zpl_label(
                        shipments_by_key[shipment["cargoKey"]], str(yk_resp["jobId"]))
                    resp_obj["successful"].append(shipments_by_key[shipment["cargoKey"]])
                else:
                    # add data from the response object to the main shipment object
                    shipments_by_key[shipment["cargoKey"]]["errCode"] = shipment["errCode"]
                    shipments_by_key[shipment["cargoKey"]]["errMessage"] = shipment["errMessage"]
                    resp_obj["failed"].append(shipments_by_key[shipment["cargoKey"]])
            resp.status = falcon.HTTP_OK
            resp.body = json.dumps(resp_obj)
        elif yk_resp["outFlag"] == "1":
            resp.status = falcon.HTTP_500
            resp.body = json.dumps(yk_resp)

    def on_get(self, req, resp):
        """
        queryShipment
        """
        shipment_id = req.get_param_as_list("shipment_id", None)
        invoice_id = req.get_param_as_list("invoice_id", None)
        add_historical_data = req.get_param_as_bool("add_historical_data", default=True)
        tracking_url_only = req.get_param_as_bool("tracking_url_only", default=False)

        response_content = {}

        if not any((shipment_id, invoice_id)):
            raise falcon.HTTPBadRequest(title="400 Bad Request",
                                        description="No identifier was provided")

        if shipment_id is not None:
            query_by_shipment_id = req.context["client"].service.queryShipment(
                wsUserName=req.context["username"],
                wsPassword=req.context["password"],
                wsLanguage="TR", # Fixed value
                keys=shipment_id,
                keyType=IDENTIFIER_SHIPMENT_ID,
                addHistoricalData=add_historical_data,
                onlyTracking=tracking_url_only,
            )
            # Error handling is not implemented yet
            if query_by_shipment_id.outFlag == SUCCESSFUL:
                response_content = serialize_object(query_by_shipment_id, target_cls=dict)

        if invoice_id is not None:
            query_by_invoice_id = req.context["client"].service.queryShipment(
                wsUserName=req.context["username"],
                wsPassword=req.context["password"],
                wsLanguage="TR", # Fixed value
                keys=invoice_id,
                keyType=IDENTIFIER_INVOICE_ID,
                addHistoricalData=add_historical_data,
                onlyTracking=tracking_url_only,
            )
            # Error handling is not implemented yet
            if query_by_invoice_id.outFlag == SUCCESSFUL:
                if response_content == {}:
                    response_content = serialize_object(query_by_invoice_id, target_cls=dict)
                else:
                    response_content["count"] += query_by_invoice_id.count
                    response_content["shippingDeliveryDetailVO"].extend(
                        serialize_object(query_by_invoice_id, target_cls=dict)["shippingDeliveryDetailVO"])

        resp.status = falcon.HTTP_OK
        resp.body = json.dumps(response_content)

    def on_delete(self, req, resp):
        """
        cancelShipment
        """
        # NOT IMPLEMENTED
        pass





shipment = Shipment()

app = falcon.API(
    media_type="application/json",
    middleware=[
        AuthMiddleware(),
        FormatMiddleware(),
        EnvironmentMiddleware(),
    ],
)

app.req_options.auto_parse_form_urlencoded = True

app.add_route("/yk/shipments", shipment)
