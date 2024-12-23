#!/usr/bin/env python3

from flask import Flask, url_for, redirect, render_template, request, abort, flash
from flask_security import Security, SQLAlchemyUserDatastore, current_user, login_required
from flask_security.utils import hash_password, verify_password, login_user, logout_user
import flask_admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import helpers as admin_helpers, AdminIndexView, expose
from wtforms import PasswordField
from models import db, User, Role, RFP
from config import *
from services.role_service import RoleService
from services.user_service import UserService
from datetime import datetime, timedelta
from sqlalchemy.sql import func
import os

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('superuser')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            else:
                return redirect(url_for('security.login'))


class UserView(MyModelView):
    column_editable_list = ['email', 'first_name', 'last_name']
    column_searchable_list = column_editable_list
    column_exclude_list = ['password']
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list
    form_overrides = {'password': PasswordField}


class RFPView(MyModelView):
    column_list = ['id', 'title', 'description', 'source', 'issue_date', 'due_date', 'location', 'agency', 'rfp_url']
    column_searchable_list = ['title', 'description', 'source', 'location', 'agency']
    column_filters = ['issue_date', 'due_date', 'location', 'agency']
    column_exclude_list = ['created_at', 'updated_at']
    can_export = True
    can_view_details = True
    edit_modal = True
    create_modal = True
    column_formatters = {
        'rfp_url': lambda v, c, m, p: f'<a href="{m.rfp_url}" target="_blank">Link</a>'
    }


class CustomAdminIndexView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        total_rfps = db.session.query(func.count(RFP.id)).scalar()
        pending_rfps = db.session.query(func.count(RFP.id)).filter(RFP.due_date >= datetime.utcnow()).scalar()
        monthly_counts_query = db.session.query(
            func.date_trunc('month', RFP.issue_date).label('month'),
            func.count(RFP.id).label('total_rfps')
        ).group_by('month').order_by('month').all()
        monthly_counts = [dict(month=str(row[0]), total=row[1]) for row in monthly_counts_query]
        rfp_categories = {
            "Technology": db.session.query(func.count(RFP.id)).filter(RFP.description.ilike('%technology%')).scalar(),
            "Healthcare": db.session.query(func.count(RFP.id)).filter(RFP.description.ilike('%healthcare%')).scalar(),
            "Construction": db.session.query(func.count(RFP.id)).filter(RFP.description.ilike('%construction%')).scalar(),
            "Education": db.session.query(func.count(RFP.id)).filter(RFP.description.ilike('%education%')).scalar(),
        }
        top_sources_query = db.session.query(RFP.source, func.count(RFP.id).label('total_rfps')) \
            .group_by(RFP.source).order_by(func.count(RFP.id).desc()).limit(5).all()
        top_sources = [(src, cnt) for src, cnt in top_sources_query]
        active_users = db.session.query(func.count(User.id)).filter(User.active == True).scalar()
        return self.render(
            'admin/index.html',
            total_rfps=total_rfps,
            pending_rfps=pending_rfps,
            monthly_counts=monthly_counts,
            rfp_categories=rfp_categories,
            top_sources=top_sources,
            active_users=active_users
        )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        if not email or not password or not first_name or not last_name:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        try:
            hashed_password = hash_password(password)
            user_role = Role.query.filter_by(name='user').first()
            if not user_role:
                user_role = RoleService.create_role('user')
            user_datastore.create_user(
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                active=True,
                roles=[user_role]
            )
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error during registration: {e}', 'danger')
            db.session.rollback()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and verify_password(password, user.password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/rfps', methods=['GET'])
@login_required
def rfps():
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', '').strip()
    agency = request.args.get('agency', '').strip()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query = RFP.query
    if keyword:
        query = query.filter((RFP.title.ilike(f'%{keyword}%')) | (RFP.description.ilike(f'%{keyword}%')))
    if location:
        query = query.filter(RFP.location.ilike(f'%{location}%'))
    if agency:
        query = query.filter(RFP.agency.ilike(f'%{agency}%'))
    if start_date:
        query = query.filter(RFP.issue_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(RFP.due_date <= datetime.fromisoformat(end_date))
    rfps_data = query.all()
    return render_template('admin/rfps.html', rfps=rfps_data)


admin = flask_admin.Admin(
    app,
    'Nexus RFP',
    template_mode='bootstrap4',
    index_view=CustomAdminIndexView()
)
admin.add_view(MyModelView(Role, db.session, name="Roles"))
admin.add_view(UserView(User, db.session, name="Users"))
admin.add_view(RFPView(RFP, db.session, name="RFPs"))

@security.context_processor
def security_context_processor():
    return {
        'admin_base_template': admin.base_template,
        'admin_view': admin.index_view,
        'h': admin_helpers,
        'get_url': url_for
    }


def build_sample_db():
    with app.app_context():
        db.create_all()
        if not Role.query.first():
            user_role = RoleService.create_role('user')
            super_user_role = RoleService.create_role('superuser')
            UserService.create_user(
                first_name='Admin',
                last_name='User',
                email=os.getenv('ADMIN_EMAIL', 'admin@example.com'),
                password=os.getenv('ADMIN_PASSWORD', 'admin'),
                roles=[user_role, super_user_role]
            )


def build_sample_rfp_db():
    with app.app_context():
        db.create_all()
        if not RFP.query.first():
            sample_rfps = [
                RFP(
                    title=f"Project RFP {i+1}",
                    description=f"Description for RFP {i+1}.",
                    source=f"Agency {i+1}",
                    issue_date=datetime(2023, 1, 1) + timedelta(days=i),
                    due_date=datetime(2023, 2, 1) + timedelta(days=i),
                    location=f"City {i+1}",
                    agency=f"Agency {i+1}",
                    rfp_url=f"https://example.com/rfp/{i+1}"
                )
                for i in range(20)
            ]
            db.session.bulk_save_objects(sample_rfps)
            db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        build_sample_db()
        build_sample_rfp_db()
    app.run(debug=True)
