import pytest
from server.app import app, db, User, Article

class TestApp:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Run before every test"""
        with app.app_context():
            db.create_all()
            # Seed test data
            if not User.query.first():
                u1 = User(username="alice")
                u2 = User(username="bob")
                db.session.add_all([u1, u2])

                a1 = Article(title="Public Article", content="Everyone can read this.", is_member_only=False)
                a2 = Article(title="Members Article", content="Only members can read this.", is_member_only=True)
                db.session.add_all([a1, a2])
                db.session.commit()
        yield
        with app.app_context():
            db.drop_all()  # cleanup after test

    def login_user(self, client, username):
        return client.post('/login', json={'username': username})

    def test_can_only_access_member_only_while_logged_in(self):
        with app.test_client() as client:
            client.get('/clear')

            with app.app_context():
                user = User.query.first()

            self.login_user(client, user.username)
            response = client.get('/members_only_articles')
            data = response.get_json()

            assert response.status_code == 200
            assert all(a['title'] == "Members Article" for a in data)

    def test_member_only_articles_shows_member_only_articles(self):
        with app.test_client() as client:
            client.get('/clear')

            with app.app_context():
                user = User.query.first()

            self.login_user(client, user.username)
            response = client.get('/members_only_articles')
            data = response.get_json()

            # Only member-only articles are returned
            assert response.status_code == 200
            assert len(data) == 1
            assert data[0]['title'] == "Members Article"

    def test_can_only_access_member_only_article_while_logged_in(self):
        with app.test_client() as client:
            client.get('/clear')

            with app.app_context():
                user = User.query.first()
                article = Article.query.filter_by(is_member_only=True).first()

            self.login_user(client, user.username)
            response = client.get(f'/members_only_articles/{article.id}')
            data = response.get_json()

            assert response.status_code == 200
            assert data['title'] == article.title
