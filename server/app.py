from flask import Flask, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy

# --------------------
# App & DB setup
# --------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'

db = SQLAlchemy(app)  # bind db to app

# --------------------
# Models
# --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_member_only = db.Column(db.Boolean, default=False)

# --------------------
# Helpers
# --------------------
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

# --------------------
# Auth routes
# --------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    session['user_id'] = user.id
    return jsonify({'id': user.id, 'username': user.username})

@app.route('/logout', methods=['DELETE'])
def logout():
    session.pop('user_id', None)
    return '', 204

@app.route('/check_session', methods=['GET'])
def check_session():
    user = get_current_user()
    if not user:
        return '', 401
    return jsonify({'id': user.id, 'username': user.username})

# --------------------
# Members-only routes
# --------------------
@app.route('/members_only_articles', methods=['GET'])
def members_only_index():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    articles = Article.query.filter_by(is_member_only=True).all()
    return jsonify([{'id': a.id, 'title': a.title, 'content': a.content} for a in articles])

@app.route('/members_only_articles/<int:article_id>', methods=['GET'])
def members_only_article(article_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    article = db.session.get(Article, article_id)
    if not article or not article.is_member_only:
        return jsonify({'error': 'Article not found or not member-only'}), 404

    return jsonify({'id': article.id, 'title': article.title, 'content': article.content})

# --------------------
# DB helpers
# --------------------
@app.cli.command("create_db")
def create_db():
    db.create_all()
    print("Database created!")

@app.cli.command("seed_db")
def seed_db():
    u1 = User(username="alice")
    u2 = User(username="bob")
    db.session.add_all([u1, u2])

    a1 = Article(title="Public Article", content="Everyone can read this.", is_member_only=False)
    a2 = Article(title="Members Article", content="Only members can read this.", is_member_only=True)
    db.session.add_all([a1, a2])

    db.session.commit()
    print("Database seeded!")

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    app.run(debug=True, port=5555)
