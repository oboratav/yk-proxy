import base64
from datetime import datetime

from benedict import benedict
from zeep import xsd

from reference import SENDER_NAME, SENDER_TELEPHONE


def extract_credentials(encoded_string: str) -> tuple:
    """
    Given the base64-encoded part of the authentication header, 
    decodes and separates the username and password.
    """
    decoded = base64.b64decode(encoded_string).decode("utf-8").split(":")
    return (decoded[0], decoded[1])

def parameter_as_list(parameter) -> list:
    """
    If the parameter object is a list, return it as is. If it's a 
    string or dictionary, return it enveloped in a list.
    """
    if type(parameter) == list:
        return parameter
    elif type(parameter) in (str, dict):
        return [parameter]

def generate_special_field(shipment_object=None, **kwargs) -> str:
    """
    Given a set of keyword arguments, generates the specialField1 string 
    for a shipment.
    """
    fields = {
        "customer_serial_number": "2",
        "order_number": "3",
        "bag_number": "4",
        "packaging_number": "5",
        "customer_national_id": "6",
        "customer_full_name": "7",
        "region": "8",
        "department_or_employee_id": "9",
        "mobile_phone": "10",
        "policy_number": "11",
        "cost_center": "12",
        "product": "13",
        "customer_reference": "14",
        "rma_number": "16",
        "magazine_type": "51",
        "representative_id": "52",
        "waybill_number": "54",
        "recipient_vat_id": "55",
        "representative_team_lead_id": "56",
    }
    field = ""
    if shipment_object is not None:
        for field_name, field_code in fields.items():
            field += "{}${}#".format(field_code, shipment_object.get(field_name, "")) if field_name in shipment_object else ""
        return field if field != "" else xsd.SkipValue
    else:
        for field_name, field_code in fields.items():
            field += "{}${}#".format(field_code, kwargs.get(field_name, "")) if field_name in kwargs else ""
        return field if field != "" else xsd.SkipValue

def unpack_phone_numbers(req, shipment: dict) -> dict:
    """
    Unpacks a list of phone numbers
    """
    if req.context["formatted"]:
        numbers = parameter_as_list(shipment["to_address"].get("phone"))
        # TODO: Implement this for multiple numbers
        if len(numbers) >= 1:
            return {
                "receiverPhone1": numbers[0],
                "receiverPhone2": xsd.SkipValue,
                "receiverPhone3": xsd.SkipValue,
            }
    else:
        return {
            "receiverPhone1": shipment.get("receiverPhone1", xsd.SkipValue),
            "receiverPhone2": shipment.get("receiverPhone2", xsd.SkipValue),
            "receiverPhone3": shipment.get("receiverPhone3", xsd.SkipValue),
        }

def prettify_phone_number(number):
    return "({}) {} {} {}".format(number[0:3], number[3:6], number[6:8], number[8:10])

def read_formatted_address(req, shipment: dict) -> dict:
    """
    Unpacks a two-line address into a YK-formatted, single-line one.
    """
    pass

