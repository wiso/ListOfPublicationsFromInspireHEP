import check_biblio


def test_replace_unicode():
    assert check_biblio.replace_unicode("hello") == "hello"
    assert check_biblio.replace_unicode("H−>yy") == "H->yy"
    assert check_biblio.replace_unicode("H−−>yy") == "H-->yy"

