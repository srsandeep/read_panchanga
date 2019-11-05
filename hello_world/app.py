import json
from bs4 import BeautifulSoup
import logging
import datetime

import requests
import random

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

SKILL_NAME = "Panchanga"
GET_FACT_MESSAGE = "Here's your Panchanga information for the day: "
HELP_MESSAGE = "You can say today's panchanga, what is is today's tithi, or, you can say exit... What can I help you with?"
HELP_REPROMPT = "What can I help you with?"
STOP_MESSAGE = "Goodbye!"
FALLBACK_MESSAGE = "Panchanga skill can't help you with that.  It can help you discover facts about todays stars if you say tell me today's panchanga. What can I help you with?"
FALLBACK_REPROMPT = 'What can I help you with?'
EXCEPTION_MESSAGE = "Sorry. I cannot help you with that."

data = [
  'A year on Mercury is just 88 days long.',
  'Despite being farther from the Sun, Venus experiences higher temperatures than Mercury.',
  'Venus rotates counter-clockwise, possibly because of a collision in the past with an asteroid.',
  'On Mars, the Sun appears about half the size as it does on Earth.',
  'Earth is the only planet not named after a god.',
  'Jupiter has the shortest day of all the planets.',
  'The Milky Way galaxy will collide with the Andromeda Galaxy in about 5 billion years.',
  'The Sun contains 99.86% of the mass in the Solar System.',
  'The Sun is an almost perfect sphere.',
  'A total solar eclipse can happen once every 1 to 2 years. This makes them a rare event.',
  'Saturn radiates two and a half times more energy into space than it receives from the sun.',
  'The temperature inside the Sun can reach 15 million degrees Celsius.',
  'The Moon is moving approximately 3.8 cm away from our planet every year.',
]

out_data_template = 'Today {} in London, United Kingdom the Tithi is {} and lasts until {}'

sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_panchanga_information():
    todays_date = datetime.datetime.today().date()
    year, month, day = todays_date.year, todays_date.month, todays_date.day
    logging.debug('Year: {}, Month: {}, Day: {}'.format(year, month, day))
    panchangam_url = 'http://www.mypanchang.com/phppanchang.php?yr={0}&cityhead=London,%20UK&cityname=London-UnitedKingdom&monthtype=0&mn={1}#{2}'.format(str(year), str(format(month-1, '02')), str(day))

    page = requests.get(panchangam_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    tables_sunrise_dayinfo = soup.findAll("table", class_='style1a')
    tables_date_info = soup.findAll("table", class_='style1')

    assert len(tables_date_info) == len(tables_sunrise_dayinfo)/2, 'Page format has changed'

    date_info = tables_date_info[day-1]
    sunrise_dayinfo = tables_sunrise_dayinfo[2*(day-1) : 2*day]

    ret_dict = {}

    ret_dict = {**{'date': date_info.findAll('td', class_='title')[0].get_text()}}

    element_found = False
    for each_row_elem in sunrise_dayinfo[0].findAll('tr'):
        col_name = [each_tag.get_text() for each_tag in each_row_elem.findAll('td', class_='style6')]
        col_value = [each_tag.get_text() for each_tag in each_row_elem.findAll('td', class_='style6z')]

        if 'Sunrise:' in col_name:
            element_found = True
            break
    if element_found:
        ret_dict = {**ret_dict, **dict(zip(col_name, col_value))}
        element_found = False

    for each_row_elem in sunrise_dayinfo[1].findAll('tr'):
        col_name = [each_tag.get_text() for each_tag in each_row_elem.findAll('td', class_='style6a')]
        col_value = [each_tag.get_text() for each_tag in each_row_elem.findAll('td', class_='style6ab')]

        if 'Tithi:' in col_name:
            element_found = True
            break
    if element_found:
        ret_dict = {**ret_dict, **dict(zip(col_name[:2], col_value[:2]))}
        element_found = False

    formatted_keys = [each_key.strip(':') for each_key in ret_dict.keys()]
    ret_dict = dict(zip(formatted_keys, list(ret_dict.values())))
    
    logging.debug(ret_dict)
    print(ret_dict)
    ret_string = 'Today ' + ret_dict['date'] + ' has ' + ret_dict['Tithi'] + ' until ' + ret_dict['End time']
    return ret_string

# Built-in Intent Handlers
class GetTodayPanchangaHandler(AbstractRequestHandler):
    """Handler for Skill Launch and GetNewFact Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_request_type("LaunchRequest")(handler_input) or
                is_intent_name("GetTodayPanchanga")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In GetTodayPanchangaHandler")

        random_fact = get_panchanga_information()
        print('random fact: {}'.format(random_fact))
        speech = GET_FACT_MESSAGE + random_fact

        handler_input.response_builder.speak(speech).set_card(
            SimpleCard(SKILL_NAME, random_fact))
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")

        handler_input.response_builder.speak(HELP_MESSAGE).ask(
            HELP_REPROMPT).set_card(SimpleCard(
                SKILL_NAME, HELP_MESSAGE))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In CancelOrStopIntentHandler")

        handler_input.response_builder.speak(STOP_MESSAGE)
        return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent.

    AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")

        handler_input.response_builder.speak(FALLBACK_MESSAGE).ask(
            FALLBACK_REPROMPT)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")

        logger.info("Session ended reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response

# Exception Handler
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info("In CatchAllExceptionHandler")
        logger.error(exception, exc_info=True)

        handler_input.response_builder.speak(EXCEPTION_MESSAGE).ask(
            HELP_REPROMPT)

        return handler_input.response_builder.response


# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the alexa requests."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))

class ResponseLogger(AbstractResponseInterceptor):
    """Log the alexa responses."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug("Alexa Response: {}".format(response))


# Register intent handlers
sb.add_request_handler(GetTodayPanchangaHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# TODO: Uncomment the following lines of code for request, response logs.
# sb.add_global_request_interceptor(RequestLogger())
# sb.add_global_response_interceptor(ResponseLogger())

# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()


def temp_lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e

    print('Event received: {}'.format(event))
    todays_date = datetime.datetime.today().date()
    year, month, day = todays_date.year, todays_date.month, todays_date.day
    logging.debug('Year: {}, Month: {}, Day: {}'.format(year, month, day))
    panchangam_url = 'http://www.mypanchang.com/phppanchang.php?yr={0}&cityhead=London,%20UK&cityname=London-UnitedKingdom&monthtype=0&mn={1}#{2}'.format(str(year), str(format(month-1, '02')), str(day))

    page = requests.get(panchangam_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    tables_sunrise_dayinfo = soup.findAll("table", class_='style1a')
    tables_date_info = soup.findAll("table", class_='style1')

    assert len(tables_date_info) == len(tables_sunrise_dayinfo)/2, 'Page format has changed'

    date_info = tables_date_info[day-1]
    sunrise_dayinfo = tables_sunrise_dayinfo[2*(day-1) : 2*day]

    ret_dict = {}

    ret_dict = {**{'date': date_info.findAll('td', class_='title')[0].get_text()}}

    element_found = False
    for each_row_elem in sunrise_dayinfo[0].findAll('tr'):
        col_name = [each_tag.get_text() for each_tag in each_row_elem.findAll('td', class_='style6')]
        col_value = [each_tag.get_text() for each_tag in each_row_elem.findAll('td', class_='style6z')]

        if 'Sunrise:' in col_name:
            element_found = True
            break
    if element_found:
        ret_dict = {**ret_dict, **dict(zip(col_name, col_value))}
        element_found = False

    for each_row_elem in sunrise_dayinfo[1].findAll('tr'):
        col_name = [each_tag.get_text() for each_tag in each_row_elem.findAll('td', class_='style6a')]
        col_value = [each_tag.get_text() for each_tag in each_row_elem.findAll('td', class_='style6ab')]

        if 'Tithi:' in col_name:
            element_found = True
            break
    if element_found:
        ret_dict = {**ret_dict, **dict(zip(col_name[:2], col_value[:2]))}
        element_found = False

    formatted_keys = [each_key.strip(':') for each_key in ret_dict.keys()]
    ret_dict = dict(zip(formatted_keys, list(ret_dict.values())))
    
    logging.debug(ret_dict)
    print(ret_dict)

    return {
        "statusCode": 200,
        "body": ret_dict
        # {
        #     "message": "hello world",
        #     # "location": ip.text.replace("\n", "")
        # },
    }
