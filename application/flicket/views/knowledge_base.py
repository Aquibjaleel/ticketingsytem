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
from flask_login import login_required
from application.flicket.models.flicket_models import KBArticle
from application.flicket.forms.flicket_forms import CreateKBArticleForm
from application.flicket.forms.search import SearchForm
from flask_babel import gettext
from . import flicket_bp
from application import app, db


@flicket_bp.route(app.config['FLICKET'] + 'kb_view/<int:kb_id>/', methods=['GET'])
@login_required
def kb_view(kb_id):

    # article = KBArticle.query.get_or_404(kb_id)

    article = KBArticle(
        title='Unable to Connect to Wi-Fi Network',
        category='Network',
        issue_type='Wi-Fi',
        symptoms='No internet access',
        resolution='Restart adapter',
        keywords='wifi'
    )

    return render_template(
        'kb_article_sample.html',
        article=article
    )

@flicket_bp.route(app.config['FLICKET'] + 'kb/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'kb/page/<int:page>/', methods=['GET', 'POST'])
@login_required
def knowledge_base(page=1, is_my_view=False, subscribed=False):


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
        redirect_url = KBArticle.form_redirect(form, url='flicket_bp.knowledge_base')
        return redirect(redirect_url)

    arg_sort = request.args.get('sort')
    if arg_sort:
        args = request.args.copy()
        del args['sort']
        response = make_response(redirect(url_for('flicket_bp.knowledge_base', **args)))
        response.set_cookie('knowledge_base_sort', arg_sort, max_age=2419200, path=url_for('flicket_bp.knowledge_base', **args))
        return response

    sort = request.cookies.get('knowledge_base_sort')
    if not sort:
        sort = 'created_desc'
        set_cookie = False
    else:
        set_cookie = True

    kb_query = KBArticle.query

    if content:

        kb_query = kb_query.filter(
            db.or_(
                KBArticle.title.ilike(f'%{content}%'),
                KBArticle.category.ilike(f'%{content}%'),
                KBArticle.keywords.ilike(f'%{content}%'),
                KBArticle.issue_type.ilike(f'%{content}%'),
                KBArticle.resolution.ilike(f'%{content}%')
            )
        )
  
    # sorting
    if sort == 'created_desc':

        kb_query = kb_query.order_by(
            KBArticle.created_at.desc()
        )

    elif sort == 'created_asc':

        kb_query = kb_query.order_by(
            KBArticle.created_at.asc()
        )

  
    number_results = kb_query.count()
    kb_query = kb_query.paginate(page=page, per_page=app.config['posts_per_page'])

    title = gettext('Knowledge Base')


    response = make_response(render_template('flicket_knowledge_base.html',
                                             title=title,
                                             form=form,
                                             articles=kb_query,
                                             page=page,
                                             number_results=number_results,
                                             status=status,
                                             department=department,
                                             category=category,
                                             user_id=user_id,
                                             created_id=created_id,
                                             assigned_id=assigned_id,
                                             sort=sort,
                                             base_url='flicket_bp.knowledge_base'))

    if set_cookie:
        response.set_cookie('knowledge_base_sort', sort, max_age=2419200, path=url_for('flicket_bp.knowledge_base'))

    return response


@flicket_bp.route(app.config['FLICKET'] + 'kb_create/', methods=['GET', 'POST'])
@login_required
def kb_create():

    form = CreateKBArticleForm()

    if form.validate_on_submit():

        new_article = KBArticle(
            title=form.title.data,
            category=form.category.data,
            issue_type=form.issue_type.data,
            symptoms=form.symptoms.data,
            resolution=form.resolution.data,
            keywords=form.keywords.data
        )

        db.session.add(new_article)
        db.session.commit()

        flash(gettext('New Knowledge Base article created.'), category='success')

        return redirect(url_for('flicket_bp.knowledge_base'))

    title = gettext('Create Knowledge Base Article')

    return render_template(
        'flicket_create_kb.html',
        title=title,
        form=form
    )