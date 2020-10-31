import base64

def extract_credentials(encoded_string: str) -> tuple:
    """
    Given the base64-encoded part of the authentication header, 
    decodes and separates the username and password.
    """
    decoded = base64.b64decode(encoded_string).decode("utf-8").split(":")
    return (decoded[0], decoded[1])

def parameter_as_list(parameter) -> list:
    """
    If a query parameter is repeated, falcon returns it as a list.
    If it isn't repeated, falcon returns it as a string. This function
    simplifies this behaviour by converting everything into a list.
    """
    if type(parameter) == list:
        return parameter
    elif type(parameter) == str:
        return [parameter]

def generate_special_field(**kwargs) -> str:
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
    for field_name, field_code in fields.items():
        field += "{}${}#".format(field_code, kwargs.get(field_name, "")) if field_name in kwargs else ""

    return field