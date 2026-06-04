#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from datetime import datetime

from flask import (current_app,
                   g,
                   make_response,
                   redirect,
                   render_template,
                   request,
                   Response,
                   url_for)
from flask_babel import gettext
from flask_login import login_required
from sqlalchemy.orm import joinedload

from application import app, db
from application.flicket.forms.flicket_forms import ReplyForm, SubscribeUser
from application.flicket.forms.search import SearchForm
from application.flicket.models.flicket_models import FlicketPost
from application.flicket.models.flicket_models import FlicketTicket
from application.flicket.models.flicket_models import FlicketCategory
from application.services.ai_client import AIService
from . import flicket_bp


def clean_csv_data(input_text):
    output_text = input_text.replace('"', "'")
    return output_text


def tickets_view(page, is_my_view=False, subscribed=False):
    """
        Function common to 'tickets' and 'my_tickets' except where query is filtered for users own tickets.
    """
    form = SearchForm()

    # get request arguments from the url
    status = request.args.get('status')
    department = request.args.get('department')
    category = request.args.get('category')
    content = request.args.get('content')
    user_id = request.args.get('user_id')
    assigned_id = request.args.get('assigned_id')
    created_id = request.args.get('created_id')

    if form.validate_on_submit():
        redirect_url = FlicketTicket.form_redirect(form, url='flicket_bp.tickets')
        return redirect(redirect_url)

    arg_sort = request.args.get('sort')
    if arg_sort:
        args = request.args.copy()
        del args['sort']
        response = make_response(redirect(url_for('flicket_bp.tickets', **args)))
        response.set_cookie('tickets_sort', arg_sort, max_age=2419200, path=url_for('flicket_bp.tickets', **args))
        return response

    sort = request.cookies.get('tickets_sort')
    if not sort:
        sort = 'priority_desc'
        set_cookie = False
    else:
        set_cookie = True

    ticket_query, form = FlicketTicket.query_tickets(form, department=department, category=category, status=status,
                                                     user_id=user_id, content=content, assigned_id=assigned_id,
                                                     created_id=created_id)
    if is_my_view:
        ticket_query = FlicketTicket.my_tickets(ticket_query)
    ticket_query = FlicketTicket.sorted_tickets(ticket_query, sort)

    if subscribed:
        ticket_query = FlicketTicket.my_subscribed_tickets(ticket_query)

    number_results = ticket_query.count()
    ticket_query = ticket_query.paginate(page=page, per_page=app.config['posts_per_page'])

    title = gettext('Tickets')
    if is_my_view:
        title = gettext('My Tickets')

    if content:
        form.content.data = content

    response = make_response(render_template('flicket_tickets.html',
                                             title=title,
                                             form=form,
                                             tickets=ticket_query,
                                             page=page,
                                             number_results=number_results,
                                             status=status,
                                             department=department,
                                             category=category,
                                             user_id=user_id,
                                             created_id=created_id,
                                             assigned_id=assigned_id,
                                             sort=sort,
                                             base_url='flicket_bp.tickets'))

    if set_cookie:
        response.set_cookie('tickets_sort', sort, max_age=2419200, path=url_for('flicket_bp.tickets'))

    return response


# tickets main
@flicket_bp.route(app.config['FLICKET'] + 'tickets/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'tickets/<int:page>/', methods=['GET', 'POST'])
@login_required
def tickets(page=1):
    return tickets_view(page)


@flicket_bp.route(app.config['FLICKET'] + 'tickets_csv/', methods=['GET', 'POST'])
@login_required
def tickets_csv():
    status = request.args.get('status')
    department = request.args.get('department')
    category = request.args.get('category')
    content = request.args.get('content')
    user_id = request.args.get('user_id')

    ticket_query, form = FlicketTicket.query_tickets(department=department, category=category, status=status,
                                                     user_id=user_id, content=content)
    ticket_query = ticket_query.limit(app.config['csv_dump_limit'])

    date_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_name = date_stamp + 'ticketdump.csv'

    csv_contents = 'Ticket_ID,Priority,Title,Submitted By,Date,Replies,Category,Status,Assigned,URL\n'
    for t in ticket_query:
        _name = t.assigned.name if hasattr(t.assigned, 'name') else 'Not assigned'
        csv_contents += '{},{},"{}",{},{},{},{} - {},{},{},{}{}\n'.format(t.id_zfill,
                                                                          t.ticket_priority.priority,
                                                                          clean_csv_data(t.title),
                                                                          t.user.name,
                                                                          t.date_added.strftime("%Y-%m-%d"),
                                                                          t.num_replies,
                                                                          clean_csv_data(t.category.department.department),
                                                                          clean_csv_data(t.category.category),
                                                                          t.current_status.status,
                                                                          _name,
                                                                          app.config["base_url"],
                                                                          url_for("flicket_bp.ticket_view_detail",
                                                                                  ticket_id=t.id))

    return Response(csv_contents, mimetype='text/csv', headers={"Content-disposition": f"attachment; filename={file_name}"})


@flicket_bp.route(app.config['FLICKET'] + 'my_tickets/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'my_tickets/<int:page>/', methods=['GET', 'POST'])
@login_required
def my_tickets(page=1):
    return tickets_view(page, is_my_view=True)


@flicket_bp.route(app.config['FLICKET'] + 'subscribed/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'subscribed/<int:page>/', methods=['GET', 'POST'])
@login_required
def subscribed(page=1):
    return tickets_view(page, subscribed=True)


# AI summarization when loading a ticket
@flicket_bp.route('/ticket_view_detail/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_view_detail(ticket_id):
    # 1. Fetch ticket with Eager Loading to avoid the template 'getitem' error
    # String notation 'category.department' is safer for complex relationships
    ticket_data = (
        FlicketTicket.query
        .options(joinedload(FlicketTicket.category).joinedload(FlicketCategory.department))
        .get_or_404(ticket_id)
    )

    # 2. Instantiate forms
    form = ReplyForm()
    subscribers_form = SubscribeUser()

    # 3. Setup pagination for replies
    page = request.args.get('page', 1, type=int)
    ppp = current_app.config.get('posts_per_page', 20)

    # Filter by the foreign key (ensure 'ticket_id' matches your DB column name)
    replies = (
        FlicketPost.query
        .filter_by(ticket_id=ticket_data.id)
        .order_by(FlicketPost.date_added)
        .paginate(page=page, per_page=ppp)
    )

    # 4. AI Generation | Fetch from DB or Create
    ai_summary = ticket_data.ai_summary
    if not ai_summary and current_app.config.get('AI_PROVIDER'):
        ai_summary = AIService.get_summary(ticket_data.content)
        ticket_data.ai_summary = ai_summary
        db.session.commit()

    return render_template('flicket_view.html',
                           ticket=ticket_data,
                           ai_summary=ai_summary,
                           form=form,
                           subscribers_form=subscribers_form,
                           replies=replies)