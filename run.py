import os
from flask import Flask
from dotenv import load_dotenv
from app.models.db import init_db
from app.services.auth_service import bootstrap_admin

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key')
    
    # Initialize DB and bootstrap admin
    init_db(app)
    bootstrap_admin()
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.workers import workers_bp
    from app.routes.attendance import attendance_bp
    from app.routes.payroll import payroll_bp
    from app.routes.payments import payments_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(workers_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