def parse_shipment(req, shipment: dict) -> dict:
    """
    Parses a request and prepares a formatted shipment object for
    further use.
    """
    param_keys = {
        "cargoKey": ("cargoKey", "shipment_id"),
        "invoiceKey": ("invoiceKey", "invoice_id"),
        "receiverCustName": ("receiverCustName", "to_address.name"),
        "receiverAddress": ("receiverAddress", "to_address.street1"),
        # Phone numbers
        "cityName": ("cityName", "to_address.state"),
        "townName": ("townName", "to_address.city"),
        "custProdId": ("custProdId", "custProdId"), # deprecated
        "desi": ("desi", "parcel.volumetric_weight"),
        "kg": ("kg", "parcel.weight"),
        "cargoCount": ("cargoCount", "count"),
        "waybillNo": ("waybillNo", "waybill_id"),
        # Special fields
        "ttCollectionType": ("ttCollectionType", "options.cod_method"),
        "ttInvoiceAmount": ("ttInvoiceAmount", "options.cod_amount"),
        "ttDocumentId": ("ttDocumentId", "options.cod_invoice_id"),
        "ttDocumentSaveType": ("ttDocumentSaveType", "ttDocumentSaveType"), # not implemented here
        "orgReceiverCustId": ("orgReceiverCustId", "orgReceiverCustId"), # not implemented here
        "description": ("description", "description"),
        "taxNumber": ("taxNumber", "to_address.tr_tax_id"),
        "taxOfficeId": ("taxOfficeId", "to_address.tr_tax_office_id"),
        "taxOfficeName": ("taxOfficeName", "to_address.tr_tax_office"),
        "orgGeoCode": ("orgGeoCode", "orgGeoCode"), # deprecated
        "privilegeOrder": ("privilegeOrder", "privilegeOrder"), # deprecated
        "dcSelectedCredit": ("dcSelectedCredit", "dcSelectedCredit"), # not implemented here
        "dcCreditRule": ("dcCreditRule", "dcCreditRule"), # not implemented here
        "emailAddress": ("emailAddress", "to_address.email"),
    }

    input_object = benedict(shipment)
    output_object = benedict()

    key_format = int(req.context["formatted"])

    for param, param_name in param_keys.items():
            output_object[param] = input_object.get(param_name[key_format], xsd.SkipValue)

    # add phone numbers
    output_object.update(unpack_phone_numbers(req, shipment))
    # add special fields
    output_object["specialField1"] = generate_special_field(shipment)
    # special fields 2 and 3 are deprecated
    output_object["specialField2"] = xsd.SkipValue
    output_object["specialField3"] = xsd.SkipValue

    return dict(output_object)

def generate_zpl_label(shipment: dict, job_id: str) -> dict:
    now = datetime.now()
    time = now.strftime("%H:%M:%S")
    date = now.strftime("%d/%m/%Y")
    # really rudimentary string formatting for now
    return "^XA^CI28^PON^MUm^FO0,21.75^GB777,0.25,0.25^FS^FO0,66.75^GB777,0.25,0.25^FS^FO0,0^LRY^GB187.5,2.5,6.25^FS^FO3,1.25^A0N,5^FDYURTİÇİ KARGO                                   GÖ^FS^LRN^FO80,6.75^A0N,2.25^FD{date}-{time}^FS^FO5,8.75^A0N,3.125^FDGÖNDEREN^FS^FO7,12.75^A0N,4^FD{sender_name}^FS^FO7,16.75^A0N,4^FDTEL: {sender_telephone}^FS^FO5,24.75^A0N,3.125^FDALICI^FS^FO7,29.625^A0N,4.75^FD{recipient_name}^FS^FO7,35^A0N,4.75^FB700,3,4,^FD{recipient_address}^FS^FO7,54.75^A0N,4^FDTEL: {recipient_telephone}^FS^FO50,59.75^A0N,5^FB400,1,0,R^FD{recipient_town} ({recipient_city})^FS^FO5,69.75^A0N,3.125^FDİÇERİK^FS^FO7,73.75^A0N,4^FD{contents}^FS^FO64,82.125^A0N,3,3^FDTALEP#^FS^FO48,82.125^A0N,6.625,5^FB400,1,0,R^FD{job_id}^FS^FO3,89.125^A0N,3,3^FDREF#^FS^FO12.875,89.125^A0N,6.625,5^FD{reference}^FS^FO64,89.125^A0N,3,3^FDİRSALİYE#^FS^FO48,89.125^A0N,6.625,5^FB400,1,0,R^FD{waybill_number}^FS^FO0,122^A0N,3,3^FB800,1,0,C^FD{barcode}\&^FS^FO7,125^MUd^BY3,2^BCN,220,N,N,N,N^FWN^FD{barcode}^FS^MUd^XZ".format(
        date=date,
        time=time,
        sender_name=SENDER_NAME,
        sender_telephone=SENDER_TELEPHONE,
        recipient_name=shipment["receiverCustName"].upper(),
        recipient_address=shipment["receiverAddress"].upper(),
        recipient_telephone=prettify_phone_number(shipment["receiverPhone1"]),
        recipient_town=shipment["townName"].upper(),
        recipient_city=shipment["cityName"].upper(),
        contents=shipment["description"].upper(),
        job_id=job_id,
        reference="", # not yet implemented
        waybill_number=str(shipment["waybillNo"]).upper(),
        barcode=shipment["cargoKey"].upper(),
    )
