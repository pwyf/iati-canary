from flask import Blueprint


blueprint = Blueprint('.', __name__,
                      static_folder='../static')


@blueprint.route('/')
def hello_world():
    return 'Hello, World!'
