# Printing package initializer

from flask import Blueprint

printing_bp = Blueprint('printing', __name__, template_folder='../templates/printing', static_folder='../static/printing')

from .receipt import *  # noqa
from .purchase import *  # noqa
from .payables import *  # noqa
from .stockcheck import *  # noqa