from datetime import datetime

from flask import (current_app,
                   g,
                   flash,
                   make_response,
                   redirect,
                   render_template,
                   request,
                   session,
                   Response,
                   url_for)
from flask_babel import gettext
from flask_login import login_required
from sqlalchemy.orm import joinedload
from application.flicket.forms.search import SearchForm
from application.flicket.models.flicket_models import FlicketTicket, FlicketCategory, FlicketDepartment, FlicketStatus
from application.flicket.forms.flicket_forms import CreateProblemForm
from application.flicket.models.flicket_models import ProblemTicket, ProblemIncident
from application import app, db
from application.flicket.forms.flicket_forms import ReplyForm, SubscribeUser
from application.flicket.models.flicket_models_ext import FlicketTicketExt
from . import flicket_bp

def problems_view(page):

    form = SearchForm()

    status = request.args.get('status')
    department = request.args.get('department')
    category = request.args.get('category')
    content = request.args.get('content')
    user_id = request.args.get('user_id')

    if form.validate_on_submit():
        return redirect(url_for(
            'flicket_bp.problems',
            content=form.content.data,
            status=form.status.data,
            category=form.category.data,
            department=form.department.data,
            user_id=user_id
        ))

    arg_sort = request.args.get('sort')

    if arg_sort:
        args = request.args.copy()
        del args['sort']

        response = make_response(
            redirect(url_for('flicket_bp.problems', **args))
        )

        response.set_cookie(
            'problems_sort',
            arg_sort,
            max_age=2419200,
            path=url_for('flicket_bp.problems')
        )

        return response

    sort = request.cookies.get('problems_sort')

    if not sort:
        sort = 'created_desc'
        set_cookie = False
    else:
        set_cookie = True

    problem_query = ProblemTicket.query

    if content:
        problem_query = problem_query.filter(
            db.or_(
                ProblemTicket.problem_number.ilike(f'%{content}%'),
                ProblemTicket.title.ilike(f'%{content}%'),
                ProblemTicket.description.ilike(f'%{content}%'),
                ProblemTicket.root_cause.ilike(f'%{content}%'),
                ProblemTicket.resolution.ilike(f'%{content}%')
            )
        )

    if status:
        problem_query = problem_query.filter(
            ProblemTicket.status.has(FlicketStatus.status == status)
        )

    if category:
        problem_query = problem_query.filter(
            ProblemTicket.category.has(FlicketCategory.category == category)
        )

    if department:
        problem_query = problem_query.filter(
            ProblemTicket.category.has(
                FlicketCategory.department.has(
                    FlicketDepartment.department == department
                )
            )
        )

    if user_id:
        problem_query = problem_query.filter(
            ProblemTicket.created_by_id == int(user_id)
        )

    if sort == 'created_desc':
        problem_query = problem_query.order_by(
            ProblemTicket.created_at.desc()
        )

    elif sort == 'created_asc':
        problem_query = problem_query.order_by(
            ProblemTicket.created_at.asc()
        )

    elif sort == 'title_asc':
        problem_query = problem_query.order_by(
            ProblemTicket.title.asc()
        )

    elif sort == 'title_desc':
        problem_query = problem_query.order_by(
            ProblemTicket.title.desc()
        )

    elif sort == 'priority':
        problem_query = problem_query.order_by(
            ProblemTicket.priority_id.asc()
        )

    elif sort == 'priority_desc':
        problem_query = problem_query.order_by(
            ProblemTicket.priority_id.desc()
        )

    elif sort == 'status':
        problem_query = problem_query.order_by(
            ProblemTicket.status_id.asc()
        )

    elif sort == 'status_desc':
        problem_query = problem_query.order_by(
            ProblemTicket.status_id.desc()
        )

    else:
        problem_query = problem_query.order_by(
            ProblemTicket.created_at.desc()
        )

    number_results = problem_query.count()

    problem_query = problem_query.paginate(
        page=page,
        per_page=app.config['posts_per_page'],
        error_out=False
    )

    response = make_response(
        render_template(
            'flicket_problems.html',
            title=gettext('Problems'),
            form=form,
            problems=problem_query,
            page=page,
            number_results=number_results,
            content=content,
            status=status,
            department=department,
            category=category,
            user_id=user_id,
            sort=sort,
            base_url='flicket_bp.problems'
        )
    )

    if set_cookie:
        response.set_cookie(
            'problems_sort',
            sort,
            max_age=2419200,
            path=url_for('flicket_bp.problems')
        )

    return response

