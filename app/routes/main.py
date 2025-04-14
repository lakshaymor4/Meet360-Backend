from flask import Blueprint, render_template , jsonify , current_app

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({'message':'Up and Running'})

    