# ----------------------------------------------------------------------------#
# Imports.
# ----------------------------------------------------------------------------#

from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category

# ----------------------------------------------------------------------------#
# Pagination helper.
# ----------------------------------------------------------------------------#

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    #  CORS
    #  ---------------------------------------------------------------------------

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # ----------------------------------------------------------------------------#
    # Controllers.
    # ----------------------------------------------------------------------------#

    #  Categories
    #  ---------------------------------------------------------------------------
    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        formatted_categories = {category.id: category.type for category in
                                categories}

        if len(categories) == 0:
            abort(404)

        return jsonify({
          'success': True,
          'categories': formatted_categories
        })

    #  Questions
    #  ---------------------------------------------------------------------------
    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        categories = Category.query.order_by(Category.type).all()
        formatted_categories = {category.id: category.type for category in
                                categories}

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
          'success': True,
          'categories': formatted_categories,
          'current_category': None,
          'questions': current_questions,
          'total_questions': len(selection)
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).\
                                             one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
              'success': True,
              'deleted': question_id
            })

        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        if not ('question' in body and 'answer' in body and 'difficulty'
                in body and 'category' in body):
            abort(400)

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)

        try:
            question = Question(question=new_question,
                                answer=new_answer,
                                difficulty=new_difficulty,
                                category=new_category)

            question.insert()

            return jsonify({
              'success': True,
              'created': question.id
            })
        except:
            abort(422)

    #  Search
    #  ---------------------------------------------------------------------------
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()

        search_term = body.get('searchTerm', None)

        if search_term:
            search_results = Question.query.filter(Question.question.like(
                                            '%' + search_term + '%')).all()
            return jsonify({
              'success': True,
              'questions': [question.format() for question in search_results],
              'total_questions': len(search_results),
              'current_category': None
            })
        else:
            search_results = Question.query.all()
            return jsonify({
              'success': True,
              'questions': [question.format() for question in search_results],
              'total_questions': len(search_results),
              'current_category': None
            })

    #  Questions by Category
    #  ---------------------------------------------------------------------------
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_category_questions(category_id):
        questions = Question.query.filter(Question.category == category_id) \
                                  .all()

        if len(questions) == 0:
            abort(404)

        return jsonify({
          'success': True,
          'questions': [question.format() for question in questions],
          'total_questions': len(questions),
          'current_category': category_id
        })

    #  Quiz play
    #  ---------------------------------------------------------------------------

    @app.route('/quizzes', methods=['POST'])
    def quiz_play():
        body = request.get_json()

        if ('quiz_category' in body and 'previous_questions' in body):
            quiz_category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')
        else:
            abort(422)

        if quiz_category['type'] == 'click':
            questions = Question.query.filter(Question.id.notin_(
                                             (previous_questions))).all()
        else:
            questions = Question.query.filter_by(
                        category=quiz_category['id']).\
                        filter(Question.id.notin_((previous_questions))).all()

        if len(questions) > 0:
            next_question = questions[random.randrange(len(questions))].\
                                                       format()
        else:
            next_question = ''

        return jsonify({
          'success': True,
          'question': next_question
        })

    # ----------------------------------------------------------------------------#
    # Error handlers.
    # ----------------------------------------------------------------------------#

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
          "success": False,
          "error": 404,
          "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
          "success": False,
          "error": 422,
          "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
          "success": False,
          "error": 400,
          "message": "bad request"
        }), 400

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
          "success": False,
          "error": 500,
          "message": "internal server error"
        }), 500

    return app