# problems main
@flicket_bp.route(app.config['FLICKET'] + 'problems/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'problems/<int:page>/', methods=['GET', 'POST'])
@login_required
def problems(page=1):
    return problems_view(page)


@flicket_bp.route(app.config['FLICKET'] + 'problem_create/', methods=['GET', 'POST'])
@login_required
def problem_create():

    form = CreateProblemForm()

    if form.validate_on_submit():

        new_problem = ProblemTicket(
            problem_number=f"PRB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=form.title.data,
            description=form.description.data,
            root_cause=form.root_cause.data,
            resolution=form.resolution.data,
            priority_id=form.priority_id.data,
            category_id=form.category_id.data,
            status_id=form.status_id.data,
            created_by_id=g.user.id,
            hours=form.hours.data
        )

        db.session.add(new_problem)
        db.session.flush()

        for incident_id in form.incidents.data:
            problem_incident = ProblemIncident(
                problem_id=new_problem.id,
                incident_id=incident_id
            )
            db.session.add(problem_incident)

        db.session.commit()

        flash(gettext('New Problem created.'), category='success')

        return redirect(url_for(
            'flicket_bp.problem_view',
            problem_id=new_problem.id
        ))

    title = gettext('Create Problem')

    return render_template(
        'flicket_create_problem.html',
        title=title,
        form=form
    )


@flicket_bp.route(app.config['FLICKET'] + 'problem_generate/<int:ticket_id>/', methods=['POST'])
@login_required
def generate_problem(ticket_id):

    # current incident ticket
    ticket = FlicketTicket.query.get_or_404(ticket_id)

    #TODO: Find similar tickets, cluster and use AI to generate problem data

    # AI generated data
    problem_data = {
        "problem_number": f"PRB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "title": f"Recurring Issue - {ticket.title}",
        "description": ticket.content,
        "root_cause": "AI generated root cause analysis.",
        "resolution": "AI generated resolution recommendation."
    }

    # create problem
    new_problem = ProblemTicket(
        problem_number=problem_data.get("problem_number"),
        title=problem_data.get("title"),
        description=problem_data.get("description"),
        root_cause=problem_data.get("root_cause"),
        resolution=problem_data.get("resolution"),

        priority_id=ticket.ticket_priority_id,
        category_id=ticket.category_id,
        status_id=1,
        created_by_id=g.user.id,
        hours=0
    )

    db.session.add(new_problem)
    db.session.flush()

    # link original incident
    related_incident = ProblemIncident(
        problem_id=new_problem.id,
        incident_id=ticket.id
    )

    db.session.add(related_incident)

    db.session.commit()

    flash(
        gettext('Problem ticket created successfully.'),
        category='success'
    )

    return redirect(
        url_for(
            'flicket_bp.problem_view',
            problem_id=new_problem.id
        )
    )

@flicket_bp.route(app.config['FLICKET'] + 'problem_view/<problem_id>/', methods=['GET', 'POST'])
@login_required
def problem_view(problem_id):

    # find problem
    problem = ProblemTicket.query.filter_by(id=problem_id).first()


    form = ReplyForm()
    subscribers_form = SubscribeUser()

    # if problem does not exist
    if not problem:
        flash(
            gettext('Cannot find problem: "%(value)s"', value=problem_id),
            category='warning'
        )
        return redirect(url_for('flicket_bp.problems'))

    title = f"Problem #{problem.id} {problem.title}"

    return render_template(
        'flicket_view_problem.html',
        title=title,
        problem=problem,
        form=form,
        subscribers_form=subscribers_form
    )