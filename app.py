import os
import secrets

from flask import Flask, redirect, render_template, request, session, url_for

from links import LinkError, LinkStore


ERRORS = {
    "invalid_url": (422, "Исходный адрес указан неправильно. Введите полный URL с протоколом http:// или https://."),
    "invalid_alias": (422, "Короткое имя должно содержать от 3 до 32 латинских букв, цифр, дефисов или знаков подчёркивания."),
    "alias_taken": (409, "Указанное короткое имя уже используется. Выберите другое имя или оставьте поле пустым."),
    "invalid_title": (422, "Название ссылки не должно превышать 100 символов."),
    "csrf": (403, "Не удалось подтвердить отправку формы. Откройте форму заново и повторите действие."),
    "not_found": (404, "Ссылка с таким идентификатором или коротким именем не найдена."),
}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE_URL=os.environ.get("DATABASE_URL"),
        MAX_CONTENT_LENGTH=16 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["DATABASE_URL"]:
        raise RuntimeError("Не задана переменная окружения DATABASE_URL")
    store = LinkStore(app.config["DATABASE_URL"])
    app.extensions["link_store"] = store

    @app.context_processor
    def common_context():
        return {"version": "0.0.3"}

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/links")
    def link_list():
        return render_template("links.html", links=store.all())

    @app.route("/links/new", methods=["GET", "POST"])
    def link_form():
        if request.method == "POST":
            form = {name: request.form.get(name, "") for name in ("original_url", "title", "alias")}
            token = request.form.get("csrf_token", "")
            if not token or not secrets.compare_digest(token.encode(), session.get("csrf_token", "").encode()):
                return redirect(url_for("access_denied", reason="csrf"), code=303)
            try:
                link = store.create(**form)
            except LinkError as error:
                session["form_data"] = {
                    "original_url": form["original_url"][:2048],
                    "title": form["title"][:100],
                    "alias": form["alias"][:32],
                }
                return redirect(url_for("access_denied", reason=error.reason), code=303)
            session.pop("form_data", None)
            return redirect(url_for("link_detail", record_id=link["id"], created=1), code=303)
        session.setdefault("csrf_token", secrets.token_hex(24))
        return render_template("link_form.html", form=session.pop("form_data", {}))

    @app.get("/links/<int:record_id>")
    def link_detail(record_id):
        link = store.find(record_id)
        if link is None:
            return render_template("access_denied.html", reason=ERRORS["not_found"][1], action="открыть карточку ссылки"), 404
        return render_template("link_detail.html", link=link, created=request.args.get("created") == "1")

    @app.get("/s/<code>")
    def follow_link(code):
        link = store.by_code(code)
        if link is None:
            return render_template("access_denied.html", reason=ERRORS["not_found"][1], action="перейти по короткой ссылке"), 404
        return redirect(link["original_url"], code=302)

    @app.get("/access-denied")
    def access_denied():
        status, message = ERRORS.get(request.args.get("reason", "invalid_url"), ERRORS["invalid_url"])
        return render_template("access_denied.html", reason=message, action="создать короткую ссылку"), status

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("access_denied.html", reason="Страница с таким адресом не найдена.", action="открыть страницу"), 404

    return app


app = create_app()
