# -*- coding: utf-8 -*-
import logging
from crawler_worker import *
from indeed.spiders.indeed import *
from flask_bootstrap import Bootstrap
from flask import Flask, request, render_template, send_from_directory
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField


app = Flask(__name__)
Bootstrap(app)


class CrawlForm(Form):
    query = TextField(
        "Query:", 
        validators=[validators.DataRequired()],
        description="Scientist"
    )
    location = TextField(
        "Location:", 
        validators=[validators.DataRequired()],
        description="Seattle"
    )
    domain = TextField(
        "Domain:", 
        validators=[validators.DataRequired()],
        description=".com"
    )
    index = TextField(
        "Elasticsearch Index:", 
        validators=[validators.DataRequired()],
        description="indeed"
    )


@app.route("/", methods=["GET", "POST"])
def home():
    """"""
    running_spider = None
    form = CrawlForm(request.form)
    
    if request.method == "POST":
        try:
            # -- Init spider with form data.
            crawler = CrawlerWorker(IndeedSpider, request.form.to_dict())
            crawler.start()
        # -- Update running_spider var based on try success.
        except Exception as ee:
            raise ee
            running_spider = False
        else:
            running_spider = True

    return render_template("home.html", form=form, running_spider=running_spider)


if __name__ == "__main__":
    app.run(host="0.0.0.0")

