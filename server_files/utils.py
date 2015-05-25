
from flask import request
from werkzeug import security
import inspect

def print_exception(exception):
    """
    Print in a pretty and uniform format an exception that occured.
    """
    where = inspect.stack()[1][3]
    print("""################# EXCEPTION #################
    {0}: {1}
#############################################""".format(where, exception))

def fieldsToValuesPOST(fields, request):
    """
    Return a dict with only the wanted fields in the request.form dict.
    """
    return { fields[i] : request.form[fields[i]] 
        for i in range(0, len(fields))
        if fields[i] in request.form  }

def fieldsToValuesGET(fields, request):
    """
    Return a dict with only the wanted fields in the request.args.get dict.
    """
    return { fields[i] : request.args.get(fields[i]) 
        for i in range(0, len(fields))
        if fields[i] in request.args  }
