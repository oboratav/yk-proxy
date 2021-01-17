import os

import falcon

# WSDL URLs
TEST_WSDL_URL =  "http://testwebservices.yurticikargo.com:9090/KOPSWebServices/ShippingOrderDispatcherServices?wsdl"
PROD_WSDL_URL = "http://webservices.yurticikargo.com:8080/KOPSWebServices/ShippingOrderDispatcherServices?wsdl"

SENDER_NAME = os.getenv("YK_SENDER_NAME", "")
SENDER_TELEPHONE = os.getenv("YK_SENDER_TELEPHONE", "")

# Error messages for the shipment creation endpoint
ERRORS_CREATE_SHIPMENT = {
    936: (
        falcon.HTTP_IM_A_TEAPOT,
        "Unexpected error—please contact Yurtiçi Kargo", 
        "Beklenmeyen bir hata oluştu. Yurtiçi Kargo ile irtibata geçiniz",
    ),
    80859: (
        falcon.HTTP_NOT_FOUND,
        "Shipment ID not found", 
        "Kargo anahtarı bulunamadı",
    ),
    82500: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Shipment ID too long",
        "Kargo anahtarı belirtilen uzunluktan fazla",
    ),
    60020: (
        falcon.HTTP_CONFLICT,
        "A shipment with this shipment ID already exists",
        "Belirtilen kargo anahtarı sistemde mevcut",
    ),
    80057: (
        falcon.HTTP_NOT_FOUND,
        "Job ID not found",
        "Yurtiçi Kargo talep kodu bulunamadı",
    ),
    60017: (
        falcon.HTTP_NOT_FOUND,
        "Invoice ID not found",
        "Fatura anahtarı bulunamadı",
    ),
    82501: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Invoice ID too long",
        "Fatura anahtarı belirtilen uzunluktan fazla",
    ),
    60018: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Recipient name not provided",
        "Alıcı adı bulunamadı",
    ),
    82503: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Recipient name too long",
        "Alıcı adı belirtilen uzunluktan fazla",
    ),
    60019: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Recipient address not provided",
        "Alıcı adresi bulunamadı",
    ),
    82502: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Recipient address too long",
        "Alıcı adresi belirtilen uzunluktan fazla",
    ),
    82505: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD – Collection amount not provided",
        "Tahsilatlı Teslimat – Ödeme Tutarı bulunamadı",
    ),
    82506: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Collection amount too big",
        "Tahsilatlı Teslimat – Ödeme Tutarı belirtilen uzunluktan fazla",
    ),
    82507: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Invoice number not provided",
        "Tahsilatlı Teslimat – Fatura No. bulunamadı",
    ),
    82508: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Invoice number too long", 
        "Tahsilatlı Teslimat – Fatura No. belirtilen uzunluktan fazla",
    ),
    82509: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Pay over time - Installments not provided", 
        "Tahsilatlı Teslimat – Müşteri taksit seçimi bulunamadı",
    ),
    82510: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Pay over time - Too many installments", 
        "Tahsilatlı Teslimat – Müşteri taksit seçimi belirtilen uzunluktan fazla",
    ),
    82511: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Pay over time - Criteria not provided", 
        "Tahsilatlı Teslimat – Taksit Uygulama Kriteri bulunamadı",
    ),
    82512: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Your contract does not permit the payment method specified", 
        "Tahsilatlı Teslimat – Müşteri Sözleşmesinde tanımlı ödeme tipi ile gönderdiğiniz ödeme tipi uyuşmamaktadır",
    ),
    82513: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Invalid payment method", 
        "Hatalı ödeme tipi",
    ),
    82514: (
        "COD - Invalid invoice preference",
        "Hatalı fatura tipi",
    ),
    82515: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Invalid recipient e-mail address",
        "Hatalı e-mail adresi",
    ),
    82516: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Invalid recipient phone number",
        "Hatalı telefon bilgisi ",
    ),
    82517: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "Invalid formatting",
        "Hatalı format bilgisi, parametreye ait değer belirtilen formatta olmalıdır",
    ),
    82518: (
        falcon.HTTP_NOT_ACCEPTABLE,
        "COD - Pay over time - Invalid criteria",
        "Tahsilatlı Teslimat – Taksit uygulama kriteri parametresi hatalı",
    ),
}

IDENTIFIER_SHIPMENT_ID = 0
IDENTIFIER_INVOICE_ID = 1

COD_PAYMENT_METHOD_CASH = 0
COD_PAYMENT_METHOD_CREDIT_CARD = 1

class CallResult(object):
    def __init__(self, outFlag: str, successful: bool):
        self.outFlag = outFlag
        self.successful = successful
    
    def __eq__(self, other):
        if type(other) in [str, int]:
            # the outFlag parameter was passed directly
            if str(other) == self.outFlag:
                return True
        else:
            # the entire result object was passed
            if str(other.outFlag) == self.outFlag:
                return True
        return False


SUCCESSFUL = CallResult("0", successful=True)
