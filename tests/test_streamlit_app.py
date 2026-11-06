from streamlit.testing.v1 import AppTest


def test_app_renders_setup_form_without_errors():
    app = AppTest.from_file("../streamlit_app.py").run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "Review your old posts"
    assert app.file_uploader
    assert app.button[0].label == "Start review"


def test_app_explains_missing_inputs():
    app = AppTest.from_file("../streamlit_app.py").run(timeout=10)

    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert app.error
    assert "Please provide" in app.error[0].value
