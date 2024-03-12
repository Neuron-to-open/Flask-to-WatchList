#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2023/6/8 23:27
# @Author  : YOURNAME
# @FileName: app.py
# @Software: PyCharm
from flask import Flask, render_template
from flask import url_for
from flask import request
from flask import redirect
from flask import flash
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import click
# 用户认证
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required, logout_user
from flask_login import current_user
# 验证密码
from werkzeug.security import generate_password_hash, check_password_hash

name = 'neuron'
movies = [
    {'title': 'My Neighbor Totoro', 'year': '1988'},
    {'title': 'Dead Poets Society', 'year': '1989'},
    {'title': 'A Perfect World', 'year': '1993'},
    {'title': 'Leon', 'year': '1994'},
    {'title': 'Mahjong', 'year': '1996'},
    {'title': 'Swallowtail Butterfly', 'year': '1996'},
    {'title': 'King of Comedy', 'year': '1999'},
    {'title': 'Devils on the Doorstep', 'year': '1999'},
    {'title': 'WALL-E', 'year': '2008'},
    {'title': 'The Pork of Music', 'year': '2012'},
]

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

"""
导入包
实例化flask对象 app
"""

app = Flask(__name__)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


@app.cli.command()
@click.option('--drop', is_flag=True, help='create after drop.')
def initdb(drop):
    """Initialize the database"""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database')


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to Login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Yhe password used to login.')
def admin(username, password):
    """create user"""
    db.create_all()

    user = User.query.first()
    # user不为空
    if user is not None:
        click.echo('Updating user......')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user......')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done')


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid Input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):

            login_user(user)
            flash('Login success')
            return redirect(url_for('login'))

        flash('Invalid username or password')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye')
    return redirect(url_for('index'))


# 注册函数，绑定一个url
@app.route('/', methods=['GET', 'POST'])
def index():
    # movies = Movie.query.all()
    # return 'Welcome to My WatchList<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'
    # return render_template('index.html', name=name, movies=movies)
    if request.method == 'POST':  # 判断是否为POST请求
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        # 获取表单数据
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or year or len(year) > 4 or len(title) > 60:
            flash('Invalid Input')
            return redirect(url_for('index'))
        # 保存表单数据
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created')
        return redirect(url_for('index'))
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)


@app.route('/home')
def hello():
    return '<h1>Hello Totoro!</h1><img src="https://helloflask.com/totoro.gif">'


@app.route('/settings', methods=['POST', 'GET'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect( url_for('settings') )

        current_user.name = name
        db.session.commit()
        flash('Settings updated')
        return redirect(url_for('index'))

    return render_template('settings.html')

@app.route('/usr/<name>')
def user_page(name):
    return f'USer:{escape(name)}'


@app.route('/test')
def test_usr_for():
    print(url_for('hello'))
    print(url_for('user_page', name='neuron'))
    print(url_for('test_usr_for'))
    print(url_for('test_usr_for', name=2))
    return 'Test page'


@app.errorhandler(404)  # 传入要处理的错误代码
def page_not_found(e):  # 接受异常对象作为参数
    user = User.query.first()
    print(user)
    return render_template('404.html', user=user), 404


@app.context_processor
def inject_user():  # 函数名字可以随意更改
    user = User.query.first()
    return dict(user=user)


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':
        title = request.form('title')
        year = request.form('year')
        if not title or year or len(year) > 4 or len(title) > 60:
            flash('Invalid Input')
            return redirect(url_for('index'))
        # 保存表单数据
        movie.title = title
        movie.year = year

        db.session.commit()
        flash('Item created')
        return redirect(url_for('index'))

    return render_template('edit.html', movie=movie)


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted')
    return redirect(url_for('index'))
