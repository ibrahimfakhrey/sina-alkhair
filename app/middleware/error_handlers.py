from flask import jsonify


def register_error_handlers(app):
    """Register error handlers for the application"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large', 'message': 'Maximum file size is 1MB'}), 413

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log the error here if needed
        return jsonify({'error': 'Error', 'message': str(error)}), 500
