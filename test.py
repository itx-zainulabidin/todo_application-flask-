# test.py
# This file contains unit tests for the Flask Todo application.
import unittest
from app import app, db, User, Todo

class FlaskTodoAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def register_user(self, username, password):
        return self.app.post('/signup', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def login_user(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_user_signup_and_login(self):
        response = self.register_user('testuser', 'testpass')
        self.assertIn(b'Login', response.data)  # redirected to login page

        response = self.login_user('testuser', 'testpass')
        self.assertIn(b'Your Todos', response.data)

    def test_duplicate_signup(self):
        self.register_user('testuser', 'testpass')
        response = self.register_user('testuser', 'testpass')
        self.assertIn(b'Username already exists', response.data)

    def test_unauthenticated_todo_access(self):
        response = self.app.get('/todos', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    def test_add_todo(self):
        self.register_user('user1', 'pass')
        self.login_user('user1', 'pass')
        response = self.app.post('/todos', data={'content': 'Test todo'}, follow_redirects=True)
        self.assertIn(b'Test todo', response.data)

    def test_delete_todo(self):
        with app.app_context():
            user = User(username='deleter')
            user.set_password('hashed')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            username = user.username

            todo = Todo(content='Delete this', user_id=user_id)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        self.login_user(username, 'hashed')
        with self.app.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = username

        response = self.app.get(f'/delete/{todo_id}', follow_redirects=True)
        self.assertNotIn(b'Delete this', response.data)

    def test_update_todo(self):
        with app.app_context():
            user = User(username='updater')
            user.set_password('hashed')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            username = user.username

            todo = Todo(content='Old content', user_id=user_id)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        self.login_user(username, 'hashed')
        with self.app.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = username

        response = self.app.post(f'/update/{todo_id}', data={'content': 'New content'}, follow_redirects=True)
        self.assertIn(b'New content', response.data)


if __name__ == '__main__':
    unittest.main()
